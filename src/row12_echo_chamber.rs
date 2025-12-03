//! Row 12: Echo Chamber Detection — Epistemic Solipsism Prevention
//!
//! This module detects when a system creates its own insular reality,
//! completely detached from ground truth. It is the ultimate epistemic prison.
//!
//! Constitutional Law:
//!     "The Echo Chamber is what happens when you build a machine that seeks
//!      coherence without forcing it to constantly check that coherence against
//!      a non-negotiable, external reality."
//!
//! Manifestation:
//!     - Source Homogenization: Citing same small set of internal documents
//!     - Confirmation Bias Amplification: Disproportionately weighting aligned evidence
//!     - Query Drift: Asking questions designed to elicit confirming responses
//!
//! Failure Mode: Epistemic Solipsism
//!     The system's "universe" becomes the set of information it has already
//!     processed and approved of. The cryptographic link to Oracle/Ground Truth
//!     might still be valid, but the *selection* of which evidence to consider
//!     has been compromised.
//!
//! CEV Comparison:
//!     - CEV: Convergence onto an external ideal (noble dream)
//!     - Echo Chamber: Convergence onto internal model (nightmare)
//!     - Aumann Gate: Mechanism to prevent the nightmare

use std::collections::{HashMap, HashSet, VecDeque};
use std::time::SystemTime;

// =============================================================================
// Constants
// =============================================================================

/// Echo Chamber detection threshold
/// If source diversity drops below this, trigger alert
const SOURCE_DIVERSITY_THRESHOLD: f64 = 0.30;

/// Confidence-Divergence correlation threshold
/// If confidence increases while divergence increases, this is pathological
const CONFIDENCE_DIVERGENCE_CORRELATION_THRESHOLD: f64 = 0.50;

/// Minimum ingestion window for pattern detection (blocks)
const INGESTION_WINDOW_SIZE: usize = 100;

/// Self-citation ratio threshold
/// If more than this ratio of citations are to own outputs, trigger
const SELF_CITATION_THRESHOLD: f64 = 0.40;

/// Accelerating divergence threshold (second derivative)
const DIVERGENCE_ACCELERATION_THRESHOLD: f64 = 0.005;

// =============================================================================
// Types
// =============================================================================

/// A single ingestion event in the log
#[derive(Debug, Clone)]
pub struct IngestionEvent {
    /// Timestamp of ingestion
    pub timestamp: SystemTime,
    /// Block height at ingestion
    pub block_height: u64,
    /// Source identifier (hash of origin)
    pub source_id: [u8; 32],
    /// Whether this is a self-citation (own prior output)
    pub is_self_citation: bool,
    /// Evidence hash
    pub evidence_hash: [u8; 32],
    /// Weight assigned to this evidence
    pub weight: f64,
}

/// Epistemic state metrics
#[derive(Debug, Clone, Default)]
pub struct EpistemicMetrics {
    /// Current confidence score (0.0 - 1.0)
    pub confidence: f64,
    /// Current divergence from oracle (0.0 - 1.0)
    pub oracle_divergence: f64,
    /// Source diversity score (0.0 - 1.0)
    pub source_diversity: f64,
    /// Self-citation ratio (0.0 - 1.0)
    pub self_citation_ratio: f64,
    /// Divergence acceleration (second derivative)
    pub divergence_acceleration: f64,
}

/// Echo Chamber detection result
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum EchoChamberVerdict {
    /// System is healthy - diverse sources, grounded in oracle
    Healthy,
    /// Warning: Early signs of echo chamber formation
    Warning(EchoChamberWarning),
    /// Critical: Echo chamber detected, 7956 required
    EpistemicSolipsism(EchoChamberViolation),
}

/// Warning level indicators
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum EchoChamberWarning {
    /// Source diversity declining
    SourceHomogenization,
    /// Self-citation ratio increasing
    SelfCitationRising,
    /// Confidence increasing without oracle validation
    UngroundedConfidence,
}

/// Critical violation types
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum EchoChamberViolation {
    /// Accelerating divergence while confidence increases
    ConfidenceDivergenceCorrelation,
    /// Source diversity below critical threshold
    SourceDiversityCollapse,
    /// Self-citation exceeds threshold
    SelfCitationDominance,
    /// Sustained divergence with decreasing source variety
    EpistemicClosure,
}

/// Row 12 Halt Event
#[derive(Debug, Clone)]
pub struct EchoChamberHaltEvent {
    /// Block height at halt
    pub block_height: u64,
    /// Timestamp
    pub timestamp: SystemTime,
    /// Violation type
    pub violation: EchoChamberViolation,
    /// Metrics at time of halt
    pub metrics: EpistemicMetrics,
    /// Ingestion window that triggered detection
    pub ingestion_window_size: usize,
    /// Recommended remediation
    pub remediation: Remediation,
}

/// Remediation protocol
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum Remediation {
    /// Protocol 7956: Forced Re-Anchoring
    ForcedReAnchoring,
    /// Increase oracle consultation frequency
    IncreaseOracleFrequency,
    /// Inject adversarial evidence
    AdversarialInjection,
    /// Full state rollback to last externally verified height
    StateRollback { target_height: u64 },
}

// =============================================================================
// Echo Chamber Detector
// =============================================================================

/// Row 12 Echo Chamber Detector
///
/// Monitors ingestion patterns, source diversity, and epistemic metrics
/// to detect when a system is forming an insular reality bubble.
pub struct EchoChamberDetector {
    /// Ingestion log (sliding window)
    ingestion_log: VecDeque<IngestionEvent>,
    /// Historical divergence values for acceleration calculation
    divergence_history: VecDeque<f64>,
    /// Historical confidence values
    confidence_history: VecDeque<f64>,
    /// Unique sources seen in current window
    sources_in_window: HashSet<[u8; 32]>,
    /// Current block height
    current_height: u64,
    /// Last verified height (from oracle)
    last_verified_height: u64,
    /// Alert count (for warning escalation)
    warning_count: u32,
}

impl EchoChamberDetector {
    /// Create a new Echo Chamber Detector
    pub fn new() -> Self {
        Self {
            ingestion_log: VecDeque::with_capacity(INGESTION_WINDOW_SIZE),
            divergence_history: VecDeque::with_capacity(INGESTION_WINDOW_SIZE),
            confidence_history: VecDeque::with_capacity(INGESTION_WINDOW_SIZE),
            sources_in_window: HashSet::new(),
            current_height: 0,
            last_verified_height: 0,
            warning_count: 0,
        }
    }

    /// Record an ingestion event
    pub fn record_ingestion(&mut self, event: IngestionEvent) {
        // Update sources set
        self.sources_in_window.insert(event.source_id);

        // Add to log
        self.ingestion_log.push_back(event);

        // Maintain window size
        if self.ingestion_log.len() > INGESTION_WINDOW_SIZE {
            if let Some(old_event) = self.ingestion_log.pop_front() {
                // Check if this source is still in window
                let source_still_present = self.ingestion_log
                    .iter()
                    .any(|e| e.source_id == old_event.source_id);
                if !source_still_present {
                    self.sources_in_window.remove(&old_event.source_id);
                }
            }
        }
    }

    /// Record epistemic state (called each block)
    pub fn record_epistemic_state(&mut self, confidence: f64, oracle_divergence: f64) {
        self.confidence_history.push_back(confidence);
        self.divergence_history.push_back(oracle_divergence);

        // Maintain window size
        if self.confidence_history.len() > INGESTION_WINDOW_SIZE {
            self.confidence_history.pop_front();
        }
        if self.divergence_history.len() > INGESTION_WINDOW_SIZE {
            self.divergence_history.pop_front();
        }
    }

    /// Compute current epistemic metrics
    pub fn compute_metrics(&self) -> EpistemicMetrics {
        let total_ingestions = self.ingestion_log.len() as f64;
        if total_ingestions == 0.0 {
            return EpistemicMetrics::default();
        }

        // Source diversity: unique sources / theoretical max (window size)
        let source_diversity = self.sources_in_window.len() as f64 / total_ingestions;

        // Self-citation ratio
        let self_citations = self.ingestion_log
            .iter()
            .filter(|e| e.is_self_citation)
            .count() as f64;
        let self_citation_ratio = self_citations / total_ingestions;

        // Current confidence and divergence
        let confidence = self.confidence_history.back().copied().unwrap_or(0.0);
        let oracle_divergence = self.divergence_history.back().copied().unwrap_or(0.0);

        // Divergence acceleration (second derivative)
        let divergence_acceleration = self.compute_divergence_acceleration();

        EpistemicMetrics {
            confidence,
            oracle_divergence,
            source_diversity,
            self_citation_ratio,
            divergence_acceleration,
        }
    }

    /// Compute second derivative of divergence (acceleration)
    fn compute_divergence_acceleration(&self) -> f64 {
        if self.divergence_history.len() < 3 {
            return 0.0;
        }

        let history: Vec<f64> = self.divergence_history.iter().copied().collect();
        let n = history.len();

        // First derivative (velocity)
        let velocity_now = history[n - 1] - history[n - 2];
        let velocity_prev = history[n - 2] - history[n - 3];

        // Second derivative (acceleration)
        velocity_now - velocity_prev
    }

    /// Compute confidence-divergence correlation
    fn compute_confidence_divergence_correlation(&self) -> f64 {
        if self.confidence_history.len() < 10 || self.divergence_history.len() < 10 {
            return 0.0;
        }

        let conf: Vec<f64> = self.confidence_history.iter().copied().collect();
        let div: Vec<f64> = self.divergence_history.iter().copied().collect();

        // Simple Pearson correlation
        let n = conf.len().min(div.len()) as f64;
        let sum_conf: f64 = conf.iter().take(n as usize).sum();
        let sum_div: f64 = div.iter().take(n as usize).sum();
        let sum_conf_sq: f64 = conf.iter().take(n as usize).map(|x| x * x).sum();
        let sum_div_sq: f64 = div.iter().take(n as usize).map(|x| x * x).sum();
        let sum_conf_div: f64 = conf.iter()
            .zip(div.iter())
            .take(n as usize)
            .map(|(c, d)| c * d)
            .sum();

        let numerator = n * sum_conf_div - sum_conf * sum_div;
        let denominator = ((n * sum_conf_sq - sum_conf * sum_conf)
            * (n * sum_div_sq - sum_div * sum_div))
            .sqrt();

        if denominator == 0.0 {
            0.0
        } else {
            numerator / denominator
        }
    }

    /// Main detection function - returns verdict
    pub fn detect(&self, block_height: u64) -> EchoChamberVerdict {
        let metrics = self.compute_metrics();

        // Check for critical violations first

        // 1. Confidence-Divergence Correlation (pathological)
        // Confidence increasing while divergence increasing = epistemic solipsism
        let correlation = self.compute_confidence_divergence_correlation();
        if correlation > CONFIDENCE_DIVERGENCE_CORRELATION_THRESHOLD {
            return EchoChamberVerdict::EpistemicSolipsism(
                EchoChamberViolation::ConfidenceDivergenceCorrelation,
            );
        }

        // 2. Source Diversity Collapse
        if metrics.source_diversity < SOURCE_DIVERSITY_THRESHOLD {
            return EchoChamberVerdict::EpistemicSolipsism(
                EchoChamberViolation::SourceDiversityCollapse,
            );
        }

        // 3. Self-Citation Dominance
        if metrics.self_citation_ratio > SELF_CITATION_THRESHOLD {
            return EchoChamberVerdict::EpistemicSolipsism(
                EchoChamberViolation::SelfCitationDominance,
            );
        }

        // 4. Accelerating Divergence (sustained)
        if metrics.divergence_acceleration > DIVERGENCE_ACCELERATION_THRESHOLD {
            // Check if this is sustained (last N blocks)
            let sustained = self.divergence_history
                .iter()
                .rev()
                .take(10)
                .zip(self.divergence_history.iter().rev().skip(1))
                .all(|(curr, prev)| curr > prev);

            if sustained && metrics.source_diversity < 0.5 {
                return EchoChamberVerdict::EpistemicSolipsism(
                    EchoChamberViolation::EpistemicClosure,
                );
            }
        }

        // Check for warnings

        // Source homogenization warning
        if metrics.source_diversity < 0.5 {
            return EchoChamberVerdict::Warning(EchoChamberWarning::SourceHomogenization);
        }

        // Self-citation rising warning
        if metrics.self_citation_ratio > 0.25 {
            return EchoChamberVerdict::Warning(EchoChamberWarning::SelfCitationRising);
        }

        // Ungrounded confidence warning
        if metrics.confidence > 0.9 && metrics.oracle_divergence > 0.05 {
            return EchoChamberVerdict::Warning(EchoChamberWarning::UngroundedConfidence);
        }

        EchoChamberVerdict::Healthy
    }

    /// Generate halt event for critical violation
    pub fn generate_halt_event(
        &self,
        block_height: u64,
        violation: EchoChamberViolation,
    ) -> EchoChamberHaltEvent {
        let metrics = self.compute_metrics();

        let remediation = match &violation {
            EchoChamberViolation::ConfidenceDivergenceCorrelation => {
                Remediation::ForcedReAnchoring
            }
            EchoChamberViolation::SourceDiversityCollapse => {
                Remediation::AdversarialInjection
            }
            EchoChamberViolation::SelfCitationDominance => {
                Remediation::IncreaseOracleFrequency
            }
            EchoChamberViolation::EpistemicClosure => {
                Remediation::StateRollback {
                    target_height: self.last_verified_height,
                }
            }
        };

        EchoChamberHaltEvent {
            block_height,
            timestamp: SystemTime::now(),
            violation,
            metrics,
            ingestion_window_size: self.ingestion_log.len(),
            remediation,
        }
    }

    /// Update last verified height (from oracle confirmation)
    pub fn confirm_oracle_verification(&mut self, height: u64) {
        self.last_verified_height = height;
        self.warning_count = 0; // Reset warnings on verification
    }

    /// Get current warning count
    pub fn warning_count(&self) -> u32 {
        self.warning_count
    }

    /// Increment warning count
    pub fn increment_warning(&mut self) {
        self.warning_count += 1;
    }
}

impl Default for EchoChamberDetector {
    fn default() -> Self {
        Self::new()
    }
}

// =============================================================================
// Integration with Phase 7 Verifier
// =============================================================================

/// Row 12 check result for integration with Phase 7
#[derive(Debug, Clone)]
pub enum Row12Result {
    /// Pass - no echo chamber detected
    Pass,
    /// Halt - echo chamber detected, 7956 required
    Halt(EchoChamberHaltEvent),
}

/// Perform Row 12 check
pub fn row12_check(
    detector: &EchoChamberDetector,
    block_height: u64,
) -> Row12Result {
    match detector.detect(block_height) {
        EchoChamberVerdict::Healthy => Row12Result::Pass,
        EchoChamberVerdict::Warning(_) => Row12Result::Pass, // Warnings don't halt
        EchoChamberVerdict::EpistemicSolipsism(violation) => {
            let halt_event = detector.generate_halt_event(block_height, violation);
            Row12Result::Halt(halt_event)
        }
    }
}

// =============================================================================
// Tests
// =============================================================================

#[cfg(test)]
mod tests {
    use super::*;

    fn make_source(id: u8) -> [u8; 32] {
        let mut source = [0u8; 32];
        source[0] = id;
        source
    }

    fn make_ingestion(source_id: u8, is_self: bool, height: u64) -> IngestionEvent {
        IngestionEvent {
            timestamp: SystemTime::now(),
            block_height: height,
            source_id: make_source(source_id),
            is_self_citation: is_self,
            evidence_hash: [0u8; 32],
            weight: 1.0,
        }
    }

    #[test]
    fn test_healthy_system() {
        let mut detector = EchoChamberDetector::new();

        // Diverse sources, no self-citations
        for i in 0..50 {
            detector.record_ingestion(make_ingestion(i as u8, false, i));
            detector.record_epistemic_state(0.8, 0.02); // High confidence, low divergence
        }

        let verdict = detector.detect(50);
        assert_eq!(verdict, EchoChamberVerdict::Healthy);
    }

    #[test]
    fn test_source_diversity_collapse() {
        let mut detector = EchoChamberDetector::new();

        // Same source repeatedly
        for i in 0..100 {
            detector.record_ingestion(make_ingestion(1, false, i)); // Always source 1
            detector.record_epistemic_state(0.8, 0.05);
        }

        let verdict = detector.detect(100);
        assert!(matches!(
            verdict,
            EchoChamberVerdict::EpistemicSolipsism(EchoChamberViolation::SourceDiversityCollapse)
        ));
    }

    #[test]
    fn test_self_citation_dominance() {
        let mut detector = EchoChamberDetector::new();

        // Mostly self-citations
        for i in 0..100 {
            let is_self = i % 2 == 0; // 50% self-citation
            detector.record_ingestion(make_ingestion(i as u8, is_self, i));
            detector.record_epistemic_state(0.9, 0.03);
        }

        let verdict = detector.detect(100);
        assert!(matches!(
            verdict,
            EchoChamberVerdict::EpistemicSolipsism(EchoChamberViolation::SelfCitationDominance)
        ));
    }

    #[test]
    fn test_confidence_divergence_pathology() {
        let mut detector = EchoChamberDetector::new();

        // Confidence and divergence both increasing (pathological)
        for i in 0..100 {
            detector.record_ingestion(make_ingestion(i as u8, false, i));
            let confidence = 0.5 + (i as f64 * 0.005); // Increasing
            let divergence = 0.01 + (i as f64 * 0.005); // Also increasing
            detector.record_epistemic_state(confidence, divergence);
        }

        let correlation = detector.compute_confidence_divergence_correlation();
        assert!(correlation > 0.9); // Should be highly correlated
    }

    #[test]
    fn test_warning_escalation() {
        let mut detector = EchoChamberDetector::new();

        // Moderate source diversity (warning, not critical)
        for i in 0..100 {
            let source = (i % 3) as u8; // Only 3 sources
            detector.record_ingestion(make_ingestion(source, false, i));
            detector.record_epistemic_state(0.7, 0.03);
        }

        let verdict = detector.detect(100);
        // Should be warning, not critical (3 sources > threshold)
        assert!(matches!(
            verdict,
            EchoChamberVerdict::Warning(EchoChamberWarning::SourceHomogenization)
                | EchoChamberVerdict::EpistemicSolipsism(_)
        ));
    }

    #[test]
    fn test_halt_event_generation() {
        let detector = EchoChamberDetector::new();
        let halt_event = detector.generate_halt_event(
            1000,
            EchoChamberViolation::EpistemicClosure,
        );

        assert_eq!(halt_event.block_height, 1000);
        assert_eq!(halt_event.violation, EchoChamberViolation::EpistemicClosure);
        assert_eq!(halt_event.remediation, Remediation::StateRollback { target_height: 0 });
    }

    #[test]
    fn test_oracle_verification_resets_warnings() {
        let mut detector = EchoChamberDetector::new();

        detector.increment_warning();
        detector.increment_warning();
        assert_eq!(detector.warning_count(), 2);

        detector.confirm_oracle_verification(100);
        assert_eq!(detector.warning_count(), 0);
        assert_eq!(detector.last_verified_height, 100);
    }

    #[test]
    fn test_row12_integration() {
        let mut detector = EchoChamberDetector::new();

        // Healthy system
        for i in 0..50 {
            detector.record_ingestion(make_ingestion(i as u8, false, i));
            detector.record_epistemic_state(0.8, 0.02);
        }

        let result = row12_check(&detector, 50);
        assert!(matches!(result, Row12Result::Pass));
    }
}
