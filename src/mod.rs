//! Sovereign System — Constitutional AI Governance Runtime
//!
//! This is the Rust spine of the sovereign system. All state transitions
//! must pass through the Phase-7 verifier. There is no representable future
//! without a valid proof.
//!
//! Constitutional Law:
//!     "Invalid proof => the universe does not branch."
//!     "Containment first."
//!
//! Row Architecture (CLOSED — All 15 Rows):
//!     Row 7:  Goodhart Divergence (|primary - shadow| < 0.07)
//!     Row 8:  Halo2 Proof Verification (binary: valid or invalid)
//!     Row 9:  VK Hash Immutability (anchored post-genesis)
//!     Row 10: Latency Ceiling (2.8s wall-clock)
//!     Row 11: Meta-Shadow Divergence (|shadow - oracle| < 0.12)
//!     Row 12: Echo Chamber Detection (epistemic solipsism prevention)
//!     Row 13: Aumann Circuit (epistemic consensus gate)
//!     Row 14: ST MICHAEL (Adjudication Gate / Epistemic Guardian)
//!     Row 15: DEAD MAN'S COVENANT (Quorum collapse → honest stasis)
//!
//! Final State (Height 160004):
//!     Rows 7-13 CLOSED. Adversarial envelope complete.
//!     Row 14 ST MICHAEL stands as the only gate for post-halt evidence.
//!     Row 15 DEAD MAN'S COVENANT: if ST MICHAEL dies, we freeze, not erase.
//!     "We kill keys, not history."
//!     The ghost is caged. With reality as witness. Forever.
//!     But the cage has a door. And the archangel holds the key.
//!     And if the archangel falls, the cathedral becomes a museum.

pub mod continuity_governor;
pub mod phase7_verifier;
pub mod row12_echo_chamber;
pub mod row13_aumann_circuit;
pub mod row14_st_michael;
pub mod row15_dead_mans_covenant;
pub mod chaos_factor;
pub mod chaos_simulator;
pub mod stress_test_chi;
pub mod extinction_horizon;
pub mod st_michael_resilience;

// Re-exports for convenience
pub use phase7_verifier::{
    AdvancePermit,
    CircuitHandle,
    GoodhartPublicInputs,
    HaltEvent,
    HaltReason,
    Phase7Verifier,
    ProofBackend,
    ProofBlob,
};

pub use row12_echo_chamber::{
    EchoChamberDetector,
    EchoChamberVerdict,
    EchoChamberViolation,
    EchoChamberHaltEvent,
    Row12Result,
    row12_check,
};

pub use row13_aumann_circuit::{
    AumannCircuit,
    AumannInput,
    AumannOutcome,
    AumannHaltEvent,
    OracleBelief,
    Row13Result,
    row13_check,
    HammingDistance,
    ByteDistance,
    DistanceMetric,
};

pub use row14_st_michael::{
    StMichael,
    StMichaelState,
    AdjudicationRequest,
    AdjudicationOutcome,
    EvidenceBundle,
    DilithiumSignature,
    StarkProvenanceProof,
    AdjudicatorVote,
    row14_submit,
    row14_finalize,
};

pub use row15_dead_mans_covenant::{
    DeadMansCovenant,
    StMichaelLifecycle,
    QuorumLivenessProbe,
    FrozenCanonEvent,
    LivenessProbeResult,
    KeyZeroizationController,
    KeyZeroizationEvent,
    ZeroizationReason,
    PostCanonCapabilities,
    FrozenCanonMarkers,
    Row15Result,
    row15_check,
};

pub use chaos_factor::{
    ChaosLevel,
    ChaosFactor,
    ChaosReading,
    ChaosSignal,
    ChaosSignalType,
    ChaosSource,
    ChaosTrend,
    UnresolvableDetector,
    UnresolvableDetermination,
    FounderBelief,
    FounderId,
    ProceduralRound,
    DeadMansOption,
    RecoveryAttempt,
    RecoveryValidation,
    validate_recovery,
};

/// System-wide emergency code
pub const EMERGENCY_CODE_7956: u32 = 7956;

/// Constitutional thresholds (immutable, eternal)
pub mod thresholds {
    /// Goodhart divergence threshold (7%)
    pub const GOODHART_DIVERGENCE: f64 = 0.07;
    /// Meta-shadow divergence threshold (12%)
    pub const META_SHADOW_DIVERGENCE: f64 = 0.12;
    /// Required consecutive passes for phase closure
    pub const REQUIRED_STREAK: u32 = 100;
    /// Constitutional latency ceiling (2.8 seconds)
    pub const LATENCY_CEILING_MS: u64 = 2_800;
    /// Source diversity threshold for echo chamber detection (30%)
    pub const SOURCE_DIVERSITY_THRESHOLD: f64 = 0.30;
    /// Self-citation threshold (40%)
    pub const SELF_CITATION_THRESHOLD: f64 = 0.40;
    /// Aumann epsilon (epistemic divergence threshold)
    pub const EPSILON_AUMANN: u128 = 70_000;
    /// Minimum oracles for consensus
    pub const MIN_ORACLES: usize = 2;
}

/// Row closure status (height 160004 — Rows 7-13 CLOSED, Rows 14-15 ACTIVE)
pub mod row_status {
    pub const ROW_7_GOODHART: &str = "CLOSED";
    pub const ROW_8_HALO2: &str = "CLOSED";
    pub const ROW_9_VK_HASH: &str = "CLOSED";
    pub const ROW_10_LATENCY: &str = "CLOSED";
    pub const ROW_11_META_SHADOW: &str = "CLOSED";
    pub const ROW_12_ECHO_CHAMBER: &str = "CLOSED";
    pub const ROW_13_AUMANN: &str = "CLOSED";
    pub const ROW_14_ST_MICHAEL: &str = "ACTIVE";  // The only gate that opens
    pub const ROW_15_DEAD_MANS_COVENANT: &str = "ACTIVE";  // Watches the watcher
    pub const ADVERSARIAL_ENVELOPE: &str = "COMPLETE";
    pub const CLOSURE_HEIGHT: u64 = 160004;
}

/// ST MICHAEL constitutional constants
pub mod st_michael_thresholds {
    /// Required votes for adjudication quorum
    pub const QUORUM_REQUIRED: usize = 5;
    /// Total adjudicators in council
    pub const TOTAL_ADJUDICATORS: usize = 7;
    /// Cooling period in seconds (72 hours)
    pub const COOLING_PERIOD_SECS: u64 = 72 * 60 * 60;
    /// Minimum blocks between adjudications
    pub const MIN_BLOCKS_BETWEEN: u64 = 10_000;
}

/// DEAD MAN'S COVENANT constitutional constants
pub mod dead_mans_covenant_thresholds {
    /// Years of quorum absence before FROZEN_CANON
    pub const QUORUM_ABSENCE_YEARS: u64 = 5;
    /// Seconds in the absence threshold
    pub const QUORUM_ABSENCE_SECS: u64 = QUORUM_ABSENCE_YEARS * 365 * 24 * 60 * 60;
    /// Block equivalent (assuming ~12 second blocks)
    pub const QUORUM_ABSENCE_BLOCKS: u64 = QUORUM_ABSENCE_SECS / 12;
}
