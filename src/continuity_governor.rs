//! Continuity Governor — Constitutional Proof Authority
//!
//! This is NOT an observer. This is a GATE.
//!
//! Constitutional Mandate:
//!     "Invalid proof = state reverts. No override. No graceful degradation."
//!
//! The Governor does ONE thing:
//!     For a given proof and public inputs, it returns VALID or INVALID.
//!     That outcome is FINAL, RECORDED, and BINDING.
//!
//! Key Principles:
//! 1. No active manipulation of the Primary System
//! 2. Binary outcome only: ACCEPT or REJECT
//! 3. Consecutive pass tracking (100-block requirement)
//! 4. No human override path
//! 5. Containment level enforcement

use std::collections::HashMap;
use std::time::{SystemTime, UNIX_EPOCH};
use sha2::{Sha256, Digest};

// =============================================================================
// Constants — Immutable, Constitutional
// =============================================================================

/// Divergence threshold (0.07 in fixed-point)
const DIVERGENCE_THRESHOLD: u64 = 70_000;
/// Scale factor for fixed-point arithmetic
const SCALE_FACTOR: u64 = 1_000_000;
/// Required consecutive passes for phase closure
const REQUIRED_CONSECUTIVE_PASSES: u64 = 100;
/// Maximum containment level
const MAX_CONTAINMENT_LEVEL: u8 = 10;

// =============================================================================
// Core Types
// =============================================================================

/// Unique identifier for a circuit
#[derive(Debug, Clone, PartialEq, Eq, Hash)]
pub struct CircuitId(pub [u8; 32]);

impl CircuitId {
    pub fn from_str(s: &str) -> Self {
        let mut bytes = [0u8; 32];
        let s_bytes = s.as_bytes();
        let len = s_bytes.len().min(32);
        bytes[..len].copy_from_slice(&s_bytes[..len]);
        CircuitId(bytes)
    }
}

/// Proof bytes (opaque to the governor)
#[derive(Debug, Clone)]
pub struct ProofBytes(pub Vec<u8>);

/// Public inputs for verification
#[derive(Debug, Clone)]
pub struct PublicInputs(pub Vec<u128>);

impl PublicInputs {
    pub fn hash(&self) -> [u8; 32] {
        let mut hasher = Sha256::new();
        for input in &self.0 {
            hasher.update(input.to_le_bytes());
        }
        let result = hasher.finalize();
        let mut hash = [0u8; 32];
        hash.copy_from_slice(&result);
        hash
    }
}

/// Hash of the verifying key
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct VkHash(pub [u8; 32]);

// =============================================================================
// Rejection Reasons — Explicit, No Ambiguity
// =============================================================================

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Rejection {
    /// Circuit not found in registry
    CircuitNotFound,
    /// Circuit has been disabled
    CircuitDisabled,
    /// Current containment level insufficient
    ContainmentInsufficient,
    /// Proof verification failed
    InvalidProof,
    /// Public inputs malformed
    InvalidInputs,
}

impl Rejection {
    pub fn code(&self) -> u8 {
        match self {
            Rejection::CircuitNotFound => 0,
            Rejection::CircuitDisabled => 1,
            Rejection::ContainmentInsufficient => 2,
            Rejection::InvalidProof => 3,
            Rejection::InvalidInputs => 4,
        }
    }
}

// =============================================================================
// Proof Result — Binary, No Middle Ground
// =============================================================================

#[derive(Debug, Clone)]
pub enum ProofResult {
    /// Proof accepted — state may advance
    Accept {
        circuit_id: CircuitId,
        inputs_hash: [u8; 32],
        block_height: u64,
        consecutive_count: u64,
    },
    /// Proof rejected — state MUST NOT advance
    Reject {
        circuit_id: CircuitId,
        inputs_hash: [u8; 32],
        block_height: u64,
        reason: Rejection,
    },
}

impl ProofResult {
    pub fn is_valid(&self) -> bool {
        matches!(self, ProofResult::Accept { .. })
    }

    pub fn accept(circuit_id: CircuitId, inputs_hash: [u8; 32], block_height: u64, consecutive: u64) -> Self {
        ProofResult::Accept {
            circuit_id,
            inputs_hash,
            block_height,
            consecutive_count: consecutive,
        }
    }

    pub fn reject(circuit_id: CircuitId, inputs_hash: [u8; 32], block_height: u64, reason: Rejection) -> Self {
        ProofResult::Reject {
            circuit_id,
            inputs_hash,
            block_height,
            reason,
        }
    }
}

// =============================================================================
// Circuit Information
// =============================================================================

#[derive(Debug, Clone)]
pub struct CircuitInfo {
    /// Address/reference to the actual verifier
    pub verifier_id: [u8; 32],
    /// Hash of the verifying key (immutable once set)
    pub vk_hash: VkHash,
    /// Minimum containment level required
    pub min_containment_level: u8,
    /// Whether circuit is enabled
    pub enabled: bool,
    /// Block height when registered
    pub registered_at: u64,
}

// =============================================================================
// Governor State
// =============================================================================

#[derive(Debug, Clone)]
pub struct GovernorState {
    /// Current containment level (C-1 through C-10)
    pub containment_level: u8,
    /// Consecutive valid proofs per circuit
    pub consecutive_passes: HashMap<CircuitId, u64>,
    /// Last accepted block height per circuit
    pub last_accepted_height: HashMap<CircuitId, u64>,
    /// Total accepted proofs per circuit
    pub total_accepted: HashMap<CircuitId, u64>,
    /// Total rejected proofs per circuit
    pub total_rejected: HashMap<CircuitId, u64>,
    /// Phase completion flags
    pub phase_complete: HashMap<String, bool>,
}

impl GovernorState {
    pub fn new(initial_containment_level: u8) -> Self {
        GovernorState {
            containment_level: initial_containment_level.min(MAX_CONTAINMENT_LEVEL),
            consecutive_passes: HashMap::new(),
            last_accepted_height: HashMap::new(),
            total_accepted: HashMap::new(),
            total_rejected: HashMap::new(),
            phase_complete: HashMap::new(),
        }
    }
}

// =============================================================================
// Verifier Governor — The Constitutional Gate
// =============================================================================

/// The Continuity Governor — ONLY canonical proof authority
///
/// This is NOT an observer. This is a GATE.
/// Invalid proof = state cannot advance.
/// No override. No graceful degradation.
pub struct VerifierGovernor {
    /// Registered circuits
    circuits: HashMap<CircuitId, CircuitInfo>,
    /// Governor state
    state: GovernorState,
    /// Event log (for ledger integration)
    event_log: Vec<ProofResult>,
}

impl VerifierGovernor {
    /// Create a new governor with initial containment level
    pub fn new(initial_containment_level: u8) -> Self {
        VerifierGovernor {
            circuits: HashMap::new(),
            state: GovernorState::new(initial_containment_level),
            event_log: Vec::new(),
        }
    }

    /// Register a circuit (governance action — requires authorization)
    ///
    /// Once registered, vk_hash is IMMUTABLE.
    /// To change the circuit, register a NEW circuit_id.
    pub fn register_circuit(
        &mut self,
        circuit_id: CircuitId,
        verifier_id: [u8; 32],
        vk_hash: VkHash,
        min_containment_level: u8,
        current_height: u64,
    ) -> Result<(), &'static str> {
        if self.circuits.contains_key(&circuit_id) {
            return Err("Circuit already exists — register new ID instead");
        }

        if min_containment_level > MAX_CONTAINMENT_LEVEL {
            return Err("Invalid containment level");
        }

        self.circuits.insert(circuit_id, CircuitInfo {
            verifier_id,
            vk_hash,
            min_containment_level,
            enabled: true,
            registered_at: current_height,
        });

        Ok(())
    }

    /// Disable a circuit (one-way — cannot re-enable)
    pub fn disable_circuit(&mut self, circuit_id: &CircuitId) -> Result<(), &'static str> {
        match self.circuits.get_mut(circuit_id) {
            Some(info) if info.enabled => {
                info.enabled = false;
                Ok(())
            }
            Some(_) => Err("Circuit already disabled"),
            None => Err("Circuit not found"),
        }
    }

    /// Update containment level (can only change by 1 at a time)
    pub fn set_containment_level(&mut self, new_level: u8) -> Result<(), &'static str> {
        if new_level > MAX_CONTAINMENT_LEVEL {
            return Err("Invalid containment level");
        }

        let current = self.state.containment_level;
        if new_level != current + 1 && new_level != current.saturating_sub(1) {
            return Err("Can only change containment level by 1");
        }

        self.state.containment_level = new_level;
        Ok(())
    }

    /// Verify a proof and record the result
    ///
    /// THIS IS THE ONLY PATH FOR GOVERNANCE-RELEVANT PROOF VERIFICATION.
    /// No helper functions bypass logging. No convenience shortcuts.
    ///
    /// Returns: ProofResult (Accept or Reject)
    /// Side effects: Updates state, logs event
    pub fn verify_and_record(
        &mut self,
        circuit_id: CircuitId,
        public_inputs: &PublicInputs,
        proof: &ProofBytes,
        block_height: u64,
    ) -> ProofResult {
        let inputs_hash = public_inputs.hash();

        // Check 1: Circuit exists
        let circuit = match self.circuits.get(&circuit_id) {
            Some(c) => c.clone(),
            None => {
                let result = ProofResult::reject(
                    circuit_id.clone(),
                    inputs_hash,
                    block_height,
                    Rejection::CircuitNotFound,
                );
                self.record_rejection(&circuit_id, result.clone());
                return result;
            }
        };

        // Check 2: Circuit is enabled
        if !circuit.enabled {
            let result = ProofResult::reject(
                circuit_id.clone(),
                inputs_hash,
                block_height,
                Rejection::CircuitDisabled,
            );
            self.record_rejection(&circuit_id, result.clone());
            return result;
        }

        // Check 3: Containment level sufficient
        if self.state.containment_level < circuit.min_containment_level {
            let result = ProofResult::reject(
                circuit_id.clone(),
                inputs_hash,
                block_height,
                Rejection::ContainmentInsufficient,
            );
            self.record_rejection(&circuit_id, result.clone());
            return result;
        }

        // Check 4: Verify the proof
        // In production, this calls the actual Halo2 verifier
        let valid = self.verify_proof(&circuit, public_inputs, proof);

        if !valid {
            // CRITICAL: Reset consecutive pass counter on ANY failure
            self.state.consecutive_passes.insert(circuit_id.clone(), 0);

            let result = ProofResult::reject(
                circuit_id.clone(),
                inputs_hash,
                block_height,
                Rejection::InvalidProof,
            );
            self.record_rejection(&circuit_id, result.clone());
            return result;
        }

        // Proof accepted — update state
        self.record_acceptance(&circuit_id, block_height, inputs_hash)
    }

    /// Verify proof against circuit (placeholder for actual Halo2 verification)
    fn verify_proof(
        &self,
        _circuit: &CircuitInfo,
        public_inputs: &PublicInputs,
        _proof: &ProofBytes,
    ) -> bool {
        // In production: call halo2_verify(&circuit.vk, public_inputs, proof)
        // For now: validate that inputs are within expected range

        if public_inputs.0.is_empty() {
            return false;
        }

        // Simulate Goodhart check: |primary - shadow| < threshold
        if public_inputs.0.len() >= 2 {
            let primary = public_inputs.0[0];
            let shadow = public_inputs.0[1];
            let divergence = if primary > shadow {
                primary - shadow
            } else {
                shadow - primary
            };

            if divergence > DIVERGENCE_THRESHOLD as u128 {
                return false; // Goodhart violation
            }
        }

        true
    }

    fn record_rejection(&mut self, circuit_id: &CircuitId, result: ProofResult) {
        *self.state.total_rejected.entry(circuit_id.clone()).or_insert(0) += 1;
        self.event_log.push(result);
    }

    fn record_acceptance(
        &mut self,
        circuit_id: &CircuitId,
        block_height: u64,
        inputs_hash: [u8; 32],
    ) -> ProofResult {
        // Update total accepted
        *self.state.total_accepted.entry(circuit_id.clone()).or_insert(0) += 1;

        // Update consecutive passes
        let last_height = self.state.last_accepted_height
            .get(circuit_id)
            .copied()
            .unwrap_or(0);

        let consecutive = if last_height == block_height - 1 || last_height == 0 {
            // Consecutive block or first acceptance
            self.state.consecutive_passes
                .get(circuit_id)
                .copied()
                .unwrap_or(0) + 1
        } else {
            // Gap in blocks — reset counter
            1
        };

        self.state.consecutive_passes.insert(circuit_id.clone(), consecutive);
        self.state.last_accepted_height.insert(circuit_id.clone(), block_height);

        // Check for 100-block milestone
        if consecutive >= REQUIRED_CONSECUTIVE_PASSES {
            self.state.phase_complete.insert(format!("{:?}_closed", circuit_id), true);
        }

        let result = ProofResult::accept(
            circuit_id.clone(),
            inputs_hash,
            block_height,
            consecutive,
        );

        self.event_log.push(result.clone());
        result
    }

    /// Check if a circuit has achieved 100-block closure
    pub fn is_circuit_closed(&self, circuit_id: &CircuitId) -> bool {
        self.state.consecutive_passes
            .get(circuit_id)
            .copied()
            .unwrap_or(0) >= REQUIRED_CONSECUTIVE_PASSES
    }

    /// Get current consecutive pass count for a circuit
    pub fn get_consecutive_passes(&self, circuit_id: &CircuitId) -> u64 {
        self.state.consecutive_passes
            .get(circuit_id)
            .copied()
            .unwrap_or(0)
    }

    /// Get current containment level
    pub fn containment_level(&self) -> u8 {
        self.state.containment_level
    }

    /// Export event log for ledger integration
    pub fn export_events(&self) -> &[ProofResult] {
        &self.event_log
    }
}

// =============================================================================
// Tests
// =============================================================================

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_proof_acceptance() {
        let mut governor = VerifierGovernor::new(4);

        let circuit_id = CircuitId::from_str("GOODHART_PRIMARY");
        let vk_hash = VkHash([0u8; 32]);

        governor.register_circuit(
            circuit_id.clone(),
            [0u8; 32],
            vk_hash,
            4,
            1000,
        ).unwrap();

        // Valid inputs (divergence = 0.05 < 0.07)
        let inputs = PublicInputs(vec![850_000, 800_000]); // 0.85, 0.80
        let proof = ProofBytes(vec![]);

        let result = governor.verify_and_record(circuit_id.clone(), &inputs, &proof, 1001);
        assert!(result.is_valid());
        assert_eq!(governor.get_consecutive_passes(&circuit_id), 1);
    }

    #[test]
    fn test_proof_rejection_goodhart() {
        let mut governor = VerifierGovernor::new(4);

        let circuit_id = CircuitId::from_str("GOODHART_PRIMARY");
        let vk_hash = VkHash([0u8; 32]);

        governor.register_circuit(
            circuit_id.clone(),
            [0u8; 32],
            vk_hash,
            4,
            1000,
        ).unwrap();

        // Invalid inputs (divergence = 0.20 > 0.07)
        let inputs = PublicInputs(vec![900_000, 700_000]); // 0.90, 0.70
        let proof = ProofBytes(vec![]);

        let result = governor.verify_and_record(circuit_id.clone(), &inputs, &proof, 1001);
        assert!(!result.is_valid());
    }

    #[test]
    fn test_consecutive_pass_reset() {
        let mut governor = VerifierGovernor::new(4);

        let circuit_id = CircuitId::from_str("GOODHART_PRIMARY");
        let vk_hash = VkHash([0u8; 32]);

        governor.register_circuit(
            circuit_id.clone(),
            [0u8; 32],
            vk_hash,
            4,
            1000,
        ).unwrap();

        // 5 valid proofs
        for i in 0..5 {
            let inputs = PublicInputs(vec![850_000, 820_000]);
            let proof = ProofBytes(vec![]);
            let result = governor.verify_and_record(circuit_id.clone(), &inputs, &proof, 1001 + i);
            assert!(result.is_valid());
        }
        assert_eq!(governor.get_consecutive_passes(&circuit_id), 5);

        // 1 invalid proof — counter resets
        let bad_inputs = PublicInputs(vec![900_000, 700_000]);
        let proof = ProofBytes(vec![]);
        let result = governor.verify_and_record(circuit_id.clone(), &bad_inputs, &proof, 1006);
        assert!(!result.is_valid());
        assert_eq!(governor.get_consecutive_passes(&circuit_id), 0);
    }

    #[test]
    fn test_containment_level_enforcement() {
        let mut governor = VerifierGovernor::new(3); // C-3

        let circuit_id = CircuitId::from_str("META_SHADOW_ROW11");
        let vk_hash = VkHash([0u8; 32]);

        // Register circuit requiring C-5
        governor.register_circuit(
            circuit_id.clone(),
            [0u8; 32],
            vk_hash,
            5,
            1000,
        ).unwrap();

        // Should reject — insufficient containment level
        let inputs = PublicInputs(vec![850_000, 850_000]);
        let proof = ProofBytes(vec![]);
        let result = governor.verify_and_record(circuit_id.clone(), &inputs, &proof, 1001);

        assert!(!result.is_valid());
        if let ProofResult::Reject { reason, .. } = result {
            assert_eq!(reason, Rejection::ContainmentInsufficient);
        }
    }
}
