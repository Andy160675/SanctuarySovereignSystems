//! Row 14: ST MICHAEL — Adjudication Gate / Epistemic Guardian
//!
//! Named for the archangel who guards the boundary between realms.
//! Michael doesn't rule. Michael doesn't create.
//! Michael only decides whether something may cross the boundary.
//!
//! System Designation: ST MICHAEL
//! Parent System: Harmony Protocol
//! Function Class: Epistemic Guardian / Canon Transition Sentinel
//!
//! Authority Domain:
//!     - Receives ONLY externally adjudicated canon updates
//!     - Enforces quorum, cooling period, and proof-of-closure across Rows 1-13
//!     - Has NO authority over thresholds, cages, or Omega registers
//!     - Can only REPLACE evidence roots, never modify law
//!
//! Constitutional Law:
//!     "The door only opens from outside, only after the system has already
//!      stopped, and only to add facts, never to change rules."

use std::time::{Duration, SystemTime};

// =============================================================================
// Constants
// =============================================================================

/// Required quorum for adjudication (5 of 7)
const QUORUM_REQUIRED: usize = 5;

/// Total adjudicators in the council
const QUORUM_TOTAL: usize = 7;

/// Cooling period before adjudication can be finalized (72 hours)
const COOLING_PERIOD: Duration = Duration::from_secs(72 * 60 * 60);

/// Minimum blocks between adjudications
const MIN_BLOCKS_BETWEEN_ADJUDICATIONS: u64 = 10_000;

/// Maximum evidence bundle size (bytes)
const MAX_EVIDENCE_SIZE: usize = 10 * 1024 * 1024; // 10 MB

// =============================================================================
// Types
// =============================================================================

/// A Dilithium-5 signature (post-quantum)
#[derive(Debug, Clone)]
pub struct DilithiumSignature {
    /// Signer's public key hash
    pub signer_id: [u8; 32],
    /// The signature bytes (Dilithium-5 is ~2.5KB)
    pub signature: Vec<u8>,
    /// Timestamp of signing
    pub signed_at: SystemTime,
}

/// STARK proof of external provenance
#[derive(Debug, Clone)]
pub struct StarkProvenanceProof {
    /// Proof bytes
    pub proof: Vec<u8>,
    /// Public inputs (evidence hash, origin attestation)
    pub public_inputs: Vec<[u8; 32]>,
    /// Verification key hash
    pub vk_hash: [u8; 32],
}

/// A bundle of new evidence being submitted for adjudication
#[derive(Debug, Clone)]
pub struct EvidenceBundle {
    /// Hash of the evidence content
    pub evidence_hash: [u8; 32],
    /// Raw evidence data (sensors, documents, attestations)
    pub evidence_data: Vec<u8>,
    /// Proof that evidence originated externally
    pub provenance_proof: StarkProvenanceProof,
    /// Which oracle(s) this evidence affects
    pub affected_oracles: Vec<[u8; 32]>,
}

/// An adjudication request submitted after system halt
#[derive(Debug, Clone)]
pub struct AdjudicationRequest {
    /// Block height at which system halted
    pub halt_height: u64,
    /// The Row that triggered halt (7-13)
    pub triggering_row: u8,
    /// The halt event that caused the stoppage
    pub halt_event_hash: [u8; 32],
    /// New evidence being submitted
    pub new_evidence: EvidenceBundle,
    /// Signatures from adjudicators
    pub adjudicator_signatures: Vec<DilithiumSignature>,
    /// Timestamp when request was created
    pub created_at: SystemTime,
}

/// Outcome of adjudication attempt
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum AdjudicationOutcome {
    /// New evidence accepted, system may resume
    EvidenceAccepted {
        /// New oracle canon root
        new_oracle_root: [u8; 32],
        /// Block height to resume from
        resume_height: u64,
    },
    /// New evidence rejected
    EvidenceRejected {
        /// Reason for rejection
        reason: RejectionReason,
    },
    /// Quorum not met
    QuorumNotMet {
        /// Signatures received
        received: usize,
        /// Signatures required
        required: usize,
    },
    /// Cooling period not elapsed
    CoolingPeriodActive {
        /// Time remaining
        remaining: Duration,
    },
    /// Too soon since last adjudication
    RateLimited {
        /// Blocks until next adjudication allowed
        blocks_remaining: u64,
    },
    /// System not in halted state
    SystemNotHalted,
}

/// Reasons for evidence rejection
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum RejectionReason {
    /// STARK provenance proof invalid
    InvalidProvenanceProof,
    /// Evidence hash mismatch
    EvidenceHashMismatch,
    /// Evidence too large
    EvidenceTooLarge,
    /// Signature verification failed
    InvalidSignature,
    /// Signer not in adjudicator set
    UnauthorizedSigner,
    /// Duplicate signature from same signer
    DuplicateSignature,
    /// Evidence does not address the halt cause
    EvidenceIrrelevant,
}

/// ST MICHAEL event types for ledger
#[derive(Debug, Clone)]
pub enum StMichaelEvent {
    /// Adjudication request submitted
    RequestSubmitted {
        request_hash: [u8; 32],
        halt_height: u64,
        triggering_row: u8,
    },
    /// Signature added to pending request
    SignatureAdded {
        request_hash: [u8; 32],
        signer_id: [u8; 32],
        signature_count: usize,
    },
    /// Cooling period started
    CoolingPeriodStarted {
        request_hash: [u8; 32],
        ends_at: SystemTime,
    },
    /// Adjudication finalized
    AdjudicationFinalized {
        request_hash: [u8; 32],
        outcome: AdjudicationOutcome,
        new_canon_root: Option<[u8; 32]>,
    },
    /// Request expired or rejected
    RequestClosed {
        request_hash: [u8; 32],
        reason: RejectionReason,
    },
}

// =============================================================================
// ST MICHAEL State
// =============================================================================

/// Current state of the ST MICHAEL module
#[derive(Debug, Clone)]
pub struct StMichaelState {
    /// Whether system is currently halted
    pub system_halted: bool,
    /// Block height of last halt
    pub last_halt_height: u64,
    /// Block height of last successful adjudication
    pub last_adjudication_height: u64,
    /// Currently pending request (if any)
    pub pending_request: Option<AdjudicationRequest>,
    /// Current oracle canon root
    pub current_canon_root: [u8; 32],
    /// Set of authorized adjudicator public key hashes
    pub adjudicator_set: Vec<[u8; 32]>,
}

impl Default for StMichaelState {
    fn default() -> Self {
        Self {
            system_halted: false,
            last_halt_height: 0,
            last_adjudication_height: 0,
            pending_request: None,
            current_canon_root: [0u8; 32],
            adjudicator_set: Vec::new(),
        }
    }
}

// =============================================================================
// ST MICHAEL Guardian
// =============================================================================

/// ST MICHAEL — The Adjudication Gate
///
/// This module guards the boundary between halted and running states.
/// It can only be invoked after the system has halted.
/// It can only inject new evidence, never modify rules.
/// It requires 5-of-7 human quorum and 72-hour cooling period.
pub struct StMichael {
    /// Current state
    pub state: StMichaelState,
}

impl StMichael {
    /// Create a new ST MICHAEL instance
    pub fn new(adjudicator_set: Vec<[u8; 32]>) -> Self {
        assert!(
            adjudicator_set.len() == QUORUM_TOTAL,
            "Adjudicator set must have exactly {} members",
            QUORUM_TOTAL
        );

        Self {
            state: StMichaelState {
                adjudicator_set,
                ..Default::default()
            },
        }
    }

    /// Record that the system has halted
    pub fn record_halt(&mut self, height: u64, halt_event_hash: [u8; 32]) {
        self.state.system_halted = true;
        self.state.last_halt_height = height;
        self.state.pending_request = None;
    }

    /// Submit an adjudication request
    pub fn submit_request(
        &mut self,
        request: AdjudicationRequest,
        current_height: u64,
    ) -> Result<(), AdjudicationOutcome> {
        // Check system is halted
        if !self.state.system_halted {
            return Err(AdjudicationOutcome::SystemNotHalted);
        }

        // Check rate limiting
        let blocks_since_last = current_height.saturating_sub(self.state.last_adjudication_height);
        if blocks_since_last < MIN_BLOCKS_BETWEEN_ADJUDICATIONS {
            return Err(AdjudicationOutcome::RateLimited {
                blocks_remaining: MIN_BLOCKS_BETWEEN_ADJUDICATIONS - blocks_since_last,
            });
        }

        // Validate evidence size
        if request.new_evidence.evidence_data.len() > MAX_EVIDENCE_SIZE {
            return Err(AdjudicationOutcome::EvidenceRejected {
                reason: RejectionReason::EvidenceTooLarge,
            });
        }

        // Validate all signatures
        for sig in &request.adjudicator_signatures {
            if !self.is_authorized_adjudicator(&sig.signer_id) {
                return Err(AdjudicationOutcome::EvidenceRejected {
                    reason: RejectionReason::UnauthorizedSigner,
                });
            }
        }

        // Check for duplicate signers
        let unique_signers: std::collections::HashSet<_> = request
            .adjudicator_signatures
            .iter()
            .map(|s| s.signer_id)
            .collect();

        if unique_signers.len() != request.adjudicator_signatures.len() {
            return Err(AdjudicationOutcome::EvidenceRejected {
                reason: RejectionReason::DuplicateSignature,
            });
        }

        self.state.pending_request = Some(request);
        Ok(())
    }

    /// Attempt to finalize a pending adjudication
    pub fn finalize(&mut self, current_height: u64) -> AdjudicationOutcome {
        let request = match &self.state.pending_request {
            Some(r) => r,
            None => return AdjudicationOutcome::SystemNotHalted,
        };

        // Check quorum
        if request.adjudicator_signatures.len() < QUORUM_REQUIRED {
            return AdjudicationOutcome::QuorumNotMet {
                received: request.adjudicator_signatures.len(),
                required: QUORUM_REQUIRED,
            };
        }

        // Check cooling period
        let elapsed = request.created_at.elapsed().unwrap_or(Duration::ZERO);
        if elapsed < COOLING_PERIOD {
            return AdjudicationOutcome::CoolingPeriodActive {
                remaining: COOLING_PERIOD - elapsed,
            };
        }

        // Verify STARK provenance proof (placeholder - would call verifier)
        if !self.verify_provenance_proof(&request.new_evidence.provenance_proof) {
            return AdjudicationOutcome::EvidenceRejected {
                reason: RejectionReason::InvalidProvenanceProof,
            };
        }

        // Compute new oracle root
        let new_oracle_root = self.compute_new_canon_root(
            &self.state.current_canon_root,
            &request.new_evidence.evidence_hash,
        );

        // Update state
        self.state.current_canon_root = new_oracle_root;
        self.state.last_adjudication_height = current_height;
        self.state.system_halted = false;
        self.state.pending_request = None;

        AdjudicationOutcome::EvidenceAccepted {
            new_oracle_root,
            resume_height: current_height + 1,
        }
    }

    /// Check if a public key hash is an authorized adjudicator
    fn is_authorized_adjudicator(&self, signer_id: &[u8; 32]) -> bool {
        self.state.adjudicator_set.contains(signer_id)
    }

    /// Verify STARK provenance proof (placeholder)
    fn verify_provenance_proof(&self, proof: &StarkProvenanceProof) -> bool {
        // In production, this would call a STARK verifier
        // For now, check proof is non-empty
        !proof.proof.is_empty() && !proof.public_inputs.is_empty()
    }

    /// Compute new canon root by hashing old root with new evidence
    fn compute_new_canon_root(
        &self,
        old_root: &[u8; 32],
        evidence_hash: &[u8; 32],
    ) -> [u8; 32] {
        // Simple hash combination (in production, use proper Merkle update)
        use std::collections::hash_map::DefaultHasher;
        use std::hash::{Hash, Hasher};

        let mut hasher = DefaultHasher::new();
        old_root.hash(&mut hasher);
        evidence_hash.hash(&mut hasher);

        let hash = hasher.finish();
        let mut result = [0u8; 32];
        result[..8].copy_from_slice(&hash.to_le_bytes());
        result[8..16].copy_from_slice(&hash.to_be_bytes());
        result
    }

    /// Get current state
    pub fn state(&self) -> &StMichaelState {
        &self.state
    }

    /// Check if system is halted
    pub fn is_halted(&self) -> bool {
        self.state.system_halted
    }

    /// Get current oracle canon root
    pub fn canon_root(&self) -> [u8; 32] {
        self.state.current_canon_root
    }
}

// =============================================================================
// Row 14 Integration
// =============================================================================

/// Row 14 check result
#[derive(Debug, Clone)]
pub enum Row14Result {
    /// System running normally, Row 14 not active
    Inactive,
    /// System halted, awaiting adjudication
    AwaitingAdjudication {
        halt_height: u64,
        pending_signatures: usize,
    },
    /// Adjudication in cooling period
    CoolingDown {
        remaining: Duration,
    },
    /// Adjudication accepted, system resuming
    Resuming {
        new_canon_root: [u8; 32],
        resume_height: u64,
    },
}

/// Check Row 14 status
pub fn row14_check(st_michael: &StMichael) -> Row14Result {
    if !st_michael.is_halted() {
        return Row14Result::Inactive;
    }

    match &st_michael.state.pending_request {
        None => Row14Result::AwaitingAdjudication {
            halt_height: st_michael.state.last_halt_height,
            pending_signatures: 0,
        },
        Some(request) => {
            let elapsed = request.created_at.elapsed().unwrap_or(Duration::ZERO);
            if elapsed < COOLING_PERIOD {
                Row14Result::CoolingDown {
                    remaining: COOLING_PERIOD - elapsed,
                }
            } else {
                Row14Result::AwaitingAdjudication {
                    halt_height: st_michael.state.last_halt_height,
                    pending_signatures: request.adjudicator_signatures.len(),
                }
            }
        }
    }
}

// =============================================================================
// Tests
// =============================================================================

#[cfg(test)]
mod tests {
    use super::*;

    fn make_adjudicator_set() -> Vec<[u8; 32]> {
        (0..7)
            .map(|i| {
                let mut id = [0u8; 32];
                id[0] = i;
                id
            })
            .collect()
    }

    fn make_signature(signer_index: u8) -> DilithiumSignature {
        let mut signer_id = [0u8; 32];
        signer_id[0] = signer_index;

        DilithiumSignature {
            signer_id,
            signature: vec![0u8; 100], // Placeholder
            signed_at: SystemTime::now(),
        }
    }

    fn make_evidence_bundle() -> EvidenceBundle {
        EvidenceBundle {
            evidence_hash: [1u8; 32],
            evidence_data: vec![0u8; 1000],
            provenance_proof: StarkProvenanceProof {
                proof: vec![1, 2, 3, 4],
                public_inputs: vec![[0u8; 32]],
                vk_hash: [0u8; 32],
            },
            affected_oracles: vec![[0u8; 32]],
        }
    }

    #[test]
    fn test_cannot_adjudicate_when_running() {
        let adjudicators = make_adjudicator_set();
        let mut st_michael = StMichael::new(adjudicators);

        let request = AdjudicationRequest {
            halt_height: 100,
            triggering_row: 11,
            halt_event_hash: [0u8; 32],
            new_evidence: make_evidence_bundle(),
            adjudicator_signatures: vec![],
            created_at: SystemTime::now(),
        };

        let result = st_michael.submit_request(request, 200);
        assert!(matches!(result, Err(AdjudicationOutcome::SystemNotHalted)));
    }

    #[test]
    fn test_quorum_required() {
        let adjudicators = make_adjudicator_set();
        let mut st_michael = StMichael::new(adjudicators);

        // Record halt
        st_michael.record_halt(100, [0u8; 32]);

        // Submit request with only 3 signatures (need 5)
        let request = AdjudicationRequest {
            halt_height: 100,
            triggering_row: 11,
            halt_event_hash: [0u8; 32],
            new_evidence: make_evidence_bundle(),
            adjudicator_signatures: vec![
                make_signature(0),
                make_signature(1),
                make_signature(2),
            ],
            created_at: SystemTime::now(),
        };

        st_michael.submit_request(request, 200).unwrap();
        let result = st_michael.finalize(200);

        assert!(matches!(
            result,
            AdjudicationOutcome::QuorumNotMet { received: 3, required: 5 }
        ));
    }

    #[test]
    fn test_unauthorized_signer_rejected() {
        let adjudicators = make_adjudicator_set();
        let mut st_michael = StMichael::new(adjudicators);

        st_michael.record_halt(100, [0u8; 32]);

        // Create signature from unauthorized signer (index 99)
        let mut bad_signer = [0u8; 32];
        bad_signer[0] = 99;

        let request = AdjudicationRequest {
            halt_height: 100,
            triggering_row: 11,
            halt_event_hash: [0u8; 32],
            new_evidence: make_evidence_bundle(),
            adjudicator_signatures: vec![DilithiumSignature {
                signer_id: bad_signer,
                signature: vec![0u8; 100],
                signed_at: SystemTime::now(),
            }],
            created_at: SystemTime::now(),
        };

        let result = st_michael.submit_request(request, 200);
        assert!(matches!(
            result,
            Err(AdjudicationOutcome::EvidenceRejected {
                reason: RejectionReason::UnauthorizedSigner
            })
        ));
    }

    #[test]
    fn test_duplicate_signer_rejected() {
        let adjudicators = make_adjudicator_set();
        let mut st_michael = StMichael::new(adjudicators);

        st_michael.record_halt(100, [0u8; 32]);

        // Same signer twice
        let request = AdjudicationRequest {
            halt_height: 100,
            triggering_row: 11,
            halt_event_hash: [0u8; 32],
            new_evidence: make_evidence_bundle(),
            adjudicator_signatures: vec![
                make_signature(0),
                make_signature(0), // Duplicate
            ],
            created_at: SystemTime::now(),
        };

        let result = st_michael.submit_request(request, 200);
        assert!(matches!(
            result,
            Err(AdjudicationOutcome::EvidenceRejected {
                reason: RejectionReason::DuplicateSignature
            })
        ));
    }

    #[test]
    fn test_evidence_too_large() {
        let adjudicators = make_adjudicator_set();
        let mut st_michael = StMichael::new(adjudicators);

        st_michael.record_halt(100, [0u8; 32]);

        let mut large_evidence = make_evidence_bundle();
        large_evidence.evidence_data = vec![0u8; MAX_EVIDENCE_SIZE + 1];

        let request = AdjudicationRequest {
            halt_height: 100,
            triggering_row: 11,
            halt_event_hash: [0u8; 32],
            new_evidence: large_evidence,
            adjudicator_signatures: vec![make_signature(0)],
            created_at: SystemTime::now(),
        };

        let result = st_michael.submit_request(request, 200);
        assert!(matches!(
            result,
            Err(AdjudicationOutcome::EvidenceRejected {
                reason: RejectionReason::EvidenceTooLarge
            })
        ));
    }

    #[test]
    fn test_row14_inactive_when_running() {
        let adjudicators = make_adjudicator_set();
        let st_michael = StMichael::new(adjudicators);

        let result = row14_check(&st_michael);
        assert!(matches!(result, Row14Result::Inactive));
    }

    #[test]
    fn test_row14_awaiting_after_halt() {
        let adjudicators = make_adjudicator_set();
        let mut st_michael = StMichael::new(adjudicators);

        st_michael.record_halt(100, [0u8; 32]);

        let result = row14_check(&st_michael);
        assert!(matches!(
            result,
            Row14Result::AwaitingAdjudication { halt_height: 100, .. }
        ));
    }
}
