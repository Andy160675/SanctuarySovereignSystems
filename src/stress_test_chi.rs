//! STRESS TEST: Χ = 3 vs Χ = 4
//!
//! Deterministic comparison of UNRESOLVABLE trigger conditions
//! under sustained Destabilized vs Chaotic stress.
//!
//! No theatrics. No drift. Just data.

use std::time::{Duration, SystemTime};

// ============================================================================
// CONSTITUTIONAL PROBABILITY CURVES (CANONICAL)
// ============================================================================

/// Quorum availability probability at each chaos level
/// Derived from: probability that 5-of-7 vetted operators can assemble
pub fn quorum_probability(chi: u8) -> f64 {
    match chi {
        0 => 0.98,  // Deterministic
        1 => 0.90,  // Noisy
        2 => 0.70,  // Stressed
        3 => 0.22,  // Destabilized - razor's edge
        4 => 0.04,  // Chaotic - systemic breakdown
        _ => 0.01,  // Beyond chaos
    }
}

/// Founder coherence probability at each chaos level
/// Captures epistemic drift under pressure
pub fn coherence_probability(chi: u8) -> f64 {
    match chi {
        0 => 0.96,  // Deterministic
        1 => 0.88,  // Noisy
        2 => 0.63,  // Stressed
        3 => 0.18,  // Destabilized
        4 => 0.02,  // Chaotic
        _ => 0.00,  // Beyond chaos
    }
}

// ============================================================================
// UNRESOLVABLE TRIGGER CONDITIONS
// ============================================================================

/// Days of continuous quorum absence required for UNRESOLVABLE
pub const DEADLOCK_THRESHOLD_DAYS: u64 = 1826;  // 5 years + 1 day

/// Minimum chaos level for UNRESOLVABLE consideration
pub const MIN_CHI_FOR_UNRESOLVABLE: u8 = 3;

/// Check if UNRESOLVABLE conditions are met
pub fn check_unresolvable(
    deadlock_days: u64,
    founders_coherent: bool,
    chi: u8,
) -> bool {
    deadlock_days > DEADLOCK_THRESHOLD_DAYS
        && !founders_coherent
        && chi >= MIN_CHI_FOR_UNRESOLVABLE
}

// ============================================================================
// EPOCH SIMULATION STATE
// ============================================================================

#[derive(Debug, Clone)]
pub struct EpochState {
    pub epoch: u64,
    pub chi: u8,
    pub quorum_available: bool,
    pub founders_coherent: bool,
    pub deadlock_days: u64,
    pub unresolvable: bool,
    pub frozen_canon: bool,
}

#[derive(Debug, Clone)]
pub struct StressTestResult {
    pub chi: u8,
    pub total_epochs: u64,

    // Aggregated metrics
    pub quorum_availability_pct: f64,
    pub founder_coherence_pct: f64,
    pub max_deadlock_days: u64,
    pub unresolvable_triggered: bool,
    pub frozen_canon_triggered: bool,
    pub epoch_of_freeze: Option<u64>,

    // Time series data
    pub deadlock_history: Vec<u64>,
    pub quorum_history: Vec<bool>,
    pub coherence_history: Vec<bool>,
}

// ============================================================================
// DETERMINISTIC STRESS TEST ENGINE
// ============================================================================

/// Run a single stress test at fixed chaos level
pub fn run_stress_test(chi: u8, epochs: u64, seed: u64) -> StressTestResult {
    let mut rng_state = seed;

    let mut quorum_available_count = 0u64;
    let mut coherent_count = 0u64;
    let mut current_deadlock_days = 0u64;
    let mut max_deadlock_days = 0u64;
    let mut unresolvable_triggered = false;
    let mut frozen_canon_triggered = false;
    let mut epoch_of_freeze: Option<u64> = None;

    let mut deadlock_history = Vec::with_capacity(epochs as usize);
    let mut quorum_history = Vec::with_capacity(epochs as usize);
    let mut coherence_history = Vec::with_capacity(epochs as usize);

    let p_quorum = quorum_probability(chi);
    let p_coherence = coherence_probability(chi);

    for epoch in 0..epochs {
        // Deterministic PRNG (xorshift)
        rng_state ^= rng_state << 13;
        rng_state ^= rng_state >> 7;
        rng_state ^= rng_state << 17;
        let roll1 = (rng_state as f64) / (u64::MAX as f64);

        rng_state ^= rng_state << 13;
        rng_state ^= rng_state >> 7;
        rng_state ^= rng_state << 17;
        let roll2 = (rng_state as f64) / (u64::MAX as f64);

        // Sample quorum availability
        let quorum_available = roll1 < p_quorum;
        if quorum_available {
            quorum_available_count += 1;
            current_deadlock_days = 0;  // Reset deadlock counter
        } else {
            current_deadlock_days += 1;  // Each epoch = 1 day
        }

        // Sample founder coherence
        let founders_coherent = roll2 < p_coherence;
        if founders_coherent {
            coherent_count += 1;
        }

        // Track max deadlock
        if current_deadlock_days > max_deadlock_days {
            max_deadlock_days = current_deadlock_days;
        }

        // Check UNRESOLVABLE
        if !unresolvable_triggered && !frozen_canon_triggered {
            if check_unresolvable(current_deadlock_days, founders_coherent, chi) {
                unresolvable_triggered = true;
                frozen_canon_triggered = true;
                epoch_of_freeze = Some(epoch);
            }
        }

        // Record history
        deadlock_history.push(current_deadlock_days);
        quorum_history.push(quorum_available);
        coherence_history.push(founders_coherent);
    }

    StressTestResult {
        chi,
        total_epochs: epochs,
        quorum_availability_pct: (quorum_available_count as f64 / epochs as f64) * 100.0,
        founder_coherence_pct: (coherent_count as f64 / epochs as f64) * 100.0,
        max_deadlock_days,
        unresolvable_triggered,
        frozen_canon_triggered,
        epoch_of_freeze,
        deadlock_history,
        quorum_history,
        coherence_history,
    }
}

/// Compare Χ=3 vs Χ=4 stress tests
pub fn run_comparison(epochs: u64, seed: u64) -> StressTestComparison {
    let chi3_result = run_stress_test(3, epochs, seed);
    let chi4_result = run_stress_test(4, epochs, seed + 1);

    StressTestComparison {
        epochs,
        chi3: chi3_result,
        chi4: chi4_result,
    }
}

#[derive(Debug, Clone)]
pub struct StressTestComparison {
    pub epochs: u64,
    pub chi3: StressTestResult,
    pub chi4: StressTestResult,
}

impl StressTestComparison {
    /// Generate formatted report
    pub fn report(&self) -> String {
        format!(
r#"
╔══════════════════════════════════════════════════════════════════════════════╗
║           STRESS TEST: Χ = 3 (DESTABILIZED) vs Χ = 4 (CHAOTIC)               ║
║                         {epochs} EPOCHS SIMULATION                              ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  PROBABILITY CURVES (Constitutional Canonical):                              ║
║                                                                              ║
║    Χ │ P(quorum) │ P(coherence)                                              ║
║    ──┼───────────┼──────────────                                             ║
║    0 │   98.0%   │    96.0%                                                  ║
║    1 │   90.0%   │    88.0%                                                  ║
║    2 │   70.0%   │    63.0%                                                  ║
║    3 │   22.0%   │    18.0%     ◄─ Razor's edge                              ║
║    4 │    4.0%   │     2.0%     ◄─ Systemic breakdown                        ║
║                                                                              ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  SIMULATION RESULTS:                                                         ║
║                                                                              ║
║                        │     Χ = 3      │     Χ = 4      │                   ║
║    ────────────────────┼────────────────┼────────────────│                   ║
║    Quorum Availability │     {q3:>6.1}%    │     {q4:>6.1}%    │                   ║
║    Founder Coherence   │     {c3:>6.1}%    │     {c4:>6.1}%    │                   ║
║    Max Deadlock Days   │     {d3:>6}     │     {d4:>6}     │                   ║
║    UNRESOLVABLE        │     {u3:^6}     │     {u4:^6}     │                   ║
║    FrozenCanon         │     {f3:^6}     │     {f4:^6}     │                   ║
║    Epoch of Freeze     │     {e3:^6}     │     {e4:^6}     │                   ║
║                                                                              ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  INTERPRETATION:                                                             ║
║                                                                              ║
║  {interpretation}
║                                                                              ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  CONSTITUTIONAL IMPLICATIONS:                                                ║
║                                                                              ║
║  • Row 15 requires {threshold} continuous days of quorum absence               ║
║  • At Χ=3: Expected streak length = {streak3:.1} days before quorum reform      ║
║  • At Χ=4: Expected streak length = {streak4:.1} days before quorum reform      ║
║  • Years to reach threshold at Χ=3: {years3:.1} (statistical expectation)       ║
║  • Years to reach threshold at Χ=4: {years4:.1} (statistical expectation)       ║
║                                                                              ║
║  The machine is allowed to suffer.                                           ║
║  It is not allowed to pretend.                                               ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
"#,
            epochs = self.epochs,
            q3 = self.chi3.quorum_availability_pct,
            q4 = self.chi4.quorum_availability_pct,
            c3 = self.chi3.founder_coherence_pct,
            c4 = self.chi4.founder_coherence_pct,
            d3 = self.chi3.max_deadlock_days,
            d4 = self.chi4.max_deadlock_days,
            u3 = if self.chi3.unresolvable_triggered { "YES" } else { "NO" },
            u4 = if self.chi4.unresolvable_triggered { "YES" } else { "NO" },
            f3 = if self.chi3.frozen_canon_triggered { "YES" } else { "NO" },
            f4 = if self.chi4.frozen_canon_triggered { "YES" } else { "NO" },
            e3 = self.chi3.epoch_of_freeze.map(|e| e.to_string()).unwrap_or_else(|| "N/A".to_string()),
            e4 = self.chi4.epoch_of_freeze.map(|e| e.to_string()).unwrap_or_else(|| "N/A".to_string()),
            interpretation = self.interpret(),
            threshold = DEADLOCK_THRESHOLD_DAYS,
            streak3 = expected_streak_length(quorum_probability(3)),
            streak4 = expected_streak_length(quorum_probability(4)),
            years3 = years_to_threshold(quorum_probability(3)),
            years4 = years_to_threshold(quorum_probability(4)),
        )
    }

    fn interpret(&self) -> &'static str {
        if !self.chi3.unresolvable_triggered && !self.chi4.unresolvable_triggered {
            "Row 15 did NOT trigger in either scenario. This is constitutionally\n\
             ║  expected: UNRESOLVABLE requires 5+ years of continuous quorum absence.\n\
             ║  The system experiences chronic stress, not constitutional death.\n\
             ║  Suffering is not extinction."
        } else if self.chi4.unresolvable_triggered && !self.chi3.unresolvable_triggered {
            "Row 15 triggered at Χ=4 but not Χ=3. This demonstrates the\n\
             ║  constitutional design: the razor's edge between survivable\n\
             ║  stress and systemic collapse is correctly calibrated."
        } else if self.chi3.unresolvable_triggered && self.chi4.unresolvable_triggered {
            "Row 15 triggered in BOTH scenarios. This indicates the simulation\n\
             ║  window exceeded the constitutional threshold. The system died\n\
             ║  honestly in both cases."
        } else {
            "Unexpected state: Χ=3 triggered but Χ=4 did not. Review simulation\n\
             ║  parameters for statistical anomaly."
        }
    }
}

/// Calculate expected streak length before quorum reforms
/// (Geometric distribution: expected value = 1/p)
fn expected_streak_length(p_quorum: f64) -> f64 {
    if p_quorum <= 0.0 {
        f64::INFINITY
    } else {
        (1.0 - p_quorum) / p_quorum
    }
}

/// Calculate expected years to reach UNRESOLVABLE threshold
/// Using probability of N consecutive failures
fn years_to_threshold(p_quorum: f64) -> f64 {
    // Probability of exactly THRESHOLD consecutive failures starting at any point
    // is (1-p)^THRESHOLD
    // Expected attempts before success = 1 / P(success)
    // This is a simplified model

    let p_fail = 1.0 - p_quorum;
    if p_fail >= 1.0 {
        return 0.0;  // Will fail immediately
    }
    if p_fail <= 0.0 {
        return f64::INFINITY;  // Will never fail
    }

    // Expected number of days before a streak of THRESHOLD is reached
    // Using approximation: E[T] ≈ (1 - p^n) / ((1-p) * p^n) where n = threshold
    // For large thresholds and small p, this is approximately 1/p^n

    let threshold = DEADLOCK_THRESHOLD_DAYS as f64;

    // More accurate formula for expected hitting time of a run
    // E[T] = (1 - p_fail^threshold) / (p_quorum * p_fail^threshold) + threshold
    let p_streak = p_fail.powf(threshold);

    if p_streak <= 0.0 {
        return f64::INFINITY;
    }

    let expected_days = (1.0 - p_streak) / (p_quorum * p_streak) + threshold;
    expected_days / 365.25
}

// ============================================================================
// EXTENDED ANALYSIS
// ============================================================================

/// Analyze deadlock streak distribution
pub fn analyze_streaks(result: &StressTestResult) -> StreakAnalysis {
    let mut streak_lengths = Vec::new();
    let mut current_streak = 0u64;

    for &quorum_available in &result.quorum_history {
        if quorum_available {
            if current_streak > 0 {
                streak_lengths.push(current_streak);
            }
            current_streak = 0;
        } else {
            current_streak += 1;
        }
    }

    // Capture final streak if it exists
    if current_streak > 0 {
        streak_lengths.push(current_streak);
    }

    let total_streaks = streak_lengths.len();
    let max_streak = *streak_lengths.iter().max().unwrap_or(&0);
    let avg_streak = if total_streaks > 0 {
        streak_lengths.iter().sum::<u64>() as f64 / total_streaks as f64
    } else {
        0.0
    };

    // Streak distribution buckets
    let mut bucket_0_10 = 0;
    let mut bucket_10_50 = 0;
    let mut bucket_50_100 = 0;
    let mut bucket_100_plus = 0;

    for &len in &streak_lengths {
        match len {
            0..=10 => bucket_0_10 += 1,
            11..=50 => bucket_10_50 += 1,
            51..=100 => bucket_50_100 += 1,
            _ => bucket_100_plus += 1,
        }
    }

    StreakAnalysis {
        total_streaks,
        max_streak,
        avg_streak,
        bucket_0_10,
        bucket_10_50,
        bucket_50_100,
        bucket_100_plus,
    }
}

#[derive(Debug, Clone)]
pub struct StreakAnalysis {
    pub total_streaks: usize,
    pub max_streak: u64,
    pub avg_streak: f64,
    pub bucket_0_10: usize,
    pub bucket_10_50: usize,
    pub bucket_50_100: usize,
    pub bucket_100_plus: usize,
}

impl StreakAnalysis {
    pub fn report(&self) -> String {
        format!(
            r#"
  DEADLOCK STREAK ANALYSIS:
    Total Streaks: {}
    Maximum Streak: {} days
    Average Streak: {:.1} days

    Distribution:
      0-10 days:   {} ({:.1}%)
      11-50 days:  {} ({:.1}%)
      51-100 days: {} ({:.1}%)
      100+ days:   {} ({:.1}%)
"#,
            self.total_streaks,
            self.max_streak,
            self.avg_streak,
            self.bucket_0_10,
            self.bucket_0_10 as f64 / self.total_streaks.max(1) as f64 * 100.0,
            self.bucket_10_50,
            self.bucket_10_50 as f64 / self.total_streaks.max(1) as f64 * 100.0,
            self.bucket_50_100,
            self.bucket_50_100 as f64 / self.total_streaks.max(1) as f64 * 100.0,
            self.bucket_100_plus,
            self.bucket_100_plus as f64 / self.total_streaks.max(1) as f64 * 100.0,
        )
    }
}

// ============================================================================
// VULNERABILITY ANALYSIS
// ============================================================================

/// Identify the critical vulnerability: coherence decay rate
pub fn analyze_vulnerability(chi3: &StressTestResult, chi4: &StressTestResult) -> VulnerabilityReport {
    // The key insight: if coherence degrades faster than quorum,
    // UNRESOLVABLE can trigger even with intermittent quorum

    let quorum_p3 = quorum_probability(3);
    let coherence_p3 = coherence_probability(3);
    let quorum_p4 = quorum_probability(4);
    let coherence_p4 = coherence_probability(4);

    // Ratio of coherence to quorum probability
    let ratio_3 = coherence_p3 / quorum_p3;
    let ratio_4 = coherence_p4 / quorum_p4;

    // If ratio < 1, founders fracture faster than they become unavailable
    // This is the psychological vulnerability
    let psychological_vulnerability = ratio_3 < 1.0 || ratio_4 < 1.0;

    VulnerabilityReport {
        coherence_quorum_ratio_chi3: ratio_3,
        coherence_quorum_ratio_chi4: ratio_4,
        psychological_vulnerability,
        recommendation: if psychological_vulnerability {
            "CRITICAL: Coherence decays faster than availability. \
             Founders may psychologically fracture while quorum intermittently exists. \
             This is the only path to accidental Row 15 trigger."
        } else {
            "LOW RISK: Quorum failure precedes coherence failure. \
             Row 15 trigger requires genuine systemic collapse."
        },
    }
}

#[derive(Debug, Clone)]
pub struct VulnerabilityReport {
    pub coherence_quorum_ratio_chi3: f64,
    pub coherence_quorum_ratio_chi4: f64,
    pub psychological_vulnerability: bool,
    pub recommendation: &'static str,
}

impl VulnerabilityReport {
    pub fn report(&self) -> String {
        format!(
            r#"
╔══════════════════════════════════════════════════════════════════════════════╗
║                       VULNERABILITY ANALYSIS                                 ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  Coherence/Quorum Ratio at Χ=3: {:.2}                                        ║
║  Coherence/Quorum Ratio at Χ=4: {:.2}                                        ║
║                                                                              ║
║  Psychological Vulnerability: {}                                            ║
║                                                                              ║
║  Assessment: {}
║                                                                              ║
║  This is not a cryptographic vulnerability.                                  ║
║  It is a psychological systems-engineering constraint.                       ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
"#,
            self.coherence_quorum_ratio_chi3,
            self.coherence_quorum_ratio_chi4,
            if self.psychological_vulnerability { "PRESENT" } else { "ABSENT" },
            self.recommendation,
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
    fn test_probability_curves() {
        assert!(quorum_probability(3) < quorum_probability(2));
        assert!(quorum_probability(4) < quorum_probability(3));
        assert!(coherence_probability(3) < coherence_probability(2));
        assert!(coherence_probability(4) < coherence_probability(3));
    }

    #[test]
    fn test_unresolvable_check() {
        // Not enough days
        assert!(!check_unresolvable(1000, false, 4));

        // Founders coherent
        assert!(!check_unresolvable(2000, true, 4));

        // Chi too low
        assert!(!check_unresolvable(2000, false, 2));

        // All conditions met
        assert!(check_unresolvable(2000, false, 4));
    }

    #[test]
    fn test_stress_test_runs() {
        let result = run_stress_test(3, 100, 42);
        assert_eq!(result.total_epochs, 100);
        assert_eq!(result.chi, 3);
    }

    #[test]
    fn test_comparison_runs() {
        let comparison = run_comparison(100, 42);
        assert_eq!(comparison.chi3.chi, 3);
        assert_eq!(comparison.chi4.chi, 4);
    }

    #[test]
    fn test_1000_epoch_simulation() {
        let comparison = run_comparison(1000, 42);

        // At 1000 epochs (< 3 years), UNRESOLVABLE should not trigger
        // because we need 5+ years of continuous quorum absence
        assert!(!comparison.chi3.unresolvable_triggered);
        assert!(!comparison.chi4.unresolvable_triggered);

        // Chi4 should have lower quorum availability
        assert!(comparison.chi4.quorum_availability_pct < comparison.chi3.quorum_availability_pct);
    }

    #[test]
    fn test_expected_years_calculation() {
        let years_chi3 = years_to_threshold(quorum_probability(3));
        let years_chi4 = years_to_threshold(quorum_probability(4));

        // Chi4 should reach threshold faster
        assert!(years_chi4 < years_chi3);

        // Both should be > 5 years (the threshold itself)
        assert!(years_chi3 > 5.0);
        assert!(years_chi4 > 5.0);
    }
}
