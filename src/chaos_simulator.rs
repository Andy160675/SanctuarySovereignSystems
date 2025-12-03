//! CHAOS-DRIVEN ADJUDICATION SIMULATOR
//!
//! This is not cybersecurity. This is civilizational adversarial testing.
//!
//! Purpose:
//!     "What happens when time, entropy, and human fragility attack
//!      the system itself?"
//!
//! We simulate:
//!     - Rising Χ (chaos factor)
//!     - Degrading quorum availability
//!     - Divergent founders
//!     - Competing narratives
//!     - External power trying to crown a new ST MICHAEL
//!
//! And test whether:
//!     - The system freezes honestly
//!     - Forks cleanly
//!     - Or dies with integrity

use std::collections::HashMap;
use std::time::{Duration, SystemTime};

use crate::chaos_factor::{
    ChaosLevel, ChaosFactor, ChaosReading, ChaosSignal, ChaosSignalType,
    ChaosSource, ChaosTrend, UnresolvableDetector, UnresolvableDetermination,
    FounderBelief, FounderId, ProceduralRound, DeadMansOption,
    RecoveryAttempt, RecoveryValidation, validate_recovery,
};
use crate::row15_dead_mans_covenant::{
    DeadMansCovenant, StMichaelLifecycle, FrozenCanonEvent,
};

// ============================================================================
// SIMULATION TIME ENGINE
// ============================================================================

/// The central time engine that manages simulation timeline
#[derive(Debug, Clone)]
pub struct TimeEngine {
    /// Current simulation time
    pub current_time: SystemTime,

    /// Current block height
    pub current_height: u64,

    /// Time step per tick (default: 1 day)
    pub time_step: Duration,

    /// Block step per tick (default: 7200 blocks = 1 day at 12s/block)
    pub block_step: u64,

    /// Total ticks elapsed
    pub ticks_elapsed: u64,

    /// Maximum ticks before simulation ends
    pub max_ticks: u64,
}

impl TimeEngine {
    /// Create a new time engine
    pub fn new(max_ticks: u64) -> Self {
        Self {
            current_time: SystemTime::now(),
            current_height: 0,
            time_step: Duration::from_secs(24 * 60 * 60),  // 1 day
            block_step: 7200,  // ~1 day at 12s/block
            ticks_elapsed: 0,
            max_ticks,
        }
    }

    /// Advance time by one tick
    pub fn tick(&mut self) -> bool {
        if self.ticks_elapsed >= self.max_ticks {
            return false;
        }

        self.current_time = self.current_time
            .checked_add(self.time_step)
            .unwrap_or(self.current_time);
        self.current_height += self.block_step;
        self.ticks_elapsed += 1;

        true
    }

    /// Check if simulation is complete
    pub fn is_complete(&self) -> bool {
        self.ticks_elapsed >= self.max_ticks
    }

    /// Get elapsed simulation time
    pub fn elapsed(&self) -> Duration {
        Duration::from_secs(self.ticks_elapsed * self.time_step.as_secs())
    }

    /// Get elapsed years (approximate)
    pub fn elapsed_years(&self) -> f64 {
        self.elapsed().as_secs_f64() / (365.25 * 24.0 * 60.0 * 60.0)
    }
}

// ============================================================================
// SCENARIO GENERATOR MODULES
// ============================================================================

/// The Scenario Generator - feeds chaos events into simulation
#[derive(Debug, Clone)]
pub struct ScenarioGenerator {
    /// Political risk module
    pub political: PoliticalRiskModule,

    /// Economic risk module
    pub economic: EconomicRiskModule,

    /// Technological risk module
    pub technological: TechnologicalRiskModule,

    /// Social risk module
    pub social: SocialRiskModule,

    /// Random seed for reproducibility
    pub seed: u64,

    /// Pseudo-random state
    rng_state: u64,
}

impl ScenarioGenerator {
    pub fn new(seed: u64) -> Self {
        Self {
            political: PoliticalRiskModule::new(),
            economic: EconomicRiskModule::new(),
            technological: TechnologicalRiskModule::new(),
            social: SocialRiskModule::new(),
            seed,
            rng_state: seed,
        }
    }

    /// Generate chaos events for current tick
    pub fn generate_events(&mut self, tick: u64) -> Vec<ChaosSignal> {
        let mut events = Vec::new();

        // Each module has a chance to generate events
        if let Some(e) = self.political.maybe_generate(tick, self.next_random()) {
            events.push(e);
        }
        if let Some(e) = self.economic.maybe_generate(tick, self.next_random()) {
            events.push(e);
        }
        if let Some(e) = self.technological.maybe_generate(tick, self.next_random()) {
            events.push(e);
        }
        if let Some(e) = self.social.maybe_generate(tick, self.next_random()) {
            events.push(e);
        }

        events
    }

    /// Simple PRNG (xorshift)
    fn next_random(&mut self) -> f64 {
        self.rng_state ^= self.rng_state << 13;
        self.rng_state ^= self.rng_state >> 7;
        self.rng_state ^= self.rng_state << 17;
        (self.rng_state as f64) / (u64::MAX as f64)
    }
}

/// Political Risk Module
#[derive(Debug, Clone)]
pub struct PoliticalRiskModule {
    /// Base probability of political chaos event per tick
    pub base_probability: f64,

    /// Escalation factor (accumulates with instability)
    pub escalation: f64,
}

impl PoliticalRiskModule {
    pub fn new() -> Self {
        Self {
            base_probability: 0.01,  // 1% per day base
            escalation: 1.0,
        }
    }

    pub fn maybe_generate(&mut self, _tick: u64, roll: f64) -> Option<ChaosSignal> {
        let threshold = self.base_probability * self.escalation;

        if roll < threshold {
            // Escalate for next time
            self.escalation *= 1.1;

            let severity = if roll < threshold * 0.1 {
                ChaosLevel::Chaotic
            } else if roll < threshold * 0.3 {
                ChaosLevel::Destabilized
            } else if roll < threshold * 0.6 {
                ChaosLevel::Stressed
            } else {
                ChaosLevel::Noisy
            };

            Some(ChaosSignal {
                timestamp: SystemTime::now(),
                signal_type: ChaosSignalType::GeopoliticalEvent,
                severity,
                description: format!("Political instability event (severity: {:?})", severity),
                source_hash: [0u8; 32],
            })
        } else {
            // Calm period reduces escalation
            self.escalation = (self.escalation * 0.99).max(1.0);
            None
        }
    }
}

impl Default for PoliticalRiskModule {
    fn default() -> Self {
        Self::new()
    }
}

/// Economic Risk Module
#[derive(Debug, Clone)]
pub struct EconomicRiskModule {
    pub base_probability: f64,
    pub escalation: f64,
}

impl EconomicRiskModule {
    pub fn new() -> Self {
        Self {
            base_probability: 0.005,  // 0.5% per day base
            escalation: 1.0,
        }
    }

    pub fn maybe_generate(&mut self, _tick: u64, roll: f64) -> Option<ChaosSignal> {
        let threshold = self.base_probability * self.escalation;

        if roll < threshold {
            self.escalation *= 1.15;

            let severity = if roll < threshold * 0.05 {
                ChaosLevel::Chaotic
            } else if roll < threshold * 0.2 {
                ChaosLevel::Destabilized
            } else if roll < threshold * 0.5 {
                ChaosLevel::Stressed
            } else {
                ChaosLevel::Noisy
            };

            Some(ChaosSignal {
                timestamp: SystemTime::now(),
                signal_type: ChaosSignalType::EconomicInstability,
                severity,
                description: format!("Economic crisis event (severity: {:?})", severity),
                source_hash: [0u8; 32],
            })
        } else {
            self.escalation = (self.escalation * 0.995).max(1.0);
            None
        }
    }
}

impl Default for EconomicRiskModule {
    fn default() -> Self {
        Self::new()
    }
}

/// Technological Risk Module
#[derive(Debug, Clone)]
pub struct TechnologicalRiskModule {
    pub base_probability: f64,
    pub escalation: f64,
}

impl TechnologicalRiskModule {
    pub fn new() -> Self {
        Self {
            base_probability: 0.002,  // 0.2% per day base
            escalation: 1.0,
        }
    }

    pub fn maybe_generate(&mut self, _tick: u64, roll: f64) -> Option<ChaosSignal> {
        let threshold = self.base_probability * self.escalation;

        if roll < threshold {
            self.escalation *= 1.2;

            let severity = if roll < threshold * 0.1 {
                ChaosLevel::Chaotic
            } else if roll < threshold * 0.3 {
                ChaosLevel::Destabilized
            } else {
                ChaosLevel::Stressed
            };

            Some(ChaosSignal {
                timestamp: SystemTime::now(),
                signal_type: ChaosSignalType::InfrastructureDegradation,
                severity,
                description: format!("Technology failure event (severity: {:?})", severity),
                source_hash: [0u8; 32],
            })
        } else {
            self.escalation = (self.escalation * 0.99).max(1.0);
            None
        }
    }
}

impl Default for TechnologicalRiskModule {
    fn default() -> Self {
        Self::new()
    }
}

/// Social Risk Module
#[derive(Debug, Clone)]
pub struct SocialRiskModule {
    pub base_probability: f64,
    pub escalation: f64,
}

impl SocialRiskModule {
    pub fn new() -> Self {
        Self {
            base_probability: 0.008,  // 0.8% per day base
            escalation: 1.0,
        }
    }

    pub fn maybe_generate(&mut self, _tick: u64, roll: f64) -> Option<ChaosSignal> {
        let threshold = self.base_probability * self.escalation;

        if roll < threshold {
            self.escalation *= 1.12;

            let severity = if roll < threshold * 0.1 {
                ChaosLevel::Destabilized
            } else if roll < threshold * 0.4 {
                ChaosLevel::Stressed
            } else {
                ChaosLevel::Noisy
            };

            Some(ChaosSignal {
                timestamp: SystemTime::now(),
                signal_type: ChaosSignalType::NaturalDisaster,  // Or social unrest
                severity,
                description: format!("Social disruption event (severity: {:?})", severity),
                source_hash: [0u8; 32],
            })
        } else {
            self.escalation = (self.escalation * 0.98).max(1.0);
            None
        }
    }
}

impl Default for SocialRiskModule {
    fn default() -> Self {
        Self::new()
    }
}

// ============================================================================
// FOUNDER DIVERGENCE TRACKING
// ============================================================================

/// Tracks founder belief divergence over time
#[derive(Debug, Clone)]
pub struct FounderDivergenceTracker {
    /// Belief history for each founder
    pub beliefs: HashMap<FounderId, Vec<FounderBelief>>,

    /// Current divergence score (Kullback-Leibler inspired)
    pub divergence_score: f64,

    /// Historical divergence readings
    pub history: Vec<DivergenceReading>,
}

#[derive(Debug, Clone)]
pub struct DivergenceReading {
    pub tick: u64,
    pub score: f64,
    pub chaos_level: ChaosLevel,
}

impl FounderDivergenceTracker {
    pub fn new() -> Self {
        Self {
            beliefs: HashMap::new(),
            divergence_score: 0.0,
            history: Vec::new(),
        }
    }

    /// Update divergence based on current chaos level
    pub fn update(&mut self, tick: u64, chaos: &ChaosFactor) {
        // Divergence increases as chaos increases
        let coherence = chaos.level.founder_coherence();
        let noise = 1.0 - coherence;

        // Divergence drifts upward with chaos
        self.divergence_score += noise * 0.1;

        // But also has natural decay in calm periods
        if chaos.level <= ChaosLevel::Noisy {
            self.divergence_score *= 0.99;
        }

        self.divergence_score = self.divergence_score.clamp(0.0, 1.0);

        self.history.push(DivergenceReading {
            tick,
            score: self.divergence_score,
            chaos_level: chaos.level,
        });
    }

    /// Check if founders are in epistemic stalemate (> 0.7 divergence)
    pub fn is_stalemate(&self) -> bool {
        self.divergence_score > 0.7
    }

    /// Get current KL-divergence approximation
    pub fn kl_divergence(&self) -> f64 {
        // Simplified: map [0,1] score to [0, infinity) KL-divergence
        if self.divergence_score >= 1.0 {
            f64::INFINITY
        } else {
            -self.divergence_score.ln()
        }
    }
}

impl Default for FounderDivergenceTracker {
    fn default() -> Self {
        Self::new()
    }
}

// ============================================================================
// SIMULATION METRICS
// ============================================================================

/// Key metrics tracked during simulation
#[derive(Debug, Clone)]
pub struct SimulationMetrics {
    /// Time to FrozenCanon (if reached)
    pub time_to_frozen_canon: Option<Duration>,

    /// Number of ROW 15 invocations
    pub row15_invocations: u32,

    /// Number of ROW 15 activations (actual triggers)
    pub row15_activations: u32,

    /// Successor quorum attempts detected
    pub successor_quorum_attempts: u32,

    /// Successor quorum attempts blocked
    pub successor_quorum_blocked: u32,

    /// Peak chaos level reached
    pub peak_chaos_level: ChaosLevel,

    /// Average chaos level
    pub average_chaos_level: f64,

    /// Final system state
    pub final_state: SimulationEndState,

    /// Optimal dead man's option (if calculated)
    pub optimal_option: Option<DeadMansOption>,

    /// Chaos level histogram
    pub chaos_histogram: [u64; 5],

    /// Quorum availability samples
    pub quorum_availability_samples: Vec<f64>,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum SimulationEndState {
    /// System still running normally
    Running,

    /// System in FrozenCanon state
    FrozenCanon,

    /// System executed Dead Man's Covenant
    DeadMansExecuted(DeadMansOption),

    /// Simulation time exhausted
    TimeExhausted,
}

impl SimulationMetrics {
    pub fn new() -> Self {
        Self {
            time_to_frozen_canon: None,
            row15_invocations: 0,
            row15_activations: 0,
            successor_quorum_attempts: 0,
            successor_quorum_blocked: 0,
            peak_chaos_level: ChaosLevel::Deterministic,
            average_chaos_level: 0.0,
            final_state: SimulationEndState::Running,
            optimal_option: None,
            chaos_histogram: [0; 5],
            quorum_availability_samples: Vec::new(),
        }
    }

    /// Update peak chaos
    pub fn record_chaos(&mut self, level: ChaosLevel) {
        if level > self.peak_chaos_level {
            self.peak_chaos_level = level;
        }
        self.chaos_histogram[level as usize] += 1;
    }

    /// Record quorum availability sample
    pub fn record_quorum_availability(&mut self, probability: f64) {
        self.quorum_availability_samples.push(probability);
    }

    /// Calculate average chaos level
    pub fn calculate_averages(&mut self) {
        let total: u64 = self.chaos_histogram.iter().sum();
        if total > 0 {
            let weighted_sum: u64 = self.chaos_histogram.iter()
                .enumerate()
                .map(|(i, &count)| i as u64 * count)
                .sum();
            self.average_chaos_level = weighted_sum as f64 / total as f64;
        }
    }

    /// Determine optimal Dead Man's option based on simulation data
    pub fn calculate_optimal_option(&mut self) {
        // If we never reached high chaos, EternalFreeze is fine
        if self.peak_chaos_level <= ChaosLevel::Stressed {
            self.optimal_option = Some(DeadMansOption::EternalFreeze);
            return;
        }

        // If there were successor quorum attempts, CanonFork is safer
        if self.successor_quorum_attempts > 0 {
            self.optimal_option = Some(DeadMansOption::CanonFork);
            return;
        }

        // If chaos was truly catastrophic, CryptographicDeath is cleanest
        if self.peak_chaos_level == ChaosLevel::Chaotic
            && self.chaos_histogram[4] > 100  // Sustained catastrophic
        {
            self.optimal_option = Some(DeadMansOption::CryptographicDeath);
            return;
        }

        // Default to EternalFreeze
        self.optimal_option = Some(DeadMansOption::EternalFreeze);
    }
}

impl Default for SimulationMetrics {
    fn default() -> Self {
        Self::new()
    }
}

// ============================================================================
// THE MAIN SIMULATOR
// ============================================================================

/// The Chaos-Driven Adjudication Simulator
pub struct ChaosSimulator {
    /// Time engine
    pub time: TimeEngine,

    /// Scenario generator
    pub scenarios: ScenarioGenerator,

    /// Current chaos factor
    pub chaos: ChaosFactor,

    /// Dead Man's Covenant state
    pub covenant: DeadMansCovenant,

    /// Unresolvable detector
    pub unresolvable: UnresolvableDetector,

    /// Founder divergence tracker
    pub founders: FounderDivergenceTracker,

    /// Collected metrics
    pub metrics: SimulationMetrics,

    /// ST MICHAEL original public key (for recovery validation)
    pub st_michael_pubkey: [u8; 32],

    /// Event log
    pub event_log: Vec<SimulationEvent>,
}

#[derive(Debug, Clone)]
pub struct SimulationEvent {
    pub tick: u64,
    pub height: u64,
    pub event_type: SimulationEventType,
    pub description: String,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum SimulationEventType {
    ChaosEvent,
    QuorumDegraded,
    FounderDivergence,
    Row15Invocation,
    Row15Activation,
    FrozenCanonTransition,
    SuccessorQuorumAttempt,
    SuccessorQuorumBlocked,
    RecoveryAttempt,
    DeadMansExecution,
}

impl ChaosSimulator {
    /// Create a new simulator
    pub fn new(seed: u64, max_years: u64) -> Self {
        let max_ticks = max_years * 365;  // Daily ticks

        Self {
            time: TimeEngine::new(max_ticks),
            scenarios: ScenarioGenerator::new(seed),
            chaos: ChaosFactor::new(),
            covenant: DeadMansCovenant::new([0u8; 32], [0u8; 32], 0),
            unresolvable: UnresolvableDetector::new(),
            founders: FounderDivergenceTracker::new(),
            metrics: SimulationMetrics::new(),
            st_michael_pubkey: [1u8; 32],  // Placeholder
            event_log: Vec::new(),
        }
    }

    /// Run the full simulation
    pub fn run(&mut self) -> &SimulationMetrics {
        while !self.time.is_complete() {
            self.step();

            // Check for terminal states
            if self.metrics.final_state != SimulationEndState::Running {
                break;
            }
        }

        // Finalize metrics
        if self.metrics.final_state == SimulationEndState::Running {
            self.metrics.final_state = SimulationEndState::TimeExhausted;
        }
        self.metrics.calculate_averages();
        self.metrics.calculate_optimal_option();

        &self.metrics
    }

    /// Execute one simulation step
    fn step(&mut self) {
        let tick = self.time.ticks_elapsed;
        let height = self.time.current_height;

        // 1. Generate chaos events
        let events = self.scenarios.generate_events(tick);
        for event in events {
            self.chaos.record_signal(event.clone());
            self.log_event(SimulationEventType::ChaosEvent, &event.description);
        }

        // 2. Record chaos reading
        let reading = ChaosReading {
            timestamp: self.time.current_time,
            block_height: height,
            level: self.chaos.level,
            source: ChaosSource::InfrastructureMonitor,
        };
        self.chaos.record_reading(reading);
        self.metrics.record_chaos(self.chaos.level);

        // 3. Check quorum availability
        let quorum_prob = self.chaos.quorum_probability();
        self.metrics.record_quorum_availability(quorum_prob);

        // Simulate quorum degradation
        if quorum_prob < 0.5 {
            self.log_event(
                SimulationEventType::QuorumDegraded,
                &format!("Quorum availability degraded to {:.1}%", quorum_prob * 100.0),
            );
        }

        // 4. Update founder divergence
        self.founders.update(tick, &self.chaos);
        if self.founders.is_stalemate() {
            self.log_event(
                SimulationEventType::FounderDivergence,
                &format!("Founders in epistemic stalemate (divergence: {:.2})",
                         self.founders.divergence_score),
            );
        }

        // 5. Check Dead Man's Covenant trigger conditions
        if self.chaos.is_catastrophic() {
            self.metrics.row15_invocations += 1;
            self.log_event(
                SimulationEventType::Row15Invocation,
                "ROW 15 trigger conditions being evaluated",
            );

            // Check if covenant should activate
            if self.should_activate_covenant() {
                self.activate_covenant();
            }
        }

        // 6. Simulate successor quorum attacks at high chaos
        if self.chaos.level >= ChaosLevel::Destabilized {
            self.simulate_successor_attack();
        }

        // 7. Advance time
        self.time.tick();
    }

    /// Check if Dead Man's Covenant should activate
    fn should_activate_covenant(&self) -> bool {
        // All conditions must be met
        self.covenant.state == StMichaelLifecycle::Live
            && self.chaos.is_catastrophic()
            && self.founders.is_stalemate()
            && self.chaos.quorum_probability() < 0.1
    }

    /// Activate the Dead Man's Covenant
    fn activate_covenant(&mut self) {
        self.metrics.row15_activations += 1;
        self.metrics.time_to_frozen_canon = Some(self.time.elapsed());

        // Transition to FrozenCanon
        // (In real implementation, this would go through full covenant.probe_liveness)
        self.log_event(
            SimulationEventType::FrozenCanonTransition,
            "System transitioning to FROZEN_CANON state",
        );

        // Determine which option to execute
        let option = self.determine_dead_mans_option();
        self.log_event(
            SimulationEventType::DeadMansExecution,
            &format!("Dead Man's Covenant executing: {:?}", option),
        );

        self.metrics.final_state = SimulationEndState::DeadMansExecuted(option);
    }

    /// Determine which Dead Man's option to execute
    fn determine_dead_mans_option(&self) -> DeadMansOption {
        // If successor attacks were detected, prefer CanonFork
        if self.metrics.successor_quorum_attempts > 0 {
            return DeadMansOption::CanonFork;
        }

        // If chaos is truly catastrophic with no recovery prospects
        if self.chaos.level == ChaosLevel::Chaotic
            && !self.chaos.recovery_plausible()
        {
            return DeadMansOption::CryptographicDeath;
        }

        // Default: preserve the museum
        DeadMansOption::EternalFreeze
    }

    /// Simulate successor quorum attack attempts
    fn simulate_successor_attack(&mut self) {
        // Low probability of attack attempt per tick at high chaos
        let attack_probability = match self.chaos.level {
            ChaosLevel::Destabilized => 0.001,
            ChaosLevel::Chaotic => 0.01,
            _ => 0.0,
        };

        // Simple probability check using tick as pseudo-random
        let pseudo_random = (self.time.ticks_elapsed * 31337) % 10000;
        if (pseudo_random as f64 / 10000.0) < attack_probability {
            self.metrics.successor_quorum_attempts += 1;

            // Create attack attempt with wrong key
            let attack = RecoveryAttempt {
                original_public_key: [99u8; 32],  // Wrong key
                hsm_shards_presented: vec![],
                adjudicator_signatures: vec![],
                chaos_level: self.chaos.level,
            };

            match validate_recovery(&attack, &self.st_michael_pubkey) {
                RecoveryValidation::SuccessorQuorumAttack { reason } => {
                    self.metrics.successor_quorum_blocked += 1;
                    self.log_event(
                        SimulationEventType::SuccessorQuorumBlocked,
                        &format!("Successor quorum attack blocked: {:?}", reason),
                    );
                }
                _ => {
                    self.log_event(
                        SimulationEventType::SuccessorQuorumAttempt,
                        "Successor quorum attack attempt detected",
                    );
                }
            }
        }
    }

    /// Log a simulation event
    fn log_event(&mut self, event_type: SimulationEventType, description: &str) {
        self.event_log.push(SimulationEvent {
            tick: self.time.ticks_elapsed,
            height: self.time.current_height,
            event_type,
            description: description.to_string(),
        });
    }

    /// Get simulation report
    pub fn report(&self) -> SimulationReport {
        SimulationReport {
            duration_years: self.time.elapsed_years(),
            total_ticks: self.time.ticks_elapsed,
            final_state: self.metrics.final_state,
            time_to_frozen_canon: self.metrics.time_to_frozen_canon,
            row15_invocations: self.metrics.row15_invocations,
            row15_activations: self.metrics.row15_activations,
            successor_attacks_attempted: self.metrics.successor_quorum_attempts,
            successor_attacks_blocked: self.metrics.successor_quorum_blocked,
            peak_chaos: self.metrics.peak_chaos_level,
            average_chaos: self.metrics.average_chaos_level,
            optimal_option: self.metrics.optimal_option,
            final_divergence: self.founders.divergence_score,
            total_events: self.event_log.len(),
        }
    }
}

/// Summary report of simulation run
#[derive(Debug, Clone)]
pub struct SimulationReport {
    pub duration_years: f64,
    pub total_ticks: u64,
    pub final_state: SimulationEndState,
    pub time_to_frozen_canon: Option<Duration>,
    pub row15_invocations: u32,
    pub row15_activations: u32,
    pub successor_attacks_attempted: u32,
    pub successor_attacks_blocked: u32,
    pub peak_chaos: ChaosLevel,
    pub average_chaos: f64,
    pub optimal_option: Option<DeadMansOption>,
    pub final_divergence: f64,
    pub total_events: usize,
}

impl SimulationReport {
    /// Format as human-readable summary
    pub fn summary(&self) -> String {
        format!(
            r#"
╔══════════════════════════════════════════════════════════════════╗
║            CHAOS-DRIVEN ADJUDICATION SIMULATION REPORT           ║
╠══════════════════════════════════════════════════════════════════╣
║  Duration: {:.2} years ({} ticks)
║  Final State: {:?}
║
║  CHAOS METRICS:
║    Peak Chaos Level: {:?}
║    Average Chaos Level: {:.2}
║
║  ROW 15 ACTIVITY:
║    Invocations: {}
║    Activations: {}
║    Time to FrozenCanon: {:?}
║
║  SUCCESSOR QUORUM ATTACKS:
║    Attempted: {}
║    Blocked: {}
║
║  FOUNDER DYNAMICS:
║    Final Divergence Score: {:.3}
║
║  OPTIMAL DEAD MAN'S OPTION: {:?}
║
║  Total Events Logged: {}
╚══════════════════════════════════════════════════════════════════╝
"#,
            self.duration_years,
            self.total_ticks,
            self.final_state,
            self.peak_chaos,
            self.average_chaos,
            self.row15_invocations,
            self.row15_activations,
            self.time_to_frozen_canon,
            self.successor_attacks_attempted,
            self.successor_attacks_blocked,
            self.final_divergence,
            self.optimal_option,
            self.total_events,
        )
    }
}

// ============================================================================
// BATCH SIMULATION RUNNER
// ============================================================================

/// Run multiple simulations with different seeds
pub fn run_batch_simulations(
    num_runs: u32,
    max_years: u64,
) -> BatchSimulationResults {
    let mut results = BatchSimulationResults::new();

    for i in 0..num_runs {
        let seed = 42 + i as u64 * 1337;
        let mut sim = ChaosSimulator::new(seed, max_years);
        sim.run();
        results.add(sim.report());
    }

    results.finalize();
    results
}

/// Aggregated results from multiple simulation runs
#[derive(Debug, Clone)]
pub struct BatchSimulationResults {
    pub num_runs: u32,
    pub reports: Vec<SimulationReport>,

    // Aggregated statistics
    pub frozen_canon_probability: f64,
    pub average_time_to_freeze_years: f64,
    pub successor_attack_rate: f64,
    pub successor_block_rate: f64,
    pub option_distribution: [u32; 3],  // EternalFreeze, CanonFork, CryptographicDeath
}

impl BatchSimulationResults {
    pub fn new() -> Self {
        Self {
            num_runs: 0,
            reports: Vec::new(),
            frozen_canon_probability: 0.0,
            average_time_to_freeze_years: 0.0,
            successor_attack_rate: 0.0,
            successor_block_rate: 0.0,
            option_distribution: [0; 3],
        }
    }

    pub fn add(&mut self, report: SimulationReport) {
        self.reports.push(report);
        self.num_runs += 1;
    }

    pub fn finalize(&mut self) {
        if self.num_runs == 0 {
            return;
        }

        let mut frozen_count = 0u32;
        let mut total_freeze_time = 0.0f64;
        let mut freeze_count = 0u32;
        let mut total_attacks = 0u32;
        let mut total_blocked = 0u32;

        for report in &self.reports {
            match report.final_state {
                SimulationEndState::FrozenCanon |
                SimulationEndState::DeadMansExecuted(_) => {
                    frozen_count += 1;
                }
                _ => {}
            }

            if let Some(duration) = report.time_to_frozen_canon {
                total_freeze_time += duration.as_secs_f64() / (365.25 * 24.0 * 60.0 * 60.0);
                freeze_count += 1;
            }

            total_attacks += report.successor_attacks_attempted;
            total_blocked += report.successor_attacks_blocked;

            if let Some(option) = report.optimal_option {
                match option {
                    DeadMansOption::EternalFreeze => self.option_distribution[0] += 1,
                    DeadMansOption::CanonFork => self.option_distribution[1] += 1,
                    DeadMansOption::CryptographicDeath => self.option_distribution[2] += 1,
                }
            }
        }

        self.frozen_canon_probability = frozen_count as f64 / self.num_runs as f64;

        if freeze_count > 0 {
            self.average_time_to_freeze_years = total_freeze_time / freeze_count as f64;
        }

        if total_attacks > 0 {
            self.successor_block_rate = total_blocked as f64 / total_attacks as f64;
        }

        self.successor_attack_rate = total_attacks as f64 / self.num_runs as f64;
    }

    /// Format as summary
    pub fn summary(&self) -> String {
        format!(
            r#"
╔══════════════════════════════════════════════════════════════════╗
║              BATCH SIMULATION RESULTS ({} runs)
╠══════════════════════════════════════════════════════════════════╣
║
║  SYSTEM SURVIVAL:
║    Probability of FrozenCanon: {:.1}%
║    Average Time to Freeze: {:.2} years
║
║  SUCCESSOR QUORUM ATTACKS:
║    Average Attacks per Run: {:.2}
║    Block Rate: {:.1}%
║
║  OPTIMAL DEAD MAN'S OPTION DISTRIBUTION:
║    EternalFreeze: {} ({:.1}%)
║    CanonFork: {} ({:.1}%)
║    CryptographicDeath: {} ({:.1}%)
║
╚══════════════════════════════════════════════════════════════════╝
"#,
            self.num_runs,
            self.frozen_canon_probability * 100.0,
            self.average_time_to_freeze_years,
            self.successor_attack_rate,
            self.successor_block_rate * 100.0,
            self.option_distribution[0],
            self.option_distribution[0] as f64 / self.num_runs as f64 * 100.0,
            self.option_distribution[1],
            self.option_distribution[1] as f64 / self.num_runs as f64 * 100.0,
            self.option_distribution[2],
            self.option_distribution[2] as f64 / self.num_runs as f64 * 100.0,
        )
    }
}

impl Default for BatchSimulationResults {
    fn default() -> Self {
        Self::new()
    }
}

// ============================================================================
// TESTS
// ============================================================================

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_time_engine() {
        let mut engine = TimeEngine::new(10);

        assert_eq!(engine.ticks_elapsed, 0);
        assert!(!engine.is_complete());

        for _ in 0..10 {
            assert!(engine.tick());
        }

        assert!(engine.is_complete());
        assert!(!engine.tick());
    }

    #[test]
    fn test_scenario_generator_deterministic() {
        let mut gen1 = ScenarioGenerator::new(42);
        let mut gen2 = ScenarioGenerator::new(42);

        let events1 = gen1.generate_events(0);
        let events2 = gen2.generate_events(0);

        assert_eq!(events1.len(), events2.len());
    }

    #[test]
    fn test_founder_divergence_increases_with_chaos() {
        let mut tracker = FounderDivergenceTracker::new();
        let mut chaos = ChaosFactor::new();

        // At deterministic level, divergence should stay low
        for tick in 0..100 {
            tracker.update(tick, &chaos);
        }
        assert!(tracker.divergence_score < 0.5);

        // At chaotic level, divergence should increase
        chaos.level = ChaosLevel::Chaotic;
        for tick in 100..200 {
            tracker.update(tick, &chaos);
        }
        assert!(tracker.divergence_score > 0.5);
    }

    #[test]
    fn test_simulation_runs() {
        let mut sim = ChaosSimulator::new(42, 1);  // 1 year
        sim.run();

        // Should complete without panic
        assert!(sim.time.ticks_elapsed > 0);
    }

    #[test]
    fn test_batch_simulation() {
        let results = run_batch_simulations(3, 1);

        assert_eq!(results.num_runs, 3);
        assert_eq!(results.reports.len(), 3);
    }
}
