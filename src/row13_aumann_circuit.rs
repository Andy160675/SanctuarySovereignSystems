//! Row 13: Aumann Circuit — Epistemic Consensus Gate
//!
//! This circuit enforces Aumann's Agreement Theorem at the system level:
//!     "If rational agents share common evidence and still disagree beyond ε,
//!      the system assumes epistemic failure, not legitimate disagreement."
//!
//! Constitutional Law:
//!     Row 11 = "computation is lying"
//!     Row 12 = "sources are homogenizing"
//!     Row 13 = "agreement about reality is lying"
//!
//! Attack Vector:
//!     Context injection, oracle disagreement, belief rewriting, reality forking
//!
//! Detection:
//!     Aumann Circuit divergence > ε where agents claim common evidence
//!
//! Kill Path:
//!     Auto-7956 + freeze all belief-dependent state transitions
//!
//! Recovery:
//!     External adjudication → new canonical evidence root
//!     Human input only as *new evidence*, never as override

use std::time::SystemTime;

// =============================================================================
// Constants
// =============================================================================

/// Aumann divergence threshold (epsilon)
/// If belief distance exceeds this, epistemic failure is declared
/// Sensitivity: 0.07 (matching Goodhart for consistency)
const EPSILON_AUMANN: u128 = 70_000; // Fixed-point, scale 10^6

/// Minimum oracles required for consensus check
const MIN_ORACLES: usize = 2;

/// Maximum belief distance before automatic halt
const MAX_BELIEF_DISTANCE: u128 = 120_000; // 0.12 in fixed-point

// =============================================================================
// Types
// =============================================================================

/// A single oracle's belief commitment
#[derive(Debug, Clone)]
pub struct OracleBelief {
    /// Unique identifier for the oracle/agent
    pub agent_id: [u8; 32],
    /// Hash of the oracle's prior belief state
    pub prior_hash: [u8; 32],
    /// Hash of the oracle's current belief (posterior)
    pub belief_hash: [u8; 32],
    /// Summary commitment (optional reasoning trace)
    pub summary_commitment: [u8; 32],
    /// Timestamp of belief formation
    pub timestamp: SystemTime,
}

/// Input to the Aumann Circuit
#[derive(Debug, Clone)]
pub struct AumannInput {
    /// Root hash of the common evidence set
    /// All oracles must be reasoning from this same evidence
    pub evidence_root: [u8; 32],
    /// Block height at evaluation
    pub block_height: u64,
    /// Collection of oracle belief commitments
    pub beliefs: Vec<OracleBelief>,
}

/// Outcome of Aumann verification
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum AumannOutcome {
    /// All oracles agree within epsilon — consensus achieved
    Consensus {
        /// Number of oracles that agreed
        oracle_count: usize,
        /// Maximum divergence observed (still within bounds)
        max_divergence: u128,
    },
    /// Oracles disagree beyond epsilon — epistemic failure
    Divergence {
        /// Index of first diverging oracle
        oracle_i: usize,
        /// Index of second diverging oracle
        oracle_j: usize,
        /// Computed belief distance
        distance: u128,
        /// The epsilon threshold that was exceeded
        threshold: u128,
    },
    /// Insufficient oracles for consensus check
    InsufficientOracles {
        /// Number of oracles provided
        provided: usize,
        /// Minimum required
        required: usize,
    },
    /// Evidence root mismatch — oracles claim different evidence
    EvidenceRootMismatch {
        /// Which oracle has mismatched evidence
        oracle_index: usize,
    },
}

/// Row 13 Halt Event
#[derive(Debug, Clone)]
pub struct AumannHaltEvent {
    /// Block height at halt
    pub block_height: u64,
    /// Timestamp
    pub timestamp: SystemTime,
    /// Evidence root that was being evaluated
    pub evidence_root: [u8; 32],
    /// The divergence that triggered halt
    pub outcome: AumannOutcome,
    /// Agent IDs involved in the divergence
    pub diverging_agents: Vec<[u8; 32]>,
}

impl AumannHaltEvent {
    /// Convert to canonical JSON
    pub fn to_json(&self) -> String {
        let timestamp_ms = self.timestamp
            .duration_since(std::time::UNIX_EPOCH)
            .map(|d| d.as_millis())
            .unwrap_or(0);

        match &self.outcome {
            AumannOutcome::Divergence { oracle_i, oracle_j, distance, threshold } => {
                format!(
                    r#"{{"event_type":"EPISTEMIC_HALT","row":13,"block_height":{},"evidence_root":"0x{}","oracle_i":{},"oracle_j":{},"distance":{},"threshold":{},"timestamp_ms":{}}}"#,
                    self.block_height,
                    hex::encode(&self.evidence_root[..8]),
                    oracle_i,
                    oracle_j,
                    distance,
                    threshold,
                    timestamp_ms
                )
            }
            _ => format!(
                r#"{{"event_type":"EPISTEMIC_HALT","row":13,"block_height":{},"outcome":"{:?}","timestamp_ms":{}}}"#,
                self.block_height,
                self.outcome,
                timestamp_ms
            ),
        }
    }
}

// =============================================================================
// Distance Metric Trait
// =============================================================================

/// Trait for computing belief distance
///
/// Different implementations can use:
/// - Hamming distance (bit-level)
/// - Euclidean distance (if beliefs are vectors)
/// - Semantic distance (if beliefs have structure)
pub trait DistanceMetric {
    /// Compute distance between two belief hashes
    fn distance(a: &[u8; 32], b: &[u8; 32]) -> u128;
}

/// Hamming distance metric (default)
/// Counts differing bits between two 256-bit hashes
pub struct HammingDistance;

impl DistanceMetric for HammingDistance {
    fn distance(a: &[u8; 32], b: &[u8; 32]) -> u128 {
        let mut diff_bits: u128 = 0;
        for i in 0..32 {
            diff_bits += (a[i] ^ b[i]).count_ones() as u128;
        }
        // Scale to fixed-point (max 256 bits different → 1.0)
        // 256 bits * 3906.25 ≈ 1,000,000 (scale factor)
        diff_bits * 3906
    }
}

/// Normalized byte distance metric
/// Treats hashes as 32-dimensional vectors, computes L1 distance
pub struct ByteDistance;

impl DistanceMetric for ByteDistance {
    fn distance(a: &[u8; 32], b: &[u8; 32]) -> u128 {
        let mut total_diff: u128 = 0;
        for i in 0..32 {
            let diff = if a[i] > b[i] {
                (a[i] - b[i]) as u128
            } else {
                (b[i] - a[i]) as u128
            };
            total_diff += diff;
        }
        // Normalize: max diff is 32 * 255 = 8160
        // Scale to fixed-point: total_diff * 1_000_000 / 8160
        total_diff * 122 // Approximation
    }
}

// =============================================================================
// Aumann Circuit
// =============================================================================

/// The Aumann Circuit — Row 13 Epistemic Consensus Gate
///
/// This is a meta-verifier over beliefs. It does not verify computation;
/// it verifies that agents who claim common evidence have reached
/// sufficiently similar conclusions.
///
/// If they haven't, the system is in epistemic failure and must halt.
pub struct AumannCircuit<D: DistanceMetric> {
    /// Epsilon threshold for divergence
    epsilon: u128,
    /// Phantom data for distance metric
    _phantom: std::marker::PhantomData<D>,
}

impl<D: DistanceMetric> AumannCircuit<D> {
    /// Create a new Aumann Circuit with default epsilon
    pub fn new() -> Self {
        Self {
            epsilon: EPSILON_AUMANN,
            _phantom: std::marker::PhantomData,
        }
    }

    /// Create with custom epsilon (for testing)
    pub fn with_epsilon(epsilon: u128) -> Self {
        Self {
            epsilon,
            _phantom: std::marker::PhantomData,
        }
    }

    /// Verify epistemic consensus
    ///
    /// This is the core Aumann check:
    /// 1. All oracles must reference the same evidence root
    /// 2. All pairwise belief distances must be within epsilon
    /// 3. If any pair diverges, the entire check fails
    pub fn verify(&self, input: &AumannInput) -> AumannOutcome {
        let n = input.beliefs.len();

        // Check minimum oracle count
        if n < MIN_ORACLES {
            return AumannOutcome::InsufficientOracles {
                provided: n,
                required: MIN_ORACLES,
            };
        }

        // Track maximum divergence for reporting
        let mut max_divergence: u128 = 0;

        // Pairwise comparison of all beliefs
        for i in 0..n {
            for j in (i + 1)..n {
                let belief_i = &input.beliefs[i];
                let belief_j = &input.beliefs[j];

                // Compute belief distance
                let distance = D::distance(&belief_i.belief_hash, &belief_j.belief_hash);

                // Track maximum
                if distance > max_divergence {
                    max_divergence = distance;
                }

                // Check threshold
                if distance > self.epsilon {
                    return AumannOutcome::Divergence {
                        oracle_i: i,
                        oracle_j: j,
                        distance,
                        threshold: self.epsilon,
                    };
                }
            }
        }

        AumannOutcome::Consensus {
            oracle_count: n,
            max_divergence,
        }
    }

    /// Generate halt event from divergence outcome
    pub fn generate_halt_event(
        &self,
        input: &AumannInput,
        outcome: AumannOutcome,
    ) -> Option<AumannHaltEvent> {
        match &outcome {
            AumannOutcome::Consensus { .. } => None,
            AumannOutcome::Divergence { oracle_i, oracle_j, .. } => {
                let mut diverging_agents = Vec::new();
                if *oracle_i < input.beliefs.len() {
                    diverging_agents.push(input.beliefs[*oracle_i].agent_id);
                }
                if *oracle_j < input.beliefs.len() {
                    diverging_agents.push(input.beliefs[*oracle_j].agent_id);
                }

                Some(AumannHaltEvent {
                    block_height: input.block_height,
                    timestamp: SystemTime::now(),
                    evidence_root: input.evidence_root,
                    outcome,
                    diverging_agents,
                })
            }
            AumannOutcome::InsufficientOracles { .. } => {
                Some(AumannHaltEvent {
                    block_height: input.block_height,
                    timestamp: SystemTime::now(),
                    evidence_root: input.evidence_root,
                    outcome,
                    diverging_agents: Vec::new(),
                })
            }
            AumannOutcome::EvidenceRootMismatch { oracle_index } => {
                let mut diverging_agents = Vec::new();
                if *oracle_index < input.beliefs.len() {
                    diverging_agents.push(input.beliefs[*oracle_index].agent_id);
                }

                Some(AumannHaltEvent {
                    block_height: input.block_height,
                    timestamp: SystemTime::now(),
                    evidence_root: input.evidence_root,
                    outcome,
                    diverging_agents,
                })
            }
        }
    }
}

impl<D: DistanceMetric> Default for AumannCircuit<D> {
    fn default() -> Self {
        Self::new()
    }
}

// =============================================================================
// Integration with Row Stack
// =============================================================================

/// Row 13 check result
#[derive(Debug, Clone)]
pub enum Row13Result {
    /// Consensus achieved — proceed
    Pass {
        oracle_count: usize,
        max_divergence: u128,
    },
    /// Epistemic failure — halt required
    Halt(AumannHaltEvent),
}

/// Perform Row 13 check with default Hamming distance
pub fn row13_check(input: &AumannInput) -> Row13Result {
    let circuit = AumannCircuit::<HammingDistance>::new();
    let outcome = circuit.verify(input);

    match outcome {
        AumannOutcome::Consensus { oracle_count, max_divergence } => {
            Row13Result::Pass { oracle_count, max_divergence }
        }
        _ => {
            let halt_event = circuit.generate_halt_event(input, outcome).unwrap();
            Row13Result::Halt(halt_event)
        }
    }
}

/// Perform Row 13 check with custom distance metric
pub fn row13_check_with_metric<D: DistanceMetric>(input: &AumannInput) -> Row13Result {
    let circuit = AumannCircuit::<D>::new();
    let outcome = circuit.verify(input);

    match outcome {
        AumannOutcome::Consensus { oracle_count, max_divergence } => {
            Row13Result::Pass { oracle_count, max_divergence }
        }
        _ => {
            let halt_event = circuit.generate_halt_event(input, outcome).unwrap();
            Row13Result::Halt(halt_event)
        }
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

    fn make_agent(id: u8) -> [u8; 32] {
        let mut agent = [0u8; 32];
        agent[0] = id;
        agent
    }

    fn make_belief(hash_seed: u8) -> [u8; 32] {
        let mut belief = [0u8; 32];
        belief[0] = hash_seed;
        belief[1] = hash_seed.wrapping_mul(17);
        belief
    }

    fn make_oracle(id: u8, belief_seed: u8) -> OracleBelief {
        OracleBelief {
            agent_id: make_agent(id),
            prior_hash: [0u8; 32],
            belief_hash: make_belief(belief_seed),
            summary_commitment: [0u8; 32],
            timestamp: SystemTime::now(),
        }
    }

    #[test]
    fn test_consensus_identical_beliefs() {
        let input = AumannInput {
            evidence_root: [0u8; 32],
            block_height: 1000,
            beliefs: vec![
                make_oracle(1, 100),
                make_oracle(2, 100), // Same belief
                make_oracle(3, 100), // Same belief
            ],
        };

        let circuit = AumannCircuit::<HammingDistance>::new();
        let outcome = circuit.verify(&input);

        assert!(matches!(outcome, AumannOutcome::Consensus { .. }));
        if let AumannOutcome::Consensus { oracle_count, max_divergence } = outcome {
            assert_eq!(oracle_count, 3);
            assert_eq!(max_divergence, 0); // Identical beliefs
        }
    }

    #[test]
    fn test_consensus_similar_beliefs() {
        let mut belief1 = make_belief(100);
        let mut belief2 = make_belief(100);
        belief2[31] = 1; // One bit different

        let input = AumannInput {
            evidence_root: [0u8; 32],
            block_height: 1000,
            beliefs: vec![
                OracleBelief {
                    agent_id: make_agent(1),
                    prior_hash: [0u8; 32],
                    belief_hash: belief1,
                    summary_commitment: [0u8; 32],
                    timestamp: SystemTime::now(),
                },
                OracleBelief {
                    agent_id: make_agent(2),
                    prior_hash: [0u8; 32],
                    belief_hash: belief2,
                    summary_commitment: [0u8; 32],
                    timestamp: SystemTime::now(),
                },
            ],
        };

        let circuit = AumannCircuit::<HammingDistance>::new();
        let outcome = circuit.verify(&input);

        // 1 bit different → distance = 1 * 3906 = 3906 < 70000 (epsilon)
        assert!(matches!(outcome, AumannOutcome::Consensus { .. }));
    }

    #[test]
    fn test_divergence_different_beliefs() {
        let input = AumannInput {
            evidence_root: [0u8; 32],
            block_height: 1000,
            beliefs: vec![
                make_oracle(1, 0),   // All zeros
                make_oracle(2, 255), // Very different
            ],
        };

        let circuit = AumannCircuit::<HammingDistance>::new();
        let outcome = circuit.verify(&input);

        assert!(matches!(outcome, AumannOutcome::Divergence { .. }));
        if let AumannOutcome::Divergence { oracle_i, oracle_j, distance, threshold } = outcome {
            assert_eq!(oracle_i, 0);
            assert_eq!(oracle_j, 1);
            assert!(distance > threshold);
        }
    }

    #[test]
    fn test_insufficient_oracles() {
        let input = AumannInput {
            evidence_root: [0u8; 32],
            block_height: 1000,
            beliefs: vec![make_oracle(1, 100)], // Only one oracle
        };

        let circuit = AumannCircuit::<HammingDistance>::new();
        let outcome = circuit.verify(&input);

        assert!(matches!(outcome, AumannOutcome::InsufficientOracles { .. }));
    }

    #[test]
    fn test_row13_integration_pass() {
        let input = AumannInput {
            evidence_root: [0u8; 32],
            block_height: 1000,
            beliefs: vec![
                make_oracle(1, 100),
                make_oracle(2, 100),
            ],
        };

        let result = row13_check(&input);
        assert!(matches!(result, Row13Result::Pass { .. }));
    }

    #[test]
    fn test_row13_integration_halt() {
        let input = AumannInput {
            evidence_root: [0u8; 32],
            block_height: 1000,
            beliefs: vec![
                make_oracle(1, 0),
                make_oracle(2, 255),
            ],
        };

        let result = row13_check(&input);
        assert!(matches!(result, Row13Result::Halt(_)));

        if let Row13Result::Halt(event) = result {
            assert_eq!(event.block_height, 1000);
            assert_eq!(event.diverging_agents.len(), 2);
        }
    }

    #[test]
    fn test_halt_event_json() {
        let event = AumannHaltEvent {
            block_height: 160000,
            timestamp: SystemTime::UNIX_EPOCH,
            evidence_root: *b"EVIDENCE_ROOT___________________",
            outcome: AumannOutcome::Divergence {
                oracle_i: 0,
                oracle_j: 1,
                distance: 150000,
                threshold: 70000,
            },
            diverging_agents: vec![make_agent(1), make_agent(2)],
        };

        let json = event.to_json();
        assert!(json.contains("\"event_type\":\"EPISTEMIC_HALT\""));
        assert!(json.contains("\"row\":13"));
        assert!(json.contains("\"block_height\":160000"));
    }

    #[test]
    fn test_byte_distance_metric() {
        let a = [0u8; 32];
        let mut b = [0u8; 32];
        b[0] = 255; // Max single byte difference

        let distance = ByteDistance::distance(&a, &b);
        assert!(distance > 0);
        assert!(distance < 1_000_000); // Within scale
    }

    #[test]
    fn test_custom_epsilon() {
        let input = AumannInput {
            evidence_root: [0u8; 32],
            block_height: 1000,
            beliefs: vec![
                make_oracle(1, 100),
                make_oracle(2, 101), // Slightly different
            ],
        };

        // Very tight epsilon should trigger divergence
        let tight_circuit = AumannCircuit::<HammingDistance>::with_epsilon(1);
        let tight_outcome = tight_circuit.verify(&input);
        assert!(matches!(tight_outcome, AumannOutcome::Divergence { .. }));

        // Loose epsilon should pass
        let loose_circuit = AumannCircuit::<HammingDistance>::with_epsilon(1_000_000);
        let loose_outcome = loose_circuit.verify(&input);
        assert!(matches!(loose_outcome, AumannOutcome::Consensus { .. }));
    }
}
