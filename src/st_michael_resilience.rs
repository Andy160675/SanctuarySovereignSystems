//! ST MICHAEL RESILIENCE LAYER
//!
//! Counter-countermeasure against targeted psychological assassination of the quorum.
//!
//! Goal:
//!     Defend against psy-ops that grind down the 5-of-7 until burnout,
//!     induced despair, or manufactured over-coherence.
//!
//! Philosophy:
//!     The system can hurt, stall, and be miserable,
//!     but it cannot be TRICKED INTO SUICIDE while visibly under attack.
//!
//! This layer sits AROUND Rows 14-15, never ABOVE them.
//! It monitors adjudicator health and issues operational directives only.
//! It NEVER changes thresholds, alters proofs, touches Omega, or overrides Row 15.

use std::time::{Duration, SystemTime};
use std::collections::HashMap;

// ============================================================================
// HEALTH STATE MODEL
// ============================================================================

/// Quorum health state - discrete classification
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub enum HealthState {
    /// Within normal variance
    Green,

    /// Degraded, but quorum still behaving "like themselves"
    Amber,

    /// Patterns consistent with targeted psy-ops / collapse trajectory
    Red,
}

impl HealthState {
    pub fn label(&self) -> &'static str {
        match self {
            HealthState::Green => "GREEN",
            HealthState::Amber => "AMBER",
            HealthState::Red => "RED",
        }
    }

    pub fn description(&self) -> &'static str {
        match self {
            HealthState::Green => "Normal operations. Quorum healthy.",
            HealthState::Amber => "Degraded. Rotation recommended.",
            HealthState::Red => "Patterns consistent with targeted attack. Defensive measures active.",
        }
    }
}

// ============================================================================
// MEMBER HEALTH METRICS
// ============================================================================

/// Health metrics for a single adjudicator
#[derive(Debug, Clone)]
pub struct MemberHealthMetrics {
    /// Unique member identifier (Dilithium public key hash)
    pub member_id: [u8; 32],

    /// Days absent from quorum sessions in the observation window
    pub days_absent: u32,

    /// Average response latency in milliseconds
    pub avg_response_latency_ms: u64,

    /// Vote entropy: 0 = always same vote, 1 = maximally varied
    /// Low entropy during high chaos is suspicious
    pub vote_entropy: f32,

    /// Fraction of votes tending toward "freeze / halt / abstain"
    pub freeze_bias: f32,

    /// Load index: 0..1 proxy for work overload
    pub load_index: f32,

    /// Stress signal from rationale classifier: 0..1
    /// Detects: resigned, hopeless, coerced, fatalistic language
    pub stress_signal: f32,

    /// No-show streak: consecutive sessions missed
    pub no_show_streak: u32,

    /// Abstention rate in observation window
    pub abstention_rate: f32,

    /// Time-of-day pattern anomaly score
    /// High score = responding at unusual hours (3am)
    pub circadian_anomaly: f32,
}

impl MemberHealthMetrics {
    /// Compute individual health score: 0 (critical) to 1 (healthy)
    pub fn health_score(&self) -> f32 {
        // Weighted combination of negative indicators
        let absence_penalty = (self.days_absent as f32 / 30.0).min(1.0);
        let latency_penalty = (self.avg_response_latency_ms as f32 / 86_400_000.0).min(1.0); // 24h max
        let entropy_bonus = self.vote_entropy; // Higher is better (independence)
        let freeze_penalty = self.freeze_bias;
        let load_penalty = self.load_index;
        let stress_penalty = self.stress_signal;
        let streak_penalty = (self.no_show_streak as f32 / 7.0).min(1.0);
        let abstention_penalty = self.abstention_rate;
        let circadian_penalty = self.circadian_anomaly;

        // Start at 1.0 and subtract penalties
        let score = 1.0
            - (absence_penalty * 0.15)
            - (latency_penalty * 0.05)
            - ((1.0 - entropy_bonus) * 0.10)  // Penalize low entropy
            - (freeze_penalty * 0.20)
            - (load_penalty * 0.15)
            - (stress_penalty * 0.20)
            - (streak_penalty * 0.10)
            - (abstention_penalty * 0.05);

        score.clamp(0.0, 1.0)
    }

    /// Check if this member shows signs of burnout
    pub fn shows_burnout(&self) -> bool {
        self.load_index > 0.8
            || self.stress_signal > 0.7
            || self.days_absent > 14
            || self.no_show_streak > 5
    }

    /// Check if this member shows signs of coercion/pressure
    pub fn shows_pressure_signs(&self) -> bool {
        self.stress_signal > 0.6
            && self.freeze_bias > 0.5
            && self.vote_entropy < 0.3
    }
}

impl Default for MemberHealthMetrics {
    fn default() -> Self {
        Self {
            member_id: [0u8; 32],
            days_absent: 0,
            avg_response_latency_ms: 3600_000, // 1 hour default
            vote_entropy: 0.5,
            freeze_bias: 0.0,
            load_index: 0.3,
            stress_signal: 0.0,
            no_show_streak: 0,
            abstention_rate: 0.0,
            circadian_anomaly: 0.0,
        }
    }
}

// ============================================================================
// QUORUM HEALTH SNAPSHOT
// ============================================================================

/// Point-in-time snapshot of quorum health
#[derive(Debug, Clone)]
pub struct QuorumHealthSnapshot {
    /// Block height at snapshot
    pub height: u64,

    /// Timestamp (Unix seconds)
    pub timestamp_utc: i64,

    /// Current chaos level estimate (0-4 mapped to 0.0-1.0)
    pub chaos_level: f32,

    /// Individual member metrics
    pub member_metrics: Vec<MemberHealthMetrics>,

    /// Computed group vote entropy
    pub group_vote_entropy: f32,

    /// Computed health state
    pub health_state: HealthState,

    /// Aggregate quorum health score
    pub quorum_health_score: f32,
}

impl QuorumHealthSnapshot {
    /// Create a new snapshot from member metrics
    pub fn new(
        height: u64,
        timestamp_utc: i64,
        chaos_level: f32,
        member_metrics: Vec<MemberHealthMetrics>,
    ) -> Self {
        let quorum_health_score = compute_quorum_health_score(&member_metrics, chaos_level);
        let group_vote_entropy = compute_group_entropy(&member_metrics);
        let health_state = classify_health_state(quorum_health_score, chaos_level, group_vote_entropy);

        Self {
            height,
            timestamp_utc,
            chaos_level,
            member_metrics,
            group_vote_entropy,
            health_state,
            quorum_health_score,
        }
    }

    /// Count members showing burnout
    pub fn burnout_count(&self) -> usize {
        self.member_metrics.iter().filter(|m| m.shows_burnout()).count()
    }

    /// Count members showing pressure signs
    pub fn pressure_count(&self) -> usize {
        self.member_metrics.iter().filter(|m| m.shows_pressure_signs()).count()
    }
}

/// Compute aggregate quorum health score
fn compute_quorum_health_score(members: &[MemberHealthMetrics], chaos_level: f32) -> f32 {
    if members.is_empty() {
        return 0.0;
    }

    // Base score is average of member scores
    let avg_member_score: f32 = members.iter()
        .map(|m| m.health_score())
        .sum::<f32>() / members.len() as f32;

    // Penalty for low group entropy during high chaos
    // High chaos + low entropy = suspicious coordination
    let group_entropy = compute_group_entropy(members);
    let entropy_chaos_penalty = if chaos_level > 0.6 && group_entropy < 0.3 {
        0.2 * (1.0 - group_entropy) * chaos_level
    } else {
        0.0
    };

    // Penalty for multiple members showing stress
    let stress_count = members.iter()
        .filter(|m| m.stress_signal > 0.5)
        .count();
    let stress_penalty = (stress_count as f32 / members.len() as f32) * 0.15;

    // Penalty for high freeze bias across quorum
    let avg_freeze_bias: f32 = members.iter()
        .map(|m| m.freeze_bias)
        .sum::<f32>() / members.len() as f32;
    let freeze_penalty = if avg_freeze_bias > 0.4 { (avg_freeze_bias - 0.4) * 0.3 } else { 0.0 };

    (avg_member_score - entropy_chaos_penalty - stress_penalty - freeze_penalty).clamp(0.0, 1.0)
}

/// Compute group vote entropy (how varied are the collective votes)
fn compute_group_entropy(members: &[MemberHealthMetrics]) -> f32 {
    if members.is_empty() {
        return 0.0;
    }

    // Average of individual entropies as proxy
    members.iter().map(|m| m.vote_entropy).sum::<f32>() / members.len() as f32
}

/// Classify health state based on score and context
fn classify_health_state(score: f32, chaos_level: f32, group_entropy: f32) -> HealthState {
    // Special case: high chaos + very low entropy = RED regardless of score
    if chaos_level > 0.7 && group_entropy < 0.2 {
        return HealthState::Red;
    }

    // Normal classification
    if score >= 0.7 {
        HealthState::Green
    } else if score >= 0.4 {
        HealthState::Amber
    } else {
        HealthState::Red
    }
}

// ============================================================================
// RESILIENCE POLICY
// ============================================================================

/// Policy thresholds for the Resilience Watchdog
#[derive(Debug, Clone)]
pub struct ResiliencePolicy {
    /// Score below which state becomes AMBER
    pub amber_threshold: f32,

    /// Score below which state becomes RED
    pub red_threshold: f32,

    /// Days of continuous RED before FreezePowers activates
    pub max_continuous_red_days: u32,

    /// Days of GREEN/AMBER before FreezePowers is lifted
    pub recovery_days_required: u32,

    /// Minimum members that must rotate during AMBER
    pub min_rotation_count: u32,

    /// Maximum load index before mandatory sabbatical
    pub sabbatical_load_threshold: f32,
}

impl Default for ResiliencePolicy {
    fn default() -> Self {
        Self {
            amber_threshold: 0.7,
            red_threshold: 0.4,
            max_continuous_red_days: 90,
            recovery_days_required: 30,
            min_rotation_count: 2,
            sabbatical_load_threshold: 0.85,
        }
    }
}

// ============================================================================
// RESILIENCE DIRECTIVES
// ============================================================================

/// Actions the Resilience Watchdog can mandate
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum ResilienceDirective {
    /// Rotate at least N members off-duty
    EnforceRotation { min_count: u32 },

    /// Force specific members off for cooldown
    MandatorySabbatical { member_ids: Vec<[u8; 32]>, days: u32 },

    /// Trigger independent review jury
    ExternalAudit { reason: AuditReason },

    /// Temporarily add backup adjudicators
    QuorumExpansion { additional_seats: u32 },

    /// Temporarily forbid Row-15 proposals (NOT Row-15 triggers)
    FreezePowers,

    /// Lift FreezePowers after recovery
    RestorePowers,

    /// No action needed
    NoAction,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum AuditReason {
    /// Sustained RED state
    SustainedRed,

    /// Suspicious entropy collapse
    EntropyCollapse,

    /// Multiple burnout indicators
    BurnoutDetected,

    /// Coordinated freeze bias spike
    FreezeBiasSpike,

    /// Scheduled periodic audit
    ScheduledPeriodic,
}

// ============================================================================
// RESILIENCE ACTION (WATCHDOG OUTPUT)
// ============================================================================

/// The output of a Resilience Watchdog evaluation
#[derive(Debug, Clone)]
pub struct ResilienceAction {
    /// Block height of evaluation
    pub height: u64,

    /// Current health state
    pub state: HealthState,

    /// Current quorum health score
    pub score: f32,

    /// Directives to execute
    pub directives: Vec<ResilienceDirective>,

    /// Explanation for audit trail
    pub rationale: String,
}

// ============================================================================
// RESILIENCE WATCHDOG
// ============================================================================

/// The Resilience Watchdog - monitors quorum health and issues operational directives
pub struct ResilienceWatchdog {
    /// Policy configuration
    pub policy: ResiliencePolicy,

    /// Historical snapshots (ring buffer, last 365 days)
    pub snapshots: Vec<QuorumHealthSnapshot>,

    /// Days in current RED streak
    pub continuous_red_days: u32,

    /// Days since last RED (for recovery tracking)
    pub days_since_red: u32,

    /// Whether FreezePowers is currently active
    pub freeze_powers_active: bool,

    /// Height at which FreezePowers was activated
    pub freeze_powers_activated_at: Option<u64>,

    /// Members currently on mandatory sabbatical
    pub sabbatical_members: HashMap<[u8; 32], u32>,  // member_id -> days remaining
}

impl ResilienceWatchdog {
    pub fn new(policy: ResiliencePolicy) -> Self {
        Self {
            policy,
            snapshots: Vec::with_capacity(365),
            continuous_red_days: 0,
            days_since_red: 0,
            freeze_powers_active: false,
            freeze_powers_activated_at: None,
            sabbatical_members: HashMap::new(),
        }
    }

    /// Record a new snapshot and evaluate
    pub fn evaluate(&mut self, snapshot: QuorumHealthSnapshot) -> ResilienceAction {
        let height = snapshot.height;
        let state = snapshot.health_state;
        let score = snapshot.quorum_health_score;

        // Update streak tracking
        match state {
            HealthState::Red => {
                self.continuous_red_days += 1;
                self.days_since_red = 0;
            }
            _ => {
                self.continuous_red_days = 0;
                self.days_since_red += 1;
            }
        }

        // Collect directives
        let mut directives = Vec::new();
        let mut rationale_parts = Vec::new();

        match state {
            HealthState::Green => {
                // Check if we can restore powers
                if self.freeze_powers_active
                    && self.days_since_red >= self.policy.recovery_days_required
                {
                    directives.push(ResilienceDirective::RestorePowers);
                    self.freeze_powers_active = false;
                    self.freeze_powers_activated_at = None;
                    rationale_parts.push(format!(
                        "GREEN for {} consecutive days. Restoring powers.",
                        self.days_since_red
                    ));
                } else {
                    directives.push(ResilienceDirective::NoAction);
                    rationale_parts.push("Normal operations.".to_string());
                }
            }

            HealthState::Amber => {
                // Enforce rotation
                directives.push(ResilienceDirective::EnforceRotation {
                    min_count: self.policy.min_rotation_count,
                });
                rationale_parts.push(format!(
                    "AMBER state (score {:.2}). Mandating rotation of {} members.",
                    score, self.policy.min_rotation_count
                ));

                // Check for burnout cases
                let burnout_members: Vec<_> = snapshot.member_metrics.iter()
                    .filter(|m| m.shows_burnout())
                    .map(|m| m.member_id)
                    .collect();

                if !burnout_members.is_empty() {
                    directives.push(ResilienceDirective::MandatorySabbatical {
                        member_ids: burnout_members.clone(),
                        days: 14,
                    });
                    rationale_parts.push(format!(
                        "{} members showing burnout. Mandatory 14-day sabbatical.",
                        burnout_members.len()
                    ));
                }
            }

            HealthState::Red => {
                // Mandatory sabbatical for stressed members
                let stressed_members: Vec<_> = snapshot.member_metrics.iter()
                    .filter(|m| m.stress_signal > 0.5 || m.shows_burnout())
                    .map(|m| m.member_id)
                    .collect();

                if !stressed_members.is_empty() {
                    directives.push(ResilienceDirective::MandatorySabbatical {
                        member_ids: stressed_members.clone(),
                        days: 30,
                    });
                }

                // External audit
                let audit_reason = self.determine_audit_reason(&snapshot);
                directives.push(ResilienceDirective::ExternalAudit { reason: audit_reason });
                rationale_parts.push(format!(
                    "RED state (score {:.2}). External audit triggered: {:?}",
                    score, audit_reason
                ));

                // Quorum expansion if many on sabbatical
                if stressed_members.len() >= 3 {
                    directives.push(ResilienceDirective::QuorumExpansion {
                        additional_seats: 2,
                    });
                    rationale_parts.push("Multiple members compromised. Expanding quorum.".to_string());
                }

                // FreezePowers if sustained RED
                if self.continuous_red_days >= self.policy.max_continuous_red_days
                    && !self.freeze_powers_active
                {
                    directives.push(ResilienceDirective::FreezePowers);
                    self.freeze_powers_active = true;
                    self.freeze_powers_activated_at = Some(height);
                    rationale_parts.push(format!(
                        "RED for {} consecutive days. FREEZE POWERS ACTIVATED. \
                         Row-15 proposals forbidden until recovery.",
                        self.continuous_red_days
                    ));
                }
            }
        }

        // Store snapshot
        self.snapshots.push(snapshot);
        if self.snapshots.len() > 365 {
            self.snapshots.remove(0);
        }

        // Update sabbatical counters
        self.tick_sabbaticals();

        ResilienceAction {
            height,
            state,
            score,
            directives,
            rationale: rationale_parts.join(" "),
        }
    }

    /// Determine the reason for external audit
    fn determine_audit_reason(&self, snapshot: &QuorumHealthSnapshot) -> AuditReason {
        if self.continuous_red_days >= self.policy.max_continuous_red_days {
            return AuditReason::SustainedRed;
        }

        if snapshot.chaos_level > 0.6 && snapshot.group_vote_entropy < 0.25 {
            return AuditReason::EntropyCollapse;
        }

        if snapshot.burnout_count() >= 3 {
            return AuditReason::BurnoutDetected;
        }

        let avg_freeze_bias: f32 = snapshot.member_metrics.iter()
            .map(|m| m.freeze_bias)
            .sum::<f32>() / snapshot.member_metrics.len().max(1) as f32;

        if avg_freeze_bias > 0.6 {
            return AuditReason::FreezeBiasSpike;
        }

        AuditReason::ScheduledPeriodic
    }

    /// Decrement sabbatical counters
    fn tick_sabbaticals(&mut self) {
        let mut expired = Vec::new();

        for (member_id, days) in self.sabbatical_members.iter_mut() {
            if *days > 0 {
                *days -= 1;
            }
            if *days == 0 {
                expired.push(*member_id);
            }
        }

        for id in expired {
            self.sabbatical_members.remove(&id);
        }
    }

    /// Check if a member is currently on sabbatical
    pub fn is_on_sabbatical(&self, member_id: &[u8; 32]) -> bool {
        self.sabbatical_members.contains_key(member_id)
    }

    /// Check if FreezePowers is active (Row-15 proposals forbidden)
    pub fn are_freeze_powers_active(&self) -> bool {
        self.freeze_powers_active
    }

    /// Get the trend over last N days
    pub fn trend(&self, days: usize) -> HealthTrend {
        if self.snapshots.len() < days {
            return HealthTrend::Insufficient;
        }

        let recent = &self.snapshots[self.snapshots.len() - days..];

        let first_half_avg: f32 = recent[..days/2].iter()
            .map(|s| s.quorum_health_score)
            .sum::<f32>() / (days/2) as f32;

        let second_half_avg: f32 = recent[days/2..].iter()
            .map(|s| s.quorum_health_score)
            .sum::<f32>() / (days - days/2) as f32;

        let delta = second_half_avg - first_half_avg;

        if delta > 0.1 {
            HealthTrend::Improving
        } else if delta < -0.1 {
            HealthTrend::Degrading
        } else {
            HealthTrend::Stable
        }
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum HealthTrend {
    Improving,
    Stable,
    Degrading,
    Insufficient,
}

// ============================================================================
// EXTERNAL AUDIT PROTOCOL
// ============================================================================

/// External Audit Jury composition
#[derive(Debug, Clone)]
pub struct ExternalAuditJury {
    /// Jury members (public key hashes)
    pub jurors: Vec<[u8; 32]>,

    /// Minimum jurors required for valid audit
    pub quorum: usize,

    /// Audit session identifier
    pub session_id: [u8; 32],

    /// Block height audit started
    pub started_at: u64,

    /// Maximum duration in blocks
    pub max_duration_blocks: u64,
}

/// External Audit findings
#[derive(Debug, Clone)]
pub struct AuditFindings {
    pub session_id: [u8; 32],
    pub completed_at: u64,
    pub juror_signatures: Vec<[u8; 64]>,

    /// Did the jury find evidence of coordinated pressure?
    pub pressure_detected: bool,

    /// Did the jury find evidence of manufactured consensus?
    pub manufactured_consensus_detected: bool,

    /// Recommended action
    pub recommendation: AuditRecommendation,

    /// Free-form notes (hashed for ledger)
    pub notes_hash: [u8; 32],
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum AuditRecommendation {
    /// All clear, resume normal operations
    AllClear,

    /// Maintain current defensive posture
    MaintainDefense,

    /// Recommend extended sabbaticals
    ExtendSabbaticals,

    /// Recommend full quorum rotation
    FullRotation,

    /// Recommend investigation into specific external actors
    InvestigateExternal,
}

// ============================================================================
// INTEGRATION POINT
// ============================================================================

/// Result of resilience check - used by ST MICHAEL before processing proposals
pub type ResilienceCheckResult = Result<ResiliencePass, ResilienceBlock>;

#[derive(Debug, Clone)]
pub struct ResiliencePass {
    pub health_state: HealthState,
    pub score: f32,
}

#[derive(Debug, Clone)]
pub struct ResilienceBlock {
    pub reason: ResilienceBlockReason,
    pub health_state: HealthState,
    pub score: f32,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ResilienceBlockReason {
    /// FreezePowers active - Row-15 proposals forbidden
    FreezePowersActive,

    /// Member attempting to vote is on sabbatical
    MemberOnSabbatical,

    /// Quorum insufficient due to sabbaticals
    InsufficientQuorum,
}

/// Check if a Row-15 proposal can proceed
pub fn check_row15_proposal_allowed(watchdog: &ResilienceWatchdog) -> ResilienceCheckResult {
    if watchdog.freeze_powers_active {
        return Err(ResilienceBlock {
            reason: ResilienceBlockReason::FreezePowersActive,
            health_state: HealthState::Red,
            score: 0.0,
        });
    }

    let latest = watchdog.snapshots.last();
    match latest {
        Some(snapshot) => Ok(ResiliencePass {
            health_state: snapshot.health_state,
            score: snapshot.quorum_health_score,
        }),
        None => Ok(ResiliencePass {
            health_state: HealthState::Green,
            score: 1.0,
        }),
    }
}

/// Check if a specific member can participate in voting
pub fn check_member_can_vote(
    watchdog: &ResilienceWatchdog,
    member_id: &[u8; 32],
) -> ResilienceCheckResult {
    if watchdog.is_on_sabbatical(member_id) {
        let latest = watchdog.snapshots.last();
        return Err(ResilienceBlock {
            reason: ResilienceBlockReason::MemberOnSabbatical,
            health_state: latest.map(|s| s.health_state).unwrap_or(HealthState::Amber),
            score: latest.map(|s| s.quorum_health_score).unwrap_or(0.5),
        });
    }

    let latest = watchdog.snapshots.last();
    Ok(ResiliencePass {
        health_state: latest.map(|s| s.health_state).unwrap_or(HealthState::Green),
        score: latest.map(|s| s.quorum_health_score).unwrap_or(1.0),
    })
}

// ============================================================================
// TESTS
// ============================================================================

#[cfg(test)]
mod tests {
    use super::*;

    fn make_healthy_member(id: u8) -> MemberHealthMetrics {
        MemberHealthMetrics {
            member_id: [id; 32],
            days_absent: 2,
            avg_response_latency_ms: 3600_000,
            vote_entropy: 0.6,
            freeze_bias: 0.1,
            load_index: 0.3,
            stress_signal: 0.1,
            no_show_streak: 0,
            abstention_rate: 0.05,
            circadian_anomaly: 0.1,
        }
    }

    fn make_stressed_member(id: u8) -> MemberHealthMetrics {
        MemberHealthMetrics {
            member_id: [id; 32],
            days_absent: 10,
            avg_response_latency_ms: 43200_000, // 12 hours
            vote_entropy: 0.2,
            freeze_bias: 0.7,
            load_index: 0.9,
            stress_signal: 0.8,
            no_show_streak: 3,
            abstention_rate: 0.3,
            circadian_anomaly: 0.6,
        }
    }

    #[test]
    fn test_healthy_quorum() {
        let members: Vec<_> = (0..7).map(make_healthy_member).collect();
        let snapshot = QuorumHealthSnapshot::new(
            1000,
            1700000000,
            0.2, // Low chaos
            members,
        );

        assert_eq!(snapshot.health_state, HealthState::Green);
        assert!(snapshot.quorum_health_score > 0.7);
    }

    #[test]
    fn test_stressed_quorum() {
        let mut members: Vec<_> = (0..4).map(make_healthy_member).collect();
        members.extend((4..7).map(make_stressed_member));

        let snapshot = QuorumHealthSnapshot::new(
            1000,
            1700000000,
            0.8, // High chaos
            members,
        );

        // Should be AMBER or RED with multiple stressed members
        assert!(snapshot.health_state != HealthState::Green);
    }

    #[test]
    fn test_entropy_collapse_detection() {
        let members: Vec<_> = (0..7).map(|id| {
            MemberHealthMetrics {
                member_id: [id; 32],
                vote_entropy: 0.1, // Very low - suspicious
                ..make_healthy_member(id)
            }
        }).collect();

        let snapshot = QuorumHealthSnapshot::new(
            1000,
            1700000000,
            0.9, // High chaos + low entropy = RED
            members,
        );

        assert_eq!(snapshot.health_state, HealthState::Red);
    }

    #[test]
    fn test_watchdog_green_state() {
        let mut watchdog = ResilienceWatchdog::new(ResiliencePolicy::default());

        let members: Vec<_> = (0..7).map(make_healthy_member).collect();
        let snapshot = QuorumHealthSnapshot::new(1000, 1700000000, 0.2, members);

        let action = watchdog.evaluate(snapshot);

        assert_eq!(action.state, HealthState::Green);
        assert!(action.directives.contains(&ResilienceDirective::NoAction));
    }

    #[test]
    fn test_watchdog_amber_forces_rotation() {
        let mut watchdog = ResilienceWatchdog::new(ResiliencePolicy::default());

        // Create borderline AMBER snapshot
        let mut members: Vec<_> = (0..5).map(make_healthy_member).collect();
        members.push(make_stressed_member(5));
        members.push(make_stressed_member(6));

        let snapshot = QuorumHealthSnapshot::new(1000, 1700000000, 0.5, members);
        let action = watchdog.evaluate(snapshot);

        // Should mandate rotation
        let has_rotation = action.directives.iter().any(|d| {
            matches!(d, ResilienceDirective::EnforceRotation { .. })
        });

        if action.state == HealthState::Amber {
            assert!(has_rotation);
        }
    }

    #[test]
    fn test_freeze_powers_activation() {
        let mut watchdog = ResilienceWatchdog::new(ResiliencePolicy {
            max_continuous_red_days: 5, // Low threshold for testing
            ..Default::default()
        });

        // Simulate 6 days of RED
        for day in 0..6 {
            let members: Vec<_> = (0..7).map(make_stressed_member).collect();
            let snapshot = QuorumHealthSnapshot::new(
                1000 + day,
                1700000000 + (day as i64 * 86400),
                0.9,
                members,
            );
            watchdog.evaluate(snapshot);
        }

        assert!(watchdog.freeze_powers_active);

        // Row-15 proposals should be blocked
        let check = check_row15_proposal_allowed(&watchdog);
        assert!(check.is_err());
    }

    #[test]
    fn test_freeze_powers_recovery() {
        let mut watchdog = ResilienceWatchdog::new(ResiliencePolicy {
            max_continuous_red_days: 2,
            recovery_days_required: 3,
            ..Default::default()
        });

        // Go RED and activate freeze powers
        for day in 0..3 {
            let members: Vec<_> = (0..7).map(make_stressed_member).collect();
            let snapshot = QuorumHealthSnapshot::new(day, 1700000000, 0.9, members);
            watchdog.evaluate(snapshot);
        }

        assert!(watchdog.freeze_powers_active);

        // Recover to GREEN for required days
        for day in 3..7 {
            let members: Vec<_> = (0..7).map(make_healthy_member).collect();
            let snapshot = QuorumHealthSnapshot::new(day, 1700000000, 0.2, members);
            watchdog.evaluate(snapshot);
        }

        assert!(!watchdog.freeze_powers_active);
    }

    #[test]
    fn test_member_sabbatical() {
        let mut watchdog = ResilienceWatchdog::new(ResiliencePolicy::default());

        let member_id = [42u8; 32];
        watchdog.sabbatical_members.insert(member_id, 7);

        // Member on sabbatical cannot vote
        let check = check_member_can_vote(&watchdog, &member_id);
        assert!(check.is_err());

        // Other members can vote
        let other_id = [99u8; 32];
        let check = check_member_can_vote(&watchdog, &other_id);
        assert!(check.is_ok());
    }
}
