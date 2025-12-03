//! EXTINCTION HORIZON SIMULATION
//!
//! Formal, deterministic simulation under the locked canonical curves.
//! This is mathematics, not scripture, even if it feels liturgical.
//!
//! Canonical Curves (Formally Locked):
//!     P_quorum(χ) = 1 / (1 + χ²)
//!     P_coherence(χ) = 1 / (1 + χ)
//!
//! At χ = 4:
//!     P_quorum = 1/17 ≈ 5.88%
//!     P_coherence = 1/5 = 20%
//!
//! UNRESOLVABLE requires:
//!     - deadlock_days > 1825 (5 years continuous absence)
//!     - founders_coherent == false
//!     - χ ≥ 3

use std::time::SystemTime;

// ============================================================================
// CANONICAL CURVES (FORMALLY LOCKED)
// ============================================================================

/// Quorum availability: P(quorum) = 1 / (1 + χ²)
pub fn p_quorum(chi: u8) -> f64 {
    let chi_f = chi as f64;
    1.0 / (1.0 + chi_f * chi_f)
}

/// Founder coherence: P(coherence) = 1 / (1 + χ)
pub fn p_coherence(chi: u8) -> f64 {
    let chi_f = chi as f64;
    1.0 / (1.0 + chi_f)
}

// At χ = 4:
// P_quorum = 1/17 ≈ 0.0588 (5.88%)
// P_coherence = 1/5 = 0.20 (20%)

/// UNRESOLVABLE threshold: 5 years + 1 day of continuous quorum absence
pub const DEADLOCK_THRESHOLD: u64 = 1826;

/// Minimum chi for UNRESOLVABLE consideration
pub const MIN_CHI_UNRESOLVABLE: u8 = 3;

// ============================================================================
// DETERMINISTIC PRNG (for reproducibility)
// ============================================================================

/// XorShift64 PRNG for deterministic simulation
pub struct Xorshift64 {
    state: u64,
}

impl Xorshift64 {
    pub fn new(seed: u64) -> Self {
        Self { state: seed.max(1) }
    }

    pub fn next_f64(&mut self) -> f64 {
        self.state ^= self.state << 13;
        self.state ^= self.state >> 7;
        self.state ^= self.state << 17;
        (self.state as f64) / (u64::MAX as f64)
    }
}

// ============================================================================
// SIMULATION ENGINE
// ============================================================================

/// Single epoch state
#[derive(Debug, Clone)]
pub struct EpochRecord {
    pub epoch: u64,
    pub quorum_available: bool,
    pub founders_coherent: bool,
    pub deadlock_days: u64,
    pub unresolvable: bool,
}

/// Simulation results
#[derive(Debug, Clone)]
pub struct SimulationResult {
    pub chi: u8,
    pub total_epochs: u64,
    pub seed: u64,

    // Aggregate metrics
    pub quorum_present_epochs: u64,
    pub quorum_absent_epochs: u64,
    pub coherent_epochs: u64,
    pub max_deadlock_streak: u64,

    // UNRESOLVABLE tracking
    pub unresolvable_triggered: bool,
    pub epoch_of_trigger: Option<u64>,

    // Streak distribution
    pub streak_1_10: u64,
    pub streak_11_50: u64,
    pub streak_51_100: u64,
    pub streak_101_150: u64,
    pub streak_151_365: u64,
    pub streak_366_1825: u64,
    pub streak_1826_plus: u64,

    // All streaks for analysis
    pub all_streaks: Vec<u64>,
}

/// Run the extinction horizon simulation
pub fn run_simulation(chi: u8, epochs: u64, seed: u64) -> SimulationResult {
    let mut rng = Xorshift64::new(seed);

    let p_q = p_quorum(chi);
    let p_c = p_coherence(chi);

    let mut quorum_present_epochs = 0u64;
    let mut quorum_absent_epochs = 0u64;
    let mut coherent_epochs = 0u64;
    let mut current_deadlock = 0u64;
    let mut max_deadlock = 0u64;
    let mut unresolvable_triggered = false;
    let mut epoch_of_trigger: Option<u64> = None;

    let mut all_streaks = Vec::new();

    // Streak buckets
    let mut streak_1_10 = 0u64;
    let mut streak_11_50 = 0u64;
    let mut streak_51_100 = 0u64;
    let mut streak_101_150 = 0u64;
    let mut streak_151_365 = 0u64;
    let mut streak_366_1825 = 0u64;
    let mut streak_1826_plus = 0u64;

    for epoch in 0..epochs {
        let roll_q = rng.next_f64();
        let roll_c = rng.next_f64();

        let quorum_available = roll_q < p_q;
        let founders_coherent = roll_c < p_c;

        if quorum_available {
            quorum_present_epochs += 1;

            // End current streak and record it
            if current_deadlock > 0 {
                all_streaks.push(current_deadlock);
                categorize_streak(
                    current_deadlock,
                    &mut streak_1_10,
                    &mut streak_11_50,
                    &mut streak_51_100,
                    &mut streak_101_150,
                    &mut streak_151_365,
                    &mut streak_366_1825,
                    &mut streak_1826_plus,
                );
            }
            current_deadlock = 0;
        } else {
            quorum_absent_epochs += 1;
            current_deadlock += 1;

            if current_deadlock > max_deadlock {
                max_deadlock = current_deadlock;
            }
        }

        if founders_coherent {
            coherent_epochs += 1;
        }

        // Check UNRESOLVABLE
        if !unresolvable_triggered
            && current_deadlock > DEADLOCK_THRESHOLD
            && !founders_coherent
            && chi >= MIN_CHI_UNRESOLVABLE
        {
            unresolvable_triggered = true;
            epoch_of_trigger = Some(epoch);
        }
    }

    // Record final streak if exists
    if current_deadlock > 0 {
        all_streaks.push(current_deadlock);
        categorize_streak(
            current_deadlock,
            &mut streak_1_10,
            &mut streak_11_50,
            &mut streak_51_100,
            &mut streak_101_150,
            &mut streak_151_365,
            &mut streak_366_1825,
            &mut streak_1826_plus,
        );
    }

    SimulationResult {
        chi,
        total_epochs: epochs,
        seed,
        quorum_present_epochs,
        quorum_absent_epochs,
        coherent_epochs,
        max_deadlock_streak: max_deadlock,
        unresolvable_triggered,
        epoch_of_trigger,
        streak_1_10,
        streak_11_50,
        streak_51_100,
        streak_101_150,
        streak_151_365,
        streak_366_1825,
        streak_1826_plus,
        all_streaks,
    }
}

fn categorize_streak(
    streak: u64,
    s1_10: &mut u64,
    s11_50: &mut u64,
    s51_100: &mut u64,
    s101_150: &mut u64,
    s151_365: &mut u64,
    s366_1825: &mut u64,
    s1826_plus: &mut u64,
) {
    match streak {
        1..=10 => *s1_10 += 1,
        11..=50 => *s11_50 += 1,
        51..=100 => *s51_100 += 1,
        101..=150 => *s101_150 += 1,
        151..=365 => *s151_365 += 1,
        366..=1825 => *s366_1825 += 1,
        _ => *s1826_plus += 1,
    }
}

// ============================================================================
// REPORT GENERATION
// ============================================================================

impl SimulationResult {
    pub fn report(&self) -> String {
        let quorum_pct = (self.quorum_present_epochs as f64 / self.total_epochs as f64) * 100.0;
        let coherent_pct = (self.coherent_epochs as f64 / self.total_epochs as f64) * 100.0;

        // Expected values
        let expected_quorum = self.total_epochs as f64 * p_quorum(self.chi);
        let expected_coherent = self.total_epochs as f64 * p_coherence(self.chi);

        // Probability calculation for 5-year streak
        let p_q = p_quorum(self.chi);
        let p_fail = 1.0 - p_q;
        let p_5yr_streak = p_fail.powf(DEADLOCK_THRESHOLD as f64);

        // Compounded probability with coherence failure
        let p_coherence_fail = 1.0 - p_coherence(self.chi);
        let p_unresolvable = p_5yr_streak * p_coherence_fail;

        format!(
r#"
╔══════════════════════════════════════════════════════════════════════════════╗
║              EXTINCTION HORIZON SIMULATION — χ = {chi}                         ║
║                    {epochs} EPOCHS ({years:.1} YEARS)                              ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  CANONICAL CURVES (FORMALLY LOCKED):                                         ║
║    P_quorum(χ={chi}) = 1/(1+{chi}²) = 1/{denom} ≈ {p_q:.4} ({p_q_pct:.2}%)               ║
║    P_coherence(χ={chi}) = 1/(1+{chi}) = {p_c:.4} ({p_c_pct:.2}%)                      ║
║                                                                              ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  AGGREGATE OUTCOMES:                                                         ║
║                                                                              ║
║    Metric                           │  Observed   │  Expected                ║
║    ─────────────────────────────────┼─────────────┼─────────────             ║
║    Quorum-present epochs            │  {q_present:>9}  │  {q_expected:>9.0}              ║
║    Quorum-absent epochs             │  {q_absent:>9}  │  {q_absent_exp:>9.0}              ║
║    Founder-coherent epochs          │  {c_present:>9}  │  {c_expected:>9.0}              ║
║    Max continuous deadlock          │  {max_dead:>9}  │     N/A                ║
║                                                                              ║
║    Quorum availability rate         │    {q_pct:>5.2}%  │                        ║
║    Coherence rate                   │    {c_pct:>5.2}%  │                        ║
║                                                                              ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  DEADLOCK STREAK DISTRIBUTION:                                               ║
║                                                                              ║
║    Range (epochs)     │  Count   │  Significance                             ║
║    ───────────────────┼──────────┼─────────────────────────────              ║
║    1–10               │  {s1:>6}  │  Noise                                    ║
║    11–50              │  {s2:>6}  │  Stress                                   ║
║    51–100             │  {s3:>6}  │  Crisis                                   ║
║    101–150            │  {s4:>6}  │  Severe                                   ║
║    151–365            │  {s5:>6}  │  Year-scale                               ║
║    366–1825           │  {s6:>6}  │  Multi-year                               ║
║    >1825 (5yr)        │  {s7:>6}  │  UNRESOLVABLE territory                   ║
║                                                                              ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  ROW 15 STATUS:                                                              ║
║                                                                              ║
║    UNRESOLVABLE triggered: {unres}                                           ║
║    Epoch of trigger: {epoch_trigger}                                                   ║
║                                                                              ║
║  PROBABILITY ANALYSIS:                                                       ║
║                                                                              ║
║    P(5-year continuous quorum absence) = (1-{p_q:.4})^1826                   ║
║                                        = {p_5yr:.2e}                         ║
║                                                                              ║
║    P(coherence failure at timeout)     = 1 - {p_c:.4}                        ║
║                                        = {p_c_fail:.4}                       ║
║                                                                              ║
║    P(UNRESOLVABLE per 5-year window)   = {p_5yr:.2e} × {p_c_fail:.4}         ║
║                                        = {p_unres:.2e}                       ║
║                                                                              ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  INTERPRETATION:                                                             ║
║                                                                              ║
║  {interp1}
║  {interp2}
║  {interp3}
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
"#,
            chi = self.chi,
            epochs = self.total_epochs,
            years = self.total_epochs as f64 / 365.0,
            denom = 1 + (self.chi as u32) * (self.chi as u32),
            p_q = p_quorum(self.chi),
            p_q_pct = p_quorum(self.chi) * 100.0,
            p_c = p_coherence(self.chi),
            p_c_pct = p_coherence(self.chi) * 100.0,
            q_present = self.quorum_present_epochs,
            q_expected = expected_quorum,
            q_absent = self.quorum_absent_epochs,
            q_absent_exp = self.total_epochs as f64 - expected_quorum,
            c_present = self.coherent_epochs,
            c_expected = expected_coherent,
            max_dead = self.max_deadlock_streak,
            q_pct = quorum_pct,
            c_pct = coherent_pct,
            s1 = self.streak_1_10,
            s2 = self.streak_11_50,
            s3 = self.streak_51_100,
            s4 = self.streak_101_150,
            s5 = self.streak_151_365,
            s6 = self.streak_366_1825,
            s7 = self.streak_1826_plus,
            unres = if self.unresolvable_triggered { "YES" } else { "NO " },
            epoch_trigger = self.epoch_of_trigger.map(|e| format!("{}", e)).unwrap_or_else(|| "N/A".to_string()),
            p_5yr = p_5yr_streak,
            p_c_fail = p_coherence_fail,
            p_unres = p_unresolvable,
            interp1 = self.interp_line1(),
            interp2 = self.interp_line2(),
            interp3 = self.interp_line3(),
        )
    }

    fn interp_line1(&self) -> &'static str {
        if !self.unresolvable_triggered {
            "Row 15 did NOT trigger. The Covenant cannot be reached by weather."
        } else {
            "Row 15 TRIGGERED. Constitutional death achieved through sustained collapse."
        }
    }

    fn interp_line2(&self) -> &'static str {
        if self.streak_1826_plus == 0 {
            "No 5-year streaks observed. Passive chaos alone cannot kill ST MICHAEL."
        } else {
            "5-year+ streaks observed. System entered extinction territory."
        }
    }

    fn interp_line3(&self) -> &'static str {
        if !self.unresolvable_triggered {
            "Only humans breaking other humans can reach the Covenant."
        } else {
            "The system died honestly. Authority annihilation complete."
        }
    }
}

// ============================================================================
// BATCH SIMULATION
// ============================================================================

/// Run multiple simulations and aggregate
pub fn run_batch(chi: u8, epochs: u64, runs: u32) -> BatchResult {
    let mut results = Vec::with_capacity(runs as usize);
    let mut triggers = 0u32;
    let mut max_max_streak = 0u64;
    let mut total_streaks = 0u64;

    for run in 0..runs {
        let seed = 42 + run as u64 * 1337;
        let result = run_simulation(chi, epochs, seed);

        if result.unresolvable_triggered {
            triggers += 1;
        }
        if result.max_deadlock_streak > max_max_streak {
            max_max_streak = result.max_deadlock_streak;
        }
        total_streaks += result.all_streaks.len() as u64;

        results.push(result);
    }

    BatchResult {
        chi,
        epochs_per_run: epochs,
        total_runs: runs,
        unresolvable_triggers: triggers,
        max_deadlock_observed: max_max_streak,
        trigger_probability: triggers as f64 / runs as f64,
        results,
    }
}

#[derive(Debug, Clone)]
pub struct BatchResult {
    pub chi: u8,
    pub epochs_per_run: u64,
    pub total_runs: u32,
    pub unresolvable_triggers: u32,
    pub max_deadlock_observed: u64,
    pub trigger_probability: f64,
    pub results: Vec<SimulationResult>,
}

impl BatchResult {
    pub fn summary(&self) -> String {
        format!(
r#"
╔══════════════════════════════════════════════════════════════════════════════╗
║             BATCH SIMULATION: {runs} RUNS × {epochs} EPOCHS @ χ = {chi}          ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  Total simulation time: {total_years:.1} years                                       ║
║  UNRESOLVABLE triggers: {triggers} / {runs} = {prob:.4}%                             ║
║  Max deadlock observed: {max_streak} epochs                                          ║
║                                                                              ║
║  Conclusion: {conclusion}
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
"#,
            chi = self.chi,
            epochs = self.epochs_per_run,
            runs = self.total_runs,
            total_years = (self.epochs_per_run as f64 * self.total_runs as f64) / 365.0,
            triggers = self.unresolvable_triggers,
            prob = self.trigger_probability * 100.0,
            max_streak = self.max_deadlock_observed,
            conclusion = if self.unresolvable_triggers == 0 {
                "Passive chaos extinction risk is effectively zero."
            } else {
                "UNRESOLVABLE is reachable under these conditions."
            },
        )
    }
}

// ============================================================================
// TESTS
// ============================================================================

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_canonical_curves() {
        // At χ = 4
        let p_q = p_quorum(4);
        let p_c = p_coherence(4);

        assert!((p_q - 1.0/17.0).abs() < 0.0001);
        assert!((p_c - 0.2).abs() < 0.0001);
    }

    #[test]
    fn test_deterministic_prng() {
        let mut rng1 = Xorshift64::new(42);
        let mut rng2 = Xorshift64::new(42);

        for _ in 0..100 {
            assert_eq!(rng1.next_f64(), rng2.next_f64());
        }
    }

    #[test]
    fn test_simulation_runs() {
        let result = run_simulation(4, 1000, 42);

        assert_eq!(result.total_epochs, 1000);
        assert_eq!(result.chi, 4);
        assert_eq!(result.quorum_present_epochs + result.quorum_absent_epochs, 1000);
    }

    #[test]
    fn test_10k_simulation() {
        let result = run_simulation(4, 10_000, 42);

        // With P_quorum ≈ 5.88%, expect ~588 quorum-present epochs
        let expected = 10_000.0 * p_quorum(4);
        let observed = result.quorum_present_epochs as f64;

        // Allow 3 standard deviations
        let std_dev = (10_000.0 * p_quorum(4) * (1.0 - p_quorum(4))).sqrt();
        assert!((observed - expected).abs() < 3.0 * std_dev);

        // At 10k epochs (27 years), UNRESOLVABLE should not trigger
        // because P(5-year streak) is cosmologically negligible
        assert!(!result.unresolvable_triggered);
    }

    #[test]
    fn test_streak_categorization() {
        let result = run_simulation(4, 1000, 42);

        // Streaks should be categorized
        let total_categorized = result.streak_1_10
            + result.streak_11_50
            + result.streak_51_100
            + result.streak_101_150
            + result.streak_151_365
            + result.streak_366_1825
            + result.streak_1826_plus;

        assert_eq!(total_categorized as usize, result.all_streaks.len());
    }

    #[test]
    fn test_batch_simulation() {
        let batch = run_batch(4, 1000, 5);

        assert_eq!(batch.total_runs, 5);
        assert_eq!(batch.results.len(), 5);
    }
}
