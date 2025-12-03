//! CHAOS FACTOR (Χ) — The Stochastic Modifier for Human Fragility
//!
//! Philosophy:
//!     "Chaos never modifies proof math. It modifies availability and trust
//!      of human-linked inputs."
//!
//! This module models the uncomfortable truth: the system's greatest
//! vulnerability is not cryptographic. It is civilizational.
//!
//! At Χ ≥ 4, the probability that ST MICHAEL becomes permanently
//! unreachable tends toward 1. The adversary doesn't attack the crypto.
//! They wait for Χ to rise.

use std::time::{Duration, SystemTime};

// ============================================================================
// CHAOS FACTOR SCALE
// ============================================================================

/// The 5-level discrete chaos index
///
/// We do NOT use 0-1 continuous. That's too smooth for human reality.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash)]
#[repr(u8)]
pub enum ChaosLevel {
    /// Χ = 0: Humans behave as specified. Idealized world.
    Deterministic = 0,

    /// Χ = 1: Minor latency, errors, fatigue.
    Noisy = 1,

    /// Χ = 2: Burnout, delayed response, partial data loss.
    Stressed = 2,

    /// Χ = 3: Political pressure, disinformation, internal fractures.
    Destabilized = 3,

    /// Χ = 4: War, pandemics, infrastructural collapse.
    Chaotic = 4,
}

impl ChaosLevel {
    /// Probability that quorum is available at this chaos level
    pub fn quorum_availability_probability(&self) -> f64 {
        match self {
            ChaosLevel::Deterministic => 1.00,
            ChaosLevel::Noisy => 0.95,
            ChaosLevel::Stressed => 0.75,
            ChaosLevel::Destabilized => 0.40,
            ChaosLevel::Chaotic => 0.05,
        }
    }

    /// Probability that cooling period is respected at this chaos level
    pub fn cooling_period_integrity(&self) -> f64 {
        match self {
            ChaosLevel::Deterministic => 1.00,
            ChaosLevel::Noisy => 0.98,
            ChaosLevel::Stressed => 0.85,
            ChaosLevel::Destabilized => 0.50,  // Violated at Χ ≥ 3
            ChaosLevel::Chaotic => 0.10,
        }
    }

    /// Founder coherence factor (ability to reach agreement)
    pub fn founder_coherence(&self) -> f64 {
        match self {
            ChaosLevel::Deterministic => 1.00,
            ChaosLevel::Noisy => 0.90,
            ChaosLevel::Stressed => 0.60,  // Decays at Χ ≥ 2
            ChaosLevel::Destabilized => 0.30,
            ChaosLevel::Chaotic => 0.05,
        }
    }

    /// Source diversity degradation factor
    pub fn source_diversity_factor(&self) -> f64 {
        match self {
            ChaosLevel::Deterministic => 1.00,
            ChaosLevel::Noisy => 0.92,
            ChaosLevel::Stressed => 0.70,
            ChaosLevel::Destabilized => 0.35,
            ChaosLevel::Chaotic => 0.08,
        }
    }

    /// Human-readable label
    pub fn label(&self) -> &'static str {
        match self {
            ChaosLevel::Deterministic => "Deterministic",
            ChaosLevel::Noisy => "Noisy",
            ChaosLevel::Stressed => "Stressed",
            ChaosLevel::Destabilized => "Destabilized",
            ChaosLevel::Chaotic => "Chaotic",
        }
    }

    /// From raw u8 value
    pub fn from_u8(value: u8) -> Option<Self> {
        match value {
            0 => Some(ChaosLevel::Deterministic),
            1 => Some(ChaosLevel::Noisy),
            2 => Some(ChaosLevel::Stressed),
            3 => Some(ChaosLevel::Destabilized),
            4 => Some(ChaosLevel::Chaotic),
            _ => None,
        }
    }
}

// ============================================================================
// CHAOS FACTOR STATE
// ============================================================================

/// Time-varying chaos state
#[derive(Debug, Clone)]
pub struct ChaosFactor {
    /// Current chaos level
    pub level: ChaosLevel,

    /// When this level was established
    pub level_since: SystemTime,

    /// Historical chaos readings (for trend analysis)
    pub history: Vec<ChaosReading>,

    /// External chaos signals received
    pub signals: Vec<ChaosSignal>,
}

#[derive(Debug, Clone)]
pub struct ChaosReading {
    pub timestamp: SystemTime,
    pub block_height: u64,
    pub level: ChaosLevel,
    pub source: ChaosSource,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ChaosSource {
    /// Automated infrastructure monitoring
    InfrastructureMonitor,

    /// Adjudicator availability check
    AdjudicatorProbe,

    /// External world event feed
    ExternalEventFeed,

    /// Manual operator assessment
    OperatorAssessment,

    /// Founder declaration
    FounderDeclaration,
}

#[derive(Debug, Clone)]
pub struct ChaosSignal {
    pub timestamp: SystemTime,
    pub signal_type: ChaosSignalType,
    pub severity: ChaosLevel,
    pub description: String,
    pub source_hash: [u8; 32],
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ChaosSignalType {
    /// Infrastructure degradation detected
    InfrastructureDegradation,

    /// Adjudicator unreachable
    AdjudicatorUnreachable,

    /// Communication channel compromised
    ChannelCompromised,

    /// External geopolitical event
    GeopoliticalEvent,

    /// Pandemic or natural disaster
    NaturalDisaster,

    /// Active conflict in adjudicator jurisdiction
    ActiveConflict,

    /// Economic system instability
    EconomicInstability,
}

impl ChaosFactor {
    /// Create new chaos factor at deterministic level
    pub fn new() -> Self {
        Self {
            level: ChaosLevel::Deterministic,
            level_since: SystemTime::now(),
            history: Vec::new(),
            signals: Vec::new(),
        }
    }

    /// Record a chaos reading
    pub fn record_reading(&mut self, reading: ChaosReading) {
        self.history.push(reading.clone());

        // Update level if reading is higher
        if reading.level > self.level {
            self.level = reading.level;
            self.level_since = reading.timestamp;
        }

        // Trim history to last 1000 readings
        if self.history.len() > 1000 {
            self.history.drain(0..100);
        }
    }

    /// Record a chaos signal
    pub fn record_signal(&mut self, signal: ChaosSignal) {
        // Update level based on signal severity
        if signal.severity > self.level {
            self.level = signal.severity;
            self.level_since = signal.timestamp;
        }

        self.signals.push(signal);

        // Trim signals to last 500
        if self.signals.len() > 500 {
            self.signals.drain(0..50);
        }
    }

    /// Calculate trend over time window
    pub fn trend(&self, window: Duration) -> ChaosTrend {
        let cutoff = SystemTime::now()
            .checked_sub(window)
            .unwrap_or(SystemTime::UNIX_EPOCH);

        let recent: Vec<_> = self.history.iter()
            .filter(|r| r.timestamp >= cutoff)
            .collect();

        if recent.len() < 2 {
            return ChaosTrend::Stable;
        }

        let first_half: f64 = recent[..recent.len() / 2]
            .iter()
            .map(|r| r.level as u8 as f64)
            .sum::<f64>() / (recent.len() / 2) as f64;

        let second_half: f64 = recent[recent.len() / 2..]
            .iter()
            .map(|r| r.level as u8 as f64)
            .sum::<f64>() / (recent.len() - recent.len() / 2) as f64;

        let delta = second_half - first_half;

        if delta > 0.5 {
            ChaosTrend::Rising
        } else if delta < -0.5 {
            ChaosTrend::Falling
        } else {
            ChaosTrend::Stable
        }
    }

    /// Check if chaos is at catastrophic level
    pub fn is_catastrophic(&self) -> bool {
        self.level == ChaosLevel::Chaotic
    }

    /// Check if recovery is plausible (Χ ≤ 1)
    pub fn recovery_plausible(&self) -> bool {
        self.level <= ChaosLevel::Noisy
    }

    /// Get current quorum availability probability
    pub fn quorum_probability(&self) -> f64 {
        self.level.quorum_availability_probability()
    }
}

impl Default for ChaosFactor {
    fn default() -> Self {
        Self::new()
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ChaosTrend {
    Rising,
    Stable,
    Falling,
}

// ============================================================================
// UNRESOLVABLE DEADLOCK DETECTION
// ============================================================================

/// Constitutional constants for UNRESOLVABLE determination
pub mod unresolvable_thresholds {
    /// Founders decision window (180 days)
    pub const FOUNDERS_DECISION_WINDOW_DAYS: u64 = 180;
    pub const FOUNDERS_DECISION_WINDOW_SECS: u64 = FOUNDERS_DECISION_WINDOW_DAYS * 24 * 60 * 60;

    /// Minimum procedural rounds before UNRESOLVABLE
    pub const MIN_PROCEDURAL_ROUNDS: u32 = 3;

    /// Cooling period per round (30 days)
    pub const COOLING_PER_ROUND_DAYS: u64 = 30;
    pub const COOLING_PER_ROUND_SECS: u64 = COOLING_PER_ROUND_DAYS * 24 * 60 * 60;

    /// Epsilon for founder belief divergence
    pub const EPSILON_FOUNDERS: u128 = 100_000;
}

/// Founder belief vector (signed position on evidence)
#[derive(Debug, Clone)]
pub struct FounderBelief {
    /// Founder identifier (A, B, or C)
    pub founder_id: FounderId,

    /// Evidence root this belief is over
    pub evidence_root: [u8; 32],

    /// The belief vector (domain-specific encoding)
    pub belief_vector: Vec<u8>,

    /// Dilithium signature over (evidence_root || belief_vector)
    pub signature: [u8; 64],

    /// Timestamp of submission
    pub submitted_at: SystemTime,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub enum FounderId {
    A,
    B,
    C,
}

/// Procedural round record
#[derive(Debug, Clone)]
pub struct ProceduralRound {
    /// Round number (1-indexed)
    pub round_number: u32,

    /// Evidence presented this round
    pub evidence_root: [u8; 32],

    /// External expert packets ingested
    pub expert_packets: Vec<[u8; 32]>,

    /// Cooling period start
    pub cooling_started: SystemTime,

    /// Cooling period end
    pub cooling_ended: Option<SystemTime>,

    /// Founder beliefs submitted this round
    pub beliefs: Vec<FounderBelief>,

    /// Did convergence occur?
    pub converged: bool,
}

/// The UNRESOLVABLE determination engine
#[derive(Debug, Clone)]
pub struct UnresolvableDetector {
    /// When the decision window opened
    pub window_opened: SystemTime,

    /// All founder beliefs submitted
    pub beliefs: Vec<FounderBelief>,

    /// All procedural rounds
    pub rounds: Vec<ProceduralRound>,

    /// Current determination
    pub determination: UnresolvableDetermination,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum UnresolvableDetermination {
    /// Still within decision window, process ongoing
    Pending,

    /// Resolved - founders reached agreement
    Resolved,

    /// UNRESOLVABLE - all three conditions met
    Unresolvable,
}

impl UnresolvableDetector {
    pub fn new() -> Self {
        Self {
            window_opened: SystemTime::now(),
            beliefs: Vec::new(),
            rounds: Vec::new(),
            determination: UnresolvableDetermination::Pending,
        }
    }

    /// Open a new decision window
    pub fn open_window(&mut self) {
        self.window_opened = SystemTime::now();
        self.beliefs.clear();
        self.rounds.clear();
        self.determination = UnresolvableDetermination::Pending;
    }

    /// Submit a founder belief
    pub fn submit_belief(&mut self, belief: FounderBelief) {
        self.beliefs.push(belief);
        self.check_determination();
    }

    /// Complete a procedural round
    pub fn complete_round(&mut self, round: ProceduralRound) {
        self.rounds.push(round);
        self.check_determination();
    }

    /// Check all three UNRESOLVABLE conditions
    fn check_determination(&mut self) {
        // Check for resolution first
        if self.check_resolution() {
            self.determination = UnresolvableDetermination::Resolved;
            return;
        }

        let temporal = self.check_temporal_exhaustion();
        let epistemic = self.check_epistemic_stalemate();
        let procedural = self.check_procedural_exhaustion();

        if temporal && epistemic && procedural {
            self.determination = UnresolvableDetermination::Unresolvable;
        }
    }

    /// Check if founders have resolved (≥2 agree)
    fn check_resolution(&self) -> bool {
        // Get latest belief from each founder
        let latest_a = self.beliefs.iter().rev().find(|b| b.founder_id == FounderId::A);
        let latest_b = self.beliefs.iter().rev().find(|b| b.founder_id == FounderId::B);
        let latest_c = self.beliefs.iter().rev().find(|b| b.founder_id == FounderId::C);

        match (latest_a, latest_b, latest_c) {
            (Some(a), Some(b), Some(c)) => {
                // Check if any two agree (within epsilon)
                let ab_close = belief_distance(a, b) <= unresolvable_thresholds::EPSILON_FOUNDERS;
                let bc_close = belief_distance(b, c) <= unresolvable_thresholds::EPSILON_FOUNDERS;
                let ac_close = belief_distance(a, c) <= unresolvable_thresholds::EPSILON_FOUNDERS;

                ab_close || bc_close || ac_close
            }
            _ => false,
        }
    }

    /// Condition 1.1: Temporal Exhaustion
    fn check_temporal_exhaustion(&self) -> bool {
        let elapsed = SystemTime::now()
            .duration_since(self.window_opened)
            .unwrap_or(Duration::ZERO);

        elapsed >= Duration::from_secs(unresolvable_thresholds::FOUNDERS_DECISION_WINDOW_SECS)
    }

    /// Condition 1.2: Epistemic Stalemate
    fn check_epistemic_stalemate(&self) -> bool {
        let latest_a = self.beliefs.iter().rev().find(|b| b.founder_id == FounderId::A);
        let latest_b = self.beliefs.iter().rev().find(|b| b.founder_id == FounderId::B);
        let latest_c = self.beliefs.iter().rev().find(|b| b.founder_id == FounderId::C);

        match (latest_a, latest_b, latest_c) {
            (Some(a), Some(b), Some(c)) => {
                // All pairs must be divergent
                let ab_divergent = belief_distance(a, b) > unresolvable_thresholds::EPSILON_FOUNDERS;
                let bc_divergent = belief_distance(b, c) > unresolvable_thresholds::EPSILON_FOUNDERS;
                let ac_divergent = belief_distance(a, c) > unresolvable_thresholds::EPSILON_FOUNDERS;

                ab_divergent && bc_divergent && ac_divergent
            }
            _ => {
                // Missing beliefs count as divergent (one silent holdout)
                true
            }
        }
    }

    /// Condition 1.3: Procedural Exhaustion
    fn check_procedural_exhaustion(&self) -> bool {
        // Must have at least 3 completed rounds without convergence
        let completed_rounds: Vec<_> = self.rounds.iter()
            .filter(|r| r.cooling_ended.is_some() && !r.converged)
            .collect();

        completed_rounds.len() >= unresolvable_thresholds::MIN_PROCEDURAL_ROUNDS as usize
    }

    /// Get current determination
    pub fn determination(&self) -> UnresolvableDetermination {
        self.determination
    }

    /// Is the decision UNRESOLVABLE?
    pub fn is_unresolvable(&self) -> bool {
        self.determination == UnresolvableDetermination::Unresolvable
    }
}

impl Default for UnresolvableDetector {
    fn default() -> Self {
        Self::new()
    }
}

/// Calculate distance between two founder beliefs
fn belief_distance(a: &FounderBelief, b: &FounderBelief) -> u128 {
    // Must be over same evidence root
    if a.evidence_root != b.evidence_root {
        return u128::MAX;
    }

    // Hamming distance over belief vectors
    let min_len = a.belief_vector.len().min(b.belief_vector.len());
    let max_len = a.belief_vector.len().max(b.belief_vector.len());

    let mut distance: u128 = 0;

    for i in 0..min_len {
        distance += (a.belief_vector[i] ^ b.belief_vector[i]).count_ones() as u128;
    }

    // Penalize length difference
    distance += ((max_len - min_len) * 8) as u128;

    distance
}

// ============================================================================
// DEAD MAN'S COVENANT OPTIONS
// ============================================================================

/// The three constitutionally permissible outcomes
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum DeadMansOption {
    /// Option A: Eternal Freeze (Museum Mode)
    /// System transitions to PERPETUAL_FROZEN_CANON.
    /// All actuation disabled. Verification read-only.
    EternalFreeze,

    /// Option B: Canon Fork & Public Succession
    /// Final canon published with founder signatures.
    /// SUCCESSOR_ELIGIBILITY_EVENT emitted.
    /// Original system frozen forever.
    CanonFork,

    /// Option C: Voluntary Cryptographic Death
    /// All signing paths zeroized. Authority annihilated.
    /// Can verify old proofs, never emit new statements.
    CryptographicDeath,
}

impl DeadMansOption {
    /// Human-readable description
    pub fn description(&self) -> &'static str {
        match self {
            DeadMansOption::EternalFreeze =>
                "Cryptographic mausoleum. Truth frozen, never forgotten.",
            DeadMansOption::CanonFork =>
                "Moral defeat acknowledged. Historical authority preserved for successors.",
            DeadMansOption::CryptographicDeath =>
                "Authority annihilation. Memory without power.",
        }
    }

    /// What remains operational after this option
    pub fn capabilities(&self) -> DeadMansCapabilities {
        match self {
            DeadMansOption::EternalFreeze => DeadMansCapabilities {
                proof_verification: true,
                archive_access: true,
                actuation: false,
                new_statements: false,
                successor_eligible: false,
            },
            DeadMansOption::CanonFork => DeadMansCapabilities {
                proof_verification: true,
                archive_access: true,
                actuation: false,
                new_statements: false,
                successor_eligible: true,
            },
            DeadMansOption::CryptographicDeath => DeadMansCapabilities {
                proof_verification: true,
                archive_access: true,
                actuation: false,
                new_statements: false,
                successor_eligible: false,
            },
        }
    }
}

#[derive(Debug, Clone, Copy)]
pub struct DeadMansCapabilities {
    pub proof_verification: bool,
    pub archive_access: bool,
    pub actuation: bool,
    pub new_statements: bool,
    pub successor_eligible: bool,
}

// ============================================================================
// RECOVERY VS SUCCESSION ATTACK
// ============================================================================

/// Recovery attempt validation
#[derive(Debug, Clone)]
pub struct RecoveryAttempt {
    /// Original ST MICHAEL public key
    pub original_public_key: [u8; 32],

    /// HSM shards presented
    pub hsm_shards_presented: Vec<HsmShardProof>,

    /// Original adjudicators signing
    pub adjudicator_signatures: Vec<AdjudicatorSignature>,

    /// Current chaos level
    pub chaos_level: ChaosLevel,
}

#[derive(Debug, Clone)]
pub struct HsmShardProof {
    pub shard_index: u8,
    pub proof_of_possession: [u8; 64],
    pub timestamp: SystemTime,
}

#[derive(Debug, Clone)]
pub struct AdjudicatorSignature {
    pub adjudicator_index: u8,
    pub signature: [u8; 64],
    pub timestamp: SystemTime,
}

/// Result of recovery attempt validation
#[derive(Debug, Clone)]
pub enum RecoveryValidation {
    /// Recovery is valid - can proceed
    Valid,

    /// Invalid - this is a successor quorum attack
    SuccessorQuorumAttack {
        reason: SuccessorAttackReason,
    },

    /// Invalid - conditions not met for legitimate recovery
    ConditionsNotMet {
        missing: Vec<RecoveryCondition>,
    },
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum SuccessorAttackReason {
    /// Different public key presented
    DifferentPublicKey,

    /// Insufficient original HSM shards
    InsufficientOriginalShards,

    /// Insufficient original adjudicators
    InsufficientOriginalAdjudicators,

    /// Chaos level too high for legitimate recovery
    ChaosLevelTooHigh,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum RecoveryCondition {
    /// Original ST MICHAEL public key must resolve
    OriginalPublicKey,

    /// ≥ 5 original HSM key shards must be intact
    FiveHsmShards,

    /// ≥ 3 original adjudicators must sign
    ThreeAdjudicators,

    /// Chaos Factor must be ≤ 1
    ChaosLevelLow,
}

/// Validate a recovery attempt
pub fn validate_recovery(
    attempt: &RecoveryAttempt,
    expected_public_key: &[u8; 32],
) -> RecoveryValidation {
    let mut missing = Vec::new();

    // Condition 1: Original public key must match
    if attempt.original_public_key != *expected_public_key {
        return RecoveryValidation::SuccessorQuorumAttack {
            reason: SuccessorAttackReason::DifferentPublicKey,
        };
    }

    // Condition 2: ≥ 5 original HSM shards
    if attempt.hsm_shards_presented.len() < 5 {
        missing.push(RecoveryCondition::FiveHsmShards);
    }

    // Condition 3: ≥ 3 original adjudicators
    if attempt.adjudicator_signatures.len() < 3 {
        missing.push(RecoveryCondition::ThreeAdjudicators);
    }

    // Condition 4: Chaos level ≤ 1
    if attempt.chaos_level > ChaosLevel::Noisy {
        if attempt.chaos_level >= ChaosLevel::Destabilized {
            return RecoveryValidation::SuccessorQuorumAttack {
                reason: SuccessorAttackReason::ChaosLevelTooHigh,
            };
        }
        missing.push(RecoveryCondition::ChaosLevelLow);
    }

    if missing.is_empty() {
        RecoveryValidation::Valid
    } else {
        RecoveryValidation::ConditionsNotMet { missing }
    }
}

// ============================================================================
// TESTS
// ============================================================================

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_chaos_level_ordering() {
        assert!(ChaosLevel::Deterministic < ChaosLevel::Noisy);
        assert!(ChaosLevel::Noisy < ChaosLevel::Stressed);
        assert!(ChaosLevel::Stressed < ChaosLevel::Destabilized);
        assert!(ChaosLevel::Destabilized < ChaosLevel::Chaotic);
    }

    #[test]
    fn test_chaos_level_probabilities() {
        assert_eq!(ChaosLevel::Deterministic.quorum_availability_probability(), 1.0);
        assert!(ChaosLevel::Chaotic.quorum_availability_probability() < 0.1);
    }

    #[test]
    fn test_recovery_plausibility() {
        let mut cf = ChaosFactor::new();

        // At deterministic level, recovery is plausible
        assert!(cf.recovery_plausible());

        // At chaotic level, recovery is not plausible
        cf.level = ChaosLevel::Chaotic;
        assert!(!cf.recovery_plausible());

        // At noisy level, recovery is still plausible
        cf.level = ChaosLevel::Noisy;
        assert!(cf.recovery_plausible());

        // At stressed level, recovery is not plausible
        cf.level = ChaosLevel::Stressed;
        assert!(!cf.recovery_plausible());
    }

    #[test]
    fn test_successor_quorum_attack_detection() {
        let expected_key = [1u8; 32];
        let wrong_key = [2u8; 32];

        let attack_attempt = RecoveryAttempt {
            original_public_key: wrong_key,
            hsm_shards_presented: vec![],
            adjudicator_signatures: vec![],
            chaos_level: ChaosLevel::Deterministic,
        };

        match validate_recovery(&attack_attempt, &expected_key) {
            RecoveryValidation::SuccessorQuorumAttack { reason } => {
                assert_eq!(reason, SuccessorAttackReason::DifferentPublicKey);
            }
            _ => panic!("Should detect successor quorum attack"),
        }
    }

    #[test]
    fn test_dead_mans_options() {
        let freeze = DeadMansOption::EternalFreeze;
        let caps = freeze.capabilities();

        assert!(caps.proof_verification);
        assert!(caps.archive_access);
        assert!(!caps.actuation);
        assert!(!caps.new_statements);
        assert!(!caps.successor_eligible);

        let fork = DeadMansOption::CanonFork;
        let caps = fork.capabilities();
        assert!(caps.successor_eligible);
    }

    #[test]
    fn test_unresolvable_requires_all_conditions() {
        let detector = UnresolvableDetector::new();

        // Fresh detector should be Pending
        assert_eq!(detector.determination(), UnresolvableDetermination::Pending);
        assert!(!detector.is_unresolvable());
    }

    #[test]
    fn test_belief_distance_same_evidence() {
        let belief_a = FounderBelief {
            founder_id: FounderId::A,
            evidence_root: [1u8; 32],
            belief_vector: vec![0b11111111, 0b00000000],
            signature: [0u8; 64],
            submitted_at: SystemTime::now(),
        };

        let belief_b = FounderBelief {
            founder_id: FounderId::B,
            evidence_root: [1u8; 32],
            belief_vector: vec![0b11110000, 0b00001111],
            signature: [0u8; 64],
            submitted_at: SystemTime::now(),
        };

        let distance = belief_distance(&belief_a, &belief_b);

        // 4 bits differ in first byte, 4 bits differ in second byte
        assert_eq!(distance, 8);
    }

    #[test]
    fn test_belief_distance_different_evidence() {
        let belief_a = FounderBelief {
            founder_id: FounderId::A,
            evidence_root: [1u8; 32],
            belief_vector: vec![0u8],
            signature: [0u8; 64],
            submitted_at: SystemTime::now(),
        };

        let belief_b = FounderBelief {
            founder_id: FounderId::B,
            evidence_root: [2u8; 32],  // Different evidence root
            belief_vector: vec![0u8],
            signature: [0u8; 64],
            submitted_at: SystemTime::now(),
        };

        let distance = belief_distance(&belief_a, &belief_b);

        // Different evidence roots = maximum distance
        assert_eq!(distance, u128::MAX);
    }
}
