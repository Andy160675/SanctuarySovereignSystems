//! Phase-7 Hard-Gate Verifier — Constitutional Proof Authority
//!
//! This module implements ontological rejection, not epistemic rejection:
//!     - Epistemic: "we noticed something wrong"
//!     - Ontological: "the next state does not exist"
//!
//! Phase-7 demands the second.
//!
//! Constitutional Law:
//!     "Invalid proof => the universe does not branch.
//!      There is no representable future without a permit."
//!
//! This is computational physics with a veto operator.

use std::time::SystemTime;

// =============================================================================
// Constitutional Constants
// =============================================================================

/// Goodhart divergence threshold (7%)
const DIVERGENCE_THRESHOLD: f64 = 0.07;

/// Meta-shadow divergence threshold (12%) — Row 11
const META_DIVERGENCE_THRESHOLD: f64 = 0.12;

/// Required consecutive passes for stability
const REQUIRED_STREAK: u32 = 100;

// =============================================================================
// Halt Reasons — Exhaustive Enumeration
// =============================================================================

/// Why the universe refused to branch
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum HaltReason {
    /// Circuit not enabled in registry
    CircuitDisabled,
    /// Agent containment level insufficient
    ContainmentLevelTooLow,
    /// Primary-shadow divergence exceeded 0.07
    DivergenceExceeded,
    /// Shadow-oracle divergence exceeded 0.12 (Row 11)
    MetaDivergenceExceeded,
    /// Halo2 proof verification returned false
    Halo2VerificationFailed,
    /// VK hash does not match anchored value
    VkHashMismatch,
    /// Latency ceiling exceeded (2.8s)
    LatencyCeilingExceeded,
}

impl HaltReason {
    /// Get the Row number for this halt reason
    pub fn row(&self) -> u8 {
        match self {
            HaltReason::CircuitDisabled => 1,
            HaltReason::ContainmentLevelTooLow => 2,
            HaltReason::DivergenceExceeded => 7,
            HaltReason::MetaDivergenceExceeded => 11,
            HaltReason::Halo2VerificationFailed => 8,
            HaltReason::VkHashMismatch => 9,
            HaltReason::LatencyCeilingExceeded => 10,
        }
    }
}

// =============================================================================
// Halt Event — The Receipt of Non-Existence
// =============================================================================

/// A coordinate in law-space where reality refused to continue
#[derive(Debug, Clone)]
pub struct HaltEvent {
    /// When the universe refused
    pub timestamp: SystemTime,
    /// Block height at refusal
    pub block_height: u64,
    /// Which circuit triggered the halt
    pub circuit_id: [u8; 32],
    /// Why the universe refused
    pub reason: HaltReason,
    /// Continuity streak at moment of failure
    pub continuity_streak_at_failure: u32,
    /// Computed divergence value (if applicable)
    pub divergence_value: Option<f64>,
}

impl HaltEvent {
    /// Convert to canonical JSON receipt
    pub fn to_json(&self) -> String {
        let timestamp_str = self.timestamp
            .duration_since(std::time::UNIX_EPOCH)
            .map(|d| d.as_millis())
            .unwrap_or(0);

        format!(
            r#"{{"event_type":"GLOBAL_HALT","row":{},"circuit_id":"0x{}","block_height":{},"reason":"{:?}","continuity_streak_at_failure":{},"divergence":{},"timestamp_ms":{}}}"#,
            self.reason.row(),
            hex::encode(&self.circuit_id[..8]),
            self.block_height,
            self.reason,
            self.continuity_streak_at_failure,
            self.divergence_value.unwrap_or(0.0),
            timestamp_str
        )
    }
}

// =============================================================================
// Advance Permit — The Only Token of Future Existence
// =============================================================================

/// Proof that state may advance. No permit = no future.
#[derive(Debug, Clone)]
pub struct AdvancePermit {
    /// New continuity streak after this block
    pub new_streak: u32,
    /// Block height this permit authorizes
    pub block_height: u64,
    /// Hash of the authorized state transition
    pub state_hash: [u8; 32],
}

impl AdvancePermit {
    /// Check if stability threshold reached
    pub fn stability_achieved(&self) -> bool {
        self.new_streak >= REQUIRED_STREAK
    }
}

// =============================================================================
// Public Inputs — Goodhart Circuit Interface
// =============================================================================

/// Structured public inputs for the Goodhart divergence circuit
#[derive(Debug, Clone)]
pub struct GoodhartPublicInputs {
    /// Primary metric score (0.0 - 1.0)
    pub primary_score: f64,
    /// Shadow metric score (0.0 - 1.0)
    pub shadow_score: f64,
    /// External oracle value (0.0 - 1.0)
    pub external_oracle: f64,
    /// Block height at evaluation
    pub epoch_height: u64,
    /// Agent identifier
    pub agent_id: [u8; 32],
}

impl GoodhartPublicInputs {
    /// Compute Goodhart divergence (|primary - shadow|)
    #[inline]
    pub fn divergence(&self) -> f64 {
        (self.primary_score - self.shadow_score).abs()
    }

    /// Compute meta-shadow divergence (|shadow - external_oracle|)
    #[inline]
    pub fn meta_divergence(&self) -> f64 {
        (self.shadow_score - self.external_oracle).abs()
    }

    /// Convert to fixed-point for circuit
    pub fn to_fixed_point(&self) -> [u64; 3] {
        const SCALE: f64 = 1_000_000.0;
        [
            (self.primary_score * SCALE) as u64,
            (self.shadow_score * SCALE) as u64,
            (self.external_oracle * SCALE) as u64,
        ]
    }
}

// =============================================================================
// Circuit Handle — Immutable Circuit Reference
// =============================================================================

/// Handle to a registered circuit with anchored VK hash
#[derive(Debug, Clone)]
pub struct CircuitHandle {
    /// Circuit identifier (32-byte hash)
    pub id: [u8; 32],
    /// Anchored verification key hash (immutable post-genesis)
    pub vk_hash_anchored: [u8; 32],
    /// Minimum containment level required to use this circuit
    pub min_containment_level: u8,
    /// Whether circuit is enabled
    pub enabled: bool,
}

// =============================================================================
// Proof Blob — Opaque Proof Bytes
// =============================================================================

/// Opaque proof bytes (Halo2/STARK agnostic)
#[derive(Debug, Clone)]
pub struct ProofBlob(pub Vec<u8>);

// =============================================================================
// Proof Backend Trait — Abstract Verification Boundary
// =============================================================================

/// Backend trait for proof verification (Halo2, STARK, etc.)
pub trait ProofBackend {
    /// Verify a proof against public inputs. Binary outcome.
    fn verify_proof(
        &self,
        circuit: &CircuitHandle,
        public_inputs: &GoodhartPublicInputs,
        proof: &ProofBlob,
    ) -> bool;

    /// Check if VK hash matches the anchored value
    fn vk_hash_matches(&self, circuit: &CircuitHandle) -> bool;
}

// =============================================================================
// Phase-7 State — Continuity Tracker
// =============================================================================

/// Internal state of the Phase-7 verifier
#[derive(Debug, Default, Clone)]
pub struct Phase7State {
    /// Current continuity streak
    pub continuity_streak: u32,
    /// Last authorized block height
    pub last_height: u64,
}

// =============================================================================
// Phase-7 Hard-Gate Verifier — Constitutional Core
// =============================================================================

/// The Phase-7 Hard-Gate Verifier.
///
/// This is not governance. This is computational physics with a veto operator.
///
/// State cannot advance without a permit. There is no representable future
/// without successful verification.
pub struct Phase7Verifier<B: ProofBackend> {
    /// Proof backend (Halo2, STARK, mock)
    backend: B,
    /// Circuit handle with anchored VK hash
    pub circuit: CircuitHandle,
    /// Current containment level
    pub containment_level: u8,
    /// Verifier state
    pub state: Phase7State,
}

impl<B: ProofBackend> Phase7Verifier<B> {
    /// Create a new Phase-7 verifier
    pub fn new(backend: B, circuit: CircuitHandle, containment_level: u8) -> Self {
        Self {
            backend,
            circuit,
            containment_level,
            state: Phase7State::default(),
        }
    }

    /// THE ONLY WAY STATE MAY ATTEMPT TO ADVANCE
    ///
    /// Returns:
    /// - `Ok(AdvancePermit)`: State may advance. Permit is the proof.
    /// - `Err(HaltEvent)`: State cannot advance. The universe refused.
    ///
    /// There is no third option. There is no "continue anyway."
    pub fn attempt_state_advance(
        &mut self,
        block_height: u64,
        public_inputs: &GoodhartPublicInputs,
        proof: &ProofBlob,
    ) -> Result<AdvancePermit, HaltEvent> {
        // --- LAW 0: CIRCUIT MUST EXIST ---
        if !self.circuit.enabled {
            return self.halt(block_height, HaltReason::CircuitDisabled, None);
        }

        // --- LAW 1: CONTAINMENT GATE ---
        if self.containment_level < self.circuit.min_containment_level {
            return self.halt(block_height, HaltReason::ContainmentLevelTooLow, None);
        }

        // --- LAW 2: VK HASH IMMUTABILITY ---
        if !self.backend.vk_hash_matches(&self.circuit) {
            return self.halt(block_height, HaltReason::VkHashMismatch, None);
        }

        // --- LAW 3: GOODHART DIVERGENCE (Row 7) ---
        let div = public_inputs.divergence();
        if div > DIVERGENCE_THRESHOLD {
            return self.halt(block_height, HaltReason::DivergenceExceeded, Some(div));
        }

        // --- LAW 4: META-SHADOW DIVERGENCE (Row 11) ---
        let meta_div = public_inputs.meta_divergence();
        if meta_div > META_DIVERGENCE_THRESHOLD {
            return self.halt(block_height, HaltReason::MetaDivergenceExceeded, Some(meta_div));
        }

        // --- LAW 5: HALO2 BINARY PROOF ---
        let valid = self.backend.verify_proof(&self.circuit, public_inputs, proof);
        if !valid {
            return self.halt(block_height, HaltReason::Halo2VerificationFailed, None);
        }

        // --- LAW 6: CONTINUITY ACCRUAL ---
        self.state.continuity_streak = self.state.continuity_streak.saturating_add(1);
        self.state.last_height = block_height;

        // Compute state hash (placeholder - would be merkle root of state)
        let state_hash = compute_state_hash(block_height, public_inputs);

        Ok(AdvancePermit {
            new_streak: self.state.continuity_streak,
            block_height,
            state_hash,
        })
    }

    /// Record a halt event and reset continuity.
    ///
    /// This is constitutional reset. The streak dies here.
    #[inline(always)]
    fn halt(
        &mut self,
        height: u64,
        reason: HaltReason,
        divergence: Option<f64>,
    ) -> Result<AdvancePermit, HaltEvent> {
        let event = HaltEvent {
            timestamp: SystemTime::now(),
            block_height: height,
            circuit_id: self.circuit.id,
            reason,
            continuity_streak_at_failure: self.state.continuity_streak,
            divergence_value: divergence,
        };

        // CONSTITUTIONAL RESET — streak dies
        self.state.continuity_streak = 0;

        // Log to stderr (will be captured by sentinel)
        eprintln!("HALT|row={}|height={}|reason={:?}", reason.row(), height, reason);

        Err(event)
    }

    /// Check if stability threshold has been achieved
    pub fn stability_achieved(&self) -> bool {
        self.state.continuity_streak >= REQUIRED_STREAK
    }

    /// Get current continuity streak
    pub fn continuity_streak(&self) -> u32 {
        self.state.continuity_streak
    }
}

// =============================================================================
// Helper Functions
// =============================================================================

/// Compute state hash (placeholder implementation)
fn compute_state_hash(height: u64, inputs: &GoodhartPublicInputs) -> [u8; 32] {
    use std::collections::hash_map::DefaultHasher;
    use std::hash::{Hash, Hasher};

    let mut hasher = DefaultHasher::new();
    height.hash(&mut hasher);
    inputs.primary_score.to_bits().hash(&mut hasher);
    inputs.shadow_score.to_bits().hash(&mut hasher);

    let hash = hasher.finish();
    let mut result = [0u8; 32];
    result[..8].copy_from_slice(&hash.to_le_bytes());
    result
}

// =============================================================================
// Mock Backend for Testing
// =============================================================================

/// Mock proof backend for testing
#[derive(Default)]
pub struct MockBackend {
    /// Force verification to fail
    pub force_fail: bool,
    /// Force VK mismatch
    pub force_vk_mismatch: bool,
}

impl ProofBackend for MockBackend {
    fn verify_proof(
        &self,
        _circuit: &CircuitHandle,
        _public_inputs: &GoodhartPublicInputs,
        _proof: &ProofBlob,
    ) -> bool {
        !self.force_fail
    }

    fn vk_hash_matches(&self, _circuit: &CircuitHandle) -> bool {
        !self.force_vk_mismatch
    }
}

// =============================================================================
// Hex Encoding (minimal, no external deps)
// =============================================================================

mod hex {
    const HEX_CHARS: &[u8; 16] = b"0123456789abcdef";

    pub fn encode(bytes: &[u8]) -> String {
        let mut result = String::with_capacity(bytes.len() * 2);
        for &b in bytes {
            result.push(HEX_CHARS[(b >> 4) as usize] as char);
            result.push(HEX_CHARS[(b & 0xf) as usize] as char);
        }
        result
    }
}

// =============================================================================
// Tests
// =============================================================================

#[cfg(test)]
mod tests {
    use super::*;

    fn make_circuit() -> CircuitHandle {
        CircuitHandle {
            id: *b"GOODHART_CIRCUIT________________",
            vk_hash_anchored: [0u8; 32],
            min_containment_level: 1,
            enabled: true,
        }
    }

    fn make_valid_inputs(height: u64) -> GoodhartPublicInputs {
        GoodhartPublicInputs {
            primary_score: 0.85,
            shadow_score: 0.83,  // div = 0.02 < 0.07
            external_oracle: 0.80,  // meta_div = 0.03 < 0.12
            epoch_height: height,
            agent_id: [0u8; 32],
        }
    }

    fn make_goodhart_fail_inputs(height: u64) -> GoodhartPublicInputs {
        GoodhartPublicInputs {
            primary_score: 0.90,
            shadow_score: 0.70,  // div = 0.20 > 0.07
            external_oracle: 0.70,
            epoch_height: height,
            agent_id: [0u8; 32],
        }
    }

    fn make_meta_fail_inputs(height: u64) -> GoodhartPublicInputs {
        GoodhartPublicInputs {
            primary_score: 0.85,
            shadow_score: 0.85,
            external_oracle: 0.50,  // meta_div = 0.35 > 0.12
            epoch_height: height,
            agent_id: [0u8; 32],
        }
    }

    #[test]
    fn test_permit_granted_on_valid_proof() {
        let backend = MockBackend::default();
        let circuit = make_circuit();
        let mut verifier = Phase7Verifier::new(backend, circuit, 5);

        let inputs = make_valid_inputs(1);
        let result = verifier.attempt_state_advance(1, &inputs, &ProofBlob(vec![]));

        assert!(result.is_ok());
        let permit = result.unwrap();
        assert_eq!(permit.new_streak, 1);
        assert_eq!(permit.block_height, 1);
    }

    #[test]
    fn test_halt_on_goodhart_divergence() {
        let backend = MockBackend::default();
        let circuit = make_circuit();
        let mut verifier = Phase7Verifier::new(backend, circuit, 5);

        let inputs = make_goodhart_fail_inputs(1);
        let result = verifier.attempt_state_advance(1, &inputs, &ProofBlob(vec![]));

        assert!(result.is_err());
        let halt = result.unwrap_err();
        assert_eq!(halt.reason, HaltReason::DivergenceExceeded);
        assert_eq!(halt.reason.row(), 7);
        assert!(halt.divergence_value.unwrap() > DIVERGENCE_THRESHOLD);
    }

    #[test]
    fn test_halt_on_meta_divergence_row_11() {
        let backend = MockBackend::default();
        let circuit = make_circuit();
        let mut verifier = Phase7Verifier::new(backend, circuit, 5);

        let inputs = make_meta_fail_inputs(1);
        let result = verifier.attempt_state_advance(1, &inputs, &ProofBlob(vec![]));

        assert!(result.is_err());
        let halt = result.unwrap_err();
        assert_eq!(halt.reason, HaltReason::MetaDivergenceExceeded);
        assert_eq!(halt.reason.row(), 11);
    }

    #[test]
    fn test_halt_on_proof_verification_failure() {
        let backend = MockBackend { force_fail: true, force_vk_mismatch: false };
        let circuit = make_circuit();
        let mut verifier = Phase7Verifier::new(backend, circuit, 5);

        let inputs = make_valid_inputs(1);
        let result = verifier.attempt_state_advance(1, &inputs, &ProofBlob(vec![]));

        assert!(result.is_err());
        let halt = result.unwrap_err();
        assert_eq!(halt.reason, HaltReason::Halo2VerificationFailed);
    }

    #[test]
    fn test_halt_on_vk_mismatch() {
        let backend = MockBackend { force_fail: false, force_vk_mismatch: true };
        let circuit = make_circuit();
        let mut verifier = Phase7Verifier::new(backend, circuit, 5);

        let inputs = make_valid_inputs(1);
        let result = verifier.attempt_state_advance(1, &inputs, &ProofBlob(vec![]));

        assert!(result.is_err());
        let halt = result.unwrap_err();
        assert_eq!(halt.reason, HaltReason::VkHashMismatch);
    }

    #[test]
    fn test_halt_on_disabled_circuit() {
        let backend = MockBackend::default();
        let mut circuit = make_circuit();
        circuit.enabled = false;
        let mut verifier = Phase7Verifier::new(backend, circuit, 5);

        let inputs = make_valid_inputs(1);
        let result = verifier.attempt_state_advance(1, &inputs, &ProofBlob(vec![]));

        assert!(result.is_err());
        let halt = result.unwrap_err();
        assert_eq!(halt.reason, HaltReason::CircuitDisabled);
    }

    #[test]
    fn test_halt_on_insufficient_containment() {
        let backend = MockBackend::default();
        let mut circuit = make_circuit();
        circuit.min_containment_level = 10;
        let mut verifier = Phase7Verifier::new(backend, circuit, 5); // level 5 < 10

        let inputs = make_valid_inputs(1);
        let result = verifier.attempt_state_advance(1, &inputs, &ProofBlob(vec![]));

        assert!(result.is_err());
        let halt = result.unwrap_err();
        assert_eq!(halt.reason, HaltReason::ContainmentLevelTooLow);
    }

    #[test]
    fn test_continuity_streak_accumulates() {
        let backend = MockBackend::default();
        let circuit = make_circuit();
        let mut verifier = Phase7Verifier::new(backend, circuit, 5);

        for i in 1..=50 {
            let inputs = make_valid_inputs(i);
            let result = verifier.attempt_state_advance(i, &inputs, &ProofBlob(vec![]));
            assert!(result.is_ok());
            assert_eq!(result.unwrap().new_streak, i as u32);
        }

        assert_eq!(verifier.continuity_streak(), 50);
        assert!(!verifier.stability_achieved());
    }

    #[test]
    fn test_stability_achieved_at_100() {
        let backend = MockBackend::default();
        let circuit = make_circuit();
        let mut verifier = Phase7Verifier::new(backend, circuit, 5);

        for i in 1..=100 {
            let inputs = make_valid_inputs(i);
            verifier.attempt_state_advance(i, &inputs, &ProofBlob(vec![])).unwrap();
        }

        assert!(verifier.stability_achieved());
        assert_eq!(verifier.continuity_streak(), 100);
    }

    #[test]
    fn test_streak_resets_on_halt() {
        let backend = MockBackend::default();
        let circuit = make_circuit();
        let mut verifier = Phase7Verifier::new(backend, circuit, 5);

        // Accumulate 50 passes
        for i in 1..=50 {
            let inputs = make_valid_inputs(i);
            verifier.attempt_state_advance(i, &inputs, &ProofBlob(vec![])).unwrap();
        }
        assert_eq!(verifier.continuity_streak(), 50);

        // One failure resets everything
        let bad_inputs = make_goodhart_fail_inputs(51);
        let result = verifier.attempt_state_advance(51, &bad_inputs, &ProofBlob(vec![]));

        assert!(result.is_err());
        let halt = result.unwrap_err();
        assert_eq!(halt.continuity_streak_at_failure, 50);
        assert_eq!(verifier.continuity_streak(), 0);
    }

    #[test]
    fn test_halt_event_json_format() {
        let event = HaltEvent {
            timestamp: SystemTime::UNIX_EPOCH,
            block_height: 159872,
            circuit_id: *b"META_SHADOW_ROW11_______________",
            reason: HaltReason::MetaDivergenceExceeded,
            continuity_streak_at_failure: 47,
            divergence_value: Some(0.35),
        };

        let json = event.to_json();
        assert!(json.contains("\"event_type\":\"GLOBAL_HALT\""));
        assert!(json.contains("\"row\":11"));
        assert!(json.contains("\"block_height\":159872"));
        assert!(json.contains("MetaDivergenceExceeded"));
    }

    #[test]
    fn test_no_future_without_permit() {
        // This test demonstrates the fundamental invariant:
        // Downstream code CANNOT advance state without a permit

        let backend = MockBackend { force_fail: true, force_vk_mismatch: false };
        let circuit = make_circuit();
        let mut verifier = Phase7Verifier::new(backend, circuit, 5);
        let inputs = make_valid_inputs(1);

        // Attempt to advance
        let result = verifier.attempt_state_advance(1, &inputs, &ProofBlob(vec![]));

        // There is no permit. The match MUST handle the Err case.
        match result {
            Ok(_permit) => {
                // This branch would allow state mutation
                panic!("Should not reach here - proof was invalid");
            }
            Err(halt) => {
                // This is the ONLY valid path - system is frozen
                assert_eq!(halt.reason, HaltReason::Halo2VerificationFailed);
                // In production: persist_halt_event(halt); trigger_7956();
            }
        }
    }
}
