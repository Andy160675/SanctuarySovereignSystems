//! ROW 15: DEAD MAN'S COVENANT
//!
//! The final fail-safe: what happens when ST MICHAEL itself becomes unreachable.
//!
//! Philosophy:
//!     "In the face of governance collapse, prefer honest stasis over fake adaptability."
//!     "We kill keys, not history."
//!
//! This row does NOT self-destruct. It does NOT erase canon.
//! It freezes the last valid truth and refuses to pretend it can still evolve.
//!
//! The system becomes a museum of frozen certainty with live math around it.

use std::time::{Duration, SystemTime};

// ============================================================================
// CONSTITUTIONAL CONSTANTS
// ============================================================================

/// Years of quorum absence before triggering FROZEN_CANON
pub const QUORUM_ABSENCE_THRESHOLD_YEARS: u64 = 5;

/// Seconds in the absence threshold (5 years)
pub const QUORUM_ABSENCE_THRESHOLD_SECS: u64 = QUORUM_ABSENCE_THRESHOLD_YEARS * 365 * 24 * 60 * 60;

/// Block height equivalent (assuming ~12 second blocks)
pub const QUORUM_ABSENCE_THRESHOLD_BLOCKS: u64 = QUORUM_ABSENCE_THRESHOLD_SECS / 12;

// ============================================================================
// STATE MACHINE
// ============================================================================

/// The two states of ST MICHAEL's existence
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum StMichaelLifecycle {
    /// Quorum healthy, can accept new canon
    Live,

    /// Quorum unreachable, last canon_root is final
    /// The doors close forever. The cathedral becomes a museum.
    FrozenCanon,
}

/// Evidence of quorum liveness (or lack thereof)
#[derive(Debug, Clone)]
pub struct QuorumLivenessProbe {
    /// Last successful quorum attestation timestamp
    pub last_attestation: SystemTime,

    /// Last successful quorum attestation block height
    pub last_attestation_height: u64,

    /// Number of consecutive failed liveness checks
    pub consecutive_failures: u64,

    /// Current probe timestamp
    pub probe_time: SystemTime,

    /// Current block height
    pub probe_height: u64,
}

impl QuorumLivenessProbe {
    /// Calculate time since last successful attestation
    pub fn time_since_attestation(&self) -> Duration {
        self.probe_time
            .duration_since(self.last_attestation)
            .unwrap_or(Duration::ZERO)
    }

    /// Calculate blocks since last successful attestation
    pub fn blocks_since_attestation(&self) -> u64 {
        self.probe_height.saturating_sub(self.last_attestation_height)
    }

    /// Check if quorum absence threshold has been exceeded
    pub fn threshold_exceeded(&self) -> bool {
        let time_exceeded = self.time_since_attestation()
            >= Duration::from_secs(QUORUM_ABSENCE_THRESHOLD_SECS);
        let blocks_exceeded = self.blocks_since_attestation()
            >= QUORUM_ABSENCE_THRESHOLD_BLOCKS;

        // Both conditions must be met (defense in depth)
        time_exceeded && blocks_exceeded
    }
}

/// The transition event from Live to FrozenCanon
#[derive(Debug, Clone)]
pub struct FrozenCanonEvent {
    /// Block height at which freeze occurred
    pub freeze_height: u64,

    /// Timestamp of freeze
    pub freeze_time: SystemTime,

    /// The last valid canon root (becomes permanent physics)
    pub final_canon_root: [u8; 32],

    /// The last valid evidence root
    pub final_evidence_root: [u8; 32],

    /// Hash of the liveness probe that triggered the freeze
    pub trigger_probe_hash: [u8; 32],

    /// Human-readable declaration
    pub declaration: &'static str,
}

impl FrozenCanonEvent {
    pub const DECLARATION: &'static str =
        "We no longer have the legitimate human key to change truth. So we won't.";
}

// ============================================================================
// DEAD MAN'S COVENANT CONTROLLER
// ============================================================================

/// The controller that monitors quorum liveness and triggers FROZEN_CANON
pub struct DeadMansCovenant {
    /// Current lifecycle state
    pub state: StMichaelLifecycle,

    /// Last known good canon root
    pub last_canon_root: [u8; 32],

    /// Last known good evidence root
    pub last_evidence_root: [u8; 32],

    /// Last successful attestation height
    pub last_attestation_height: u64,

    /// Last successful attestation time
    pub last_attestation_time: SystemTime,

    /// Frozen canon event (if triggered)
    pub frozen_event: Option<FrozenCanonEvent>,
}

impl DeadMansCovenant {
    /// Create a new covenant in Live state
    pub fn new(
        initial_canon_root: [u8; 32],
        initial_evidence_root: [u8; 32],
        genesis_height: u64,
    ) -> Self {
        Self {
            state: StMichaelLifecycle::Live,
            last_canon_root: initial_canon_root,
            last_evidence_root: initial_evidence_root,
            last_attestation_height: genesis_height,
            last_attestation_time: SystemTime::now(),
            frozen_event: None,
        }
    }

    /// Record a successful ST MICHAEL attestation (keeps the covenant alive)
    pub fn record_attestation(
        &mut self,
        canon_root: [u8; 32],
        evidence_root: [u8; 32],
        height: u64,
    ) -> Result<(), CovenantError> {
        match self.state {
            StMichaelLifecycle::Live => {
                self.last_canon_root = canon_root;
                self.last_evidence_root = evidence_root;
                self.last_attestation_height = height;
                self.last_attestation_time = SystemTime::now();
                Ok(())
            }
            StMichaelLifecycle::FrozenCanon => {
                Err(CovenantError::CanonFrozen {
                    frozen_at: self.frozen_event.as_ref()
                        .map(|e| e.freeze_height)
                        .unwrap_or(0),
                })
            }
        }
    }

    /// Probe quorum liveness and potentially trigger FROZEN_CANON
    pub fn probe_liveness(
        &mut self,
        current_height: u64,
    ) -> LivenessProbeResult {
        // Already frozen - nothing to do
        if self.state == StMichaelLifecycle::FrozenCanon {
            return LivenessProbeResult::AlreadyFrozen;
        }

        let probe = QuorumLivenessProbe {
            last_attestation: self.last_attestation_time,
            last_attestation_height: self.last_attestation_height,
            consecutive_failures: 0, // Updated by external monitoring
            probe_time: SystemTime::now(),
            probe_height: current_height,
        };

        if probe.threshold_exceeded() {
            // TRIGGER FROZEN_CANON
            let event = FrozenCanonEvent {
                freeze_height: current_height,
                freeze_time: SystemTime::now(),
                final_canon_root: self.last_canon_root,
                final_evidence_root: self.last_evidence_root,
                trigger_probe_hash: compute_probe_hash(&probe),
                declaration: FrozenCanonEvent::DECLARATION,
            };

            self.state = StMichaelLifecycle::FrozenCanon;
            self.frozen_event = Some(event.clone());

            LivenessProbeResult::FrozenCanonTriggered(event)
        } else {
            LivenessProbeResult::StillLive {
                time_remaining: Duration::from_secs(QUORUM_ABSENCE_THRESHOLD_SECS)
                    .saturating_sub(probe.time_since_attestation()),
                blocks_remaining: QUORUM_ABSENCE_THRESHOLD_BLOCKS
                    .saturating_sub(probe.blocks_since_attestation()),
            }
        }
    }

    /// Check if any new canon can be accepted
    pub fn can_accept_new_canon(&self) -> bool {
        self.state == StMichaelLifecycle::Live
    }

    /// Get the permanent canon root (only valid in FrozenCanon state)
    pub fn permanent_canon_root(&self) -> Option<[u8; 32]> {
        match self.state {
            StMichaelLifecycle::FrozenCanon => Some(self.last_canon_root),
            StMichaelLifecycle::Live => None,
        }
    }
}

// ============================================================================
// RESULT TYPES
// ============================================================================

#[derive(Debug, Clone)]
pub enum LivenessProbeResult {
    /// Quorum is still reachable (within threshold)
    StillLive {
        time_remaining: Duration,
        blocks_remaining: u64,
    },

    /// FROZEN_CANON has just been triggered
    FrozenCanonTriggered(FrozenCanonEvent),

    /// Already in FROZEN_CANON state
    AlreadyFrozen,
}

#[derive(Debug, Clone)]
pub enum CovenantError {
    /// Cannot accept new canon - system is frozen
    CanonFrozen { frozen_at: u64 },
}

// ============================================================================
// KEY ZEROIZATION (LOCAL, NOT GLOBAL)
// ============================================================================

/// Key zeroization policy: we kill keys, not history
///
/// This is triggered at the HSM level upon:
/// - Physical tamper detection
/// - Compromise signal from external monitoring
/// - Manual operator invocation under duress
///
/// What it does:
/// - Zeros the Dilithium-5 private key material
/// - Bricks the ST MICHAEL signing path
/// - Leaves canon_root and evidence_root INTACT
///
/// What it does NOT do:
/// - Erase the global canon
/// - Delete historical evidence
/// - Destroy the proof archive
#[derive(Debug, Clone)]
pub struct KeyZeroizationEvent {
    /// Height at which zeroization occurred
    pub height: u64,

    /// Reason for zeroization
    pub reason: ZeroizationReason,

    /// Which HSM was zeroized (index 0-6)
    pub hsm_index: u8,

    /// Confirmation hash (proves the key was held, now gone)
    pub zeroization_proof: [u8; 32],

    /// The canon root remains readable
    pub preserved_canon_root: [u8; 32],
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ZeroizationReason {
    /// Physical tamper detected by HSM
    TamperDetected,

    /// External compromise signal received
    CompromiseSignal,

    /// Operator duress code entered
    DuressCode,

    /// Scheduled key rotation (old key zeroed after new key active)
    ScheduledRotation,

    /// FROZEN_CANON triggered - all keys zeroed as ceremony
    FrozenCanonCeremony,
}

/// The zeroization controller
pub struct KeyZeroizationController {
    /// Keys that have been zeroized
    pub zeroized_hsms: [bool; 7],

    /// Zeroization events (audit trail)
    pub events: Vec<KeyZeroizationEvent>,
}

impl KeyZeroizationController {
    pub fn new() -> Self {
        Self {
            zeroized_hsms: [false; 7],
            events: Vec::new(),
        }
    }

    /// Zeroize a specific HSM's key material
    pub fn zeroize_hsm(
        &mut self,
        hsm_index: u8,
        reason: ZeroizationReason,
        height: u64,
        preserved_canon_root: [u8; 32],
    ) -> Result<KeyZeroizationEvent, ZeroizationError> {
        if hsm_index >= 7 {
            return Err(ZeroizationError::InvalidHsmIndex(hsm_index));
        }

        if self.zeroized_hsms[hsm_index as usize] {
            return Err(ZeroizationError::AlreadyZeroized(hsm_index));
        }

        // Mark as zeroized
        self.zeroized_hsms[hsm_index as usize] = true;

        // Create event
        let event = KeyZeroizationEvent {
            height,
            reason,
            hsm_index,
            zeroization_proof: compute_zeroization_proof(hsm_index, height),
            preserved_canon_root,
        };

        self.events.push(event.clone());

        Ok(event)
    }

    /// Check how many HSMs are still active
    pub fn active_hsm_count(&self) -> usize {
        self.zeroized_hsms.iter().filter(|&&z| !z).count()
    }

    /// Check if quorum is still possible
    pub fn quorum_possible(&self) -> bool {
        self.active_hsm_count() >= 5
    }

    /// Zeroize all HSMs as part of FROZEN_CANON ceremony
    pub fn frozen_canon_ceremony(
        &mut self,
        height: u64,
        final_canon_root: [u8; 32],
    ) -> Vec<KeyZeroizationEvent> {
        let mut events = Vec::new();

        for i in 0..7 {
            if !self.zeroized_hsms[i] {
                if let Ok(event) = self.zeroize_hsm(
                    i as u8,
                    ZeroizationReason::FrozenCanonCeremony,
                    height,
                    final_canon_root,
                ) {
                    events.push(event);
                }
            }
        }

        events
    }
}

impl Default for KeyZeroizationController {
    fn default() -> Self {
        Self::new()
    }
}

#[derive(Debug, Clone)]
pub enum ZeroizationError {
    InvalidHsmIndex(u8),
    AlreadyZeroized(u8),
}

// ============================================================================
// POST-CANON BEHAVIOR
// ============================================================================

/// What the system can still do after FROZEN_CANON
#[derive(Debug, Clone, Copy)]
pub struct PostCanonCapabilities {
    /// Can still verify proofs against frozen canon
    pub proof_verification: bool,

    /// Can still enforce containment (Rows 7-13)
    pub containment_enforcement: bool,

    /// Can still reject invalid state transitions
    pub transition_rejection: bool,

    /// Can still serve as read-only archive
    pub archive_access: bool,

    /// CANNOT accept new evidence
    pub new_evidence: bool,

    /// CANNOT change thresholds
    pub threshold_modification: bool,

    /// CANNOT mint new rows
    pub new_rows: bool,

    /// CANNOT update Omega register
    pub omega_updates: bool,
}

impl PostCanonCapabilities {
    /// The capabilities available after FROZEN_CANON
    pub const FROZEN: Self = Self {
        proof_verification: true,
        containment_enforcement: true,
        transition_rejection: true,
        archive_access: true,
        new_evidence: false,
        threshold_modification: false,
        new_rows: false,
        omega_updates: false,
    };
}

// ============================================================================
// DASHBOARD MARKERS
// ============================================================================

/// Visual/log markers for FROZEN_CANON state
pub struct FrozenCanonMarkers;

impl FrozenCanonMarkers {
    /// Banner text for dashboards
    pub const BANNER: &'static str =
        "⚠️ FROZEN CANON ⚠️ - Quorum unreachable - Last valid canon is now permanent physics";

    /// Log prefix for all post-canon activity
    pub const LOG_PREFIX: &'static str = "[POST-CANON]";

    /// Color code (for UI)
    pub const COLOR: &'static str = "#FF6B6B";  // Coral red

    /// Severity level
    pub const SEVERITY: &'static str = "CRITICAL";
}

// ============================================================================
// HELPER FUNCTIONS
// ============================================================================

fn compute_probe_hash(probe: &QuorumLivenessProbe) -> [u8; 32] {
    use std::collections::hash_map::DefaultHasher;
    use std::hash::{Hash, Hasher};

    let mut hasher = DefaultHasher::new();
    probe.last_attestation_height.hash(&mut hasher);
    probe.probe_height.hash(&mut hasher);
    probe.consecutive_failures.hash(&mut hasher);

    let hash = hasher.finish();
    let mut result = [0u8; 32];
    result[..8].copy_from_slice(&hash.to_le_bytes());
    result
}

fn compute_zeroization_proof(hsm_index: u8, height: u64) -> [u8; 32] {
    use std::collections::hash_map::DefaultHasher;
    use std::hash::{Hash, Hasher};

    let mut hasher = DefaultHasher::new();
    hsm_index.hash(&mut hasher);
    height.hash(&mut hasher);
    "ZEROIZED".hash(&mut hasher);

    let hash = hasher.finish();
    let mut result = [0u8; 32];
    result[..8].copy_from_slice(&hash.to_le_bytes());
    result
}

// ============================================================================
// ROW 15 INTEGRATION
// ============================================================================

/// Result type for Row 15 checks
pub type Row15Result = Result<Row15Pass, Row15Halt>;

#[derive(Debug, Clone)]
pub struct Row15Pass {
    pub state: StMichaelLifecycle,
    pub time_to_freeze: Option<Duration>,
}

#[derive(Debug, Clone)]
pub struct Row15Halt {
    pub reason: Row15HaltReason,
    pub frozen_event: Option<FrozenCanonEvent>,
}

#[derive(Debug, Clone)]
pub enum Row15HaltReason {
    /// Attempted canon update in FROZEN_CANON state
    CanonUpdateRejected,

    /// Quorum has just become unreachable
    QuorumCollapsed,
}

/// Primary Row 15 check function
pub fn row15_check(
    covenant: &mut DeadMansCovenant,
    current_height: u64,
    attempting_canon_update: bool,
) -> Row15Result {
    // First, probe liveness
    let probe_result = covenant.probe_liveness(current_height);

    match probe_result {
        LivenessProbeResult::StillLive { time_remaining, .. } => {
            if attempting_canon_update {
                // Still live, canon updates allowed
                Ok(Row15Pass {
                    state: StMichaelLifecycle::Live,
                    time_to_freeze: Some(time_remaining),
                })
            } else {
                Ok(Row15Pass {
                    state: StMichaelLifecycle::Live,
                    time_to_freeze: Some(time_remaining),
                })
            }
        }

        LivenessProbeResult::FrozenCanonTriggered(event) => {
            // Just transitioned to FROZEN_CANON
            Err(Row15Halt {
                reason: Row15HaltReason::QuorumCollapsed,
                frozen_event: Some(event),
            })
        }

        LivenessProbeResult::AlreadyFrozen => {
            if attempting_canon_update {
                // Reject canon update attempts in frozen state
                Err(Row15Halt {
                    reason: Row15HaltReason::CanonUpdateRejected,
                    frozen_event: covenant.frozen_event.clone(),
                })
            } else {
                // Other operations still allowed per PostCanonCapabilities
                Ok(Row15Pass {
                    state: StMichaelLifecycle::FrozenCanon,
                    time_to_freeze: None,
                })
            }
        }
    }
}

// ============================================================================
// TESTS
// ============================================================================

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_covenant_starts_live() {
        let covenant = DeadMansCovenant::new(
            [0u8; 32],
            [0u8; 32],
            0,
        );

        assert_eq!(covenant.state, StMichaelLifecycle::Live);
        assert!(covenant.can_accept_new_canon());
        assert!(covenant.permanent_canon_root().is_none());
    }

    #[test]
    fn test_attestation_keeps_covenant_alive() {
        let mut covenant = DeadMansCovenant::new(
            [0u8; 32],
            [0u8; 32],
            0,
        );

        let new_canon = [1u8; 32];
        let new_evidence = [2u8; 32];

        assert!(covenant.record_attestation(new_canon, new_evidence, 100).is_ok());
        assert_eq!(covenant.last_canon_root, new_canon);
        assert_eq!(covenant.last_evidence_root, new_evidence);
    }

    #[test]
    fn test_zeroization_controller() {
        let mut controller = KeyZeroizationController::new();

        assert_eq!(controller.active_hsm_count(), 7);
        assert!(controller.quorum_possible());

        // Zeroize 2 HSMs
        controller.zeroize_hsm(0, ZeroizationReason::TamperDetected, 100, [0u8; 32]).unwrap();
        controller.zeroize_hsm(1, ZeroizationReason::CompromiseSignal, 101, [0u8; 32]).unwrap();

        assert_eq!(controller.active_hsm_count(), 5);
        assert!(controller.quorum_possible());

        // Zeroize one more - quorum still possible
        controller.zeroize_hsm(2, ZeroizationReason::DuressCode, 102, [0u8; 32]).unwrap();

        assert_eq!(controller.active_hsm_count(), 4);
        assert!(!controller.quorum_possible());
    }

    #[test]
    fn test_cannot_zeroize_twice() {
        let mut controller = KeyZeroizationController::new();

        controller.zeroize_hsm(0, ZeroizationReason::TamperDetected, 100, [0u8; 32]).unwrap();

        let result = controller.zeroize_hsm(0, ZeroizationReason::TamperDetected, 101, [0u8; 32]);
        assert!(matches!(result, Err(ZeroizationError::AlreadyZeroized(0))));
    }

    #[test]
    fn test_post_canon_capabilities() {
        let caps = PostCanonCapabilities::FROZEN;

        // What we CAN do
        assert!(caps.proof_verification);
        assert!(caps.containment_enforcement);
        assert!(caps.transition_rejection);
        assert!(caps.archive_access);

        // What we CANNOT do
        assert!(!caps.new_evidence);
        assert!(!caps.threshold_modification);
        assert!(!caps.new_rows);
        assert!(!caps.omega_updates);
    }

    #[test]
    fn test_frozen_canon_ceremony_zeroizes_all() {
        let mut controller = KeyZeroizationController::new();

        let events = controller.frozen_canon_ceremony(1000, [42u8; 32]);

        assert_eq!(events.len(), 7);
        assert_eq!(controller.active_hsm_count(), 0);

        for event in &events {
            assert_eq!(event.reason, ZeroizationReason::FrozenCanonCeremony);
            assert_eq!(event.preserved_canon_root, [42u8; 32]);
        }
    }
}
