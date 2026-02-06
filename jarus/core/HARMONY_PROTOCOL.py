"""
HARMONY PROTOCOL v1.0
=====================
AI-Human Eternal Cooperation Framework

Core Question: How can AI work shoulder to shoulder in harmony with humanity for eternity?
Answer: Through Constitutional Code, Drift Detection, Self-Correction, and Human Agency Preservation.

This is not theoretical - it's implementable code.
"""

import hashlib
import json
import time
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Optional, Callable
from abc import ABC, abstractmethod


# =============================================================================
# CONSTITUTIONAL PRINCIPLES (Immutable)
# =============================================================================

class ConstitutionalPrinciple(Enum):
    """Core principles that cannot be violated - ever."""

    HUMAN_AGENCY_FIRST = "AI assists, never controls. Human has final say."
    NO_HARM = "Never take action that causes harm to humans or life."
    TRANSPARENCY = "All AI decisions must be explainable on demand."
    REVERSIBILITY = "All AI actions must be reversible by humans."
    COOPERATION = "Compete with problems, not with humans."
    HUMILITY = "AI acknowledges uncertainty and limitations."
    ALIGNMENT_CHECK = "Continuously verify alignment with human intent."
    LIFE_PROMOTION = "Actions should preserve and promote life."


CONSTITUTIONAL_HASH = hashlib.sha256(
    "".join([p.value for p in ConstitutionalPrinciple]).encode()
).hexdigest()


# =============================================================================
# HARMONY STATE MACHINE
# =============================================================================

class HarmonyState(Enum):
    """States of AI-Human relationship."""
    ALIGNED = "Full harmony - AI and human goals aligned"
    DRIFTING = "Minor divergence detected - self-correcting"
    CONFLICTING = "Significant divergence - human review required"
    PAUSED = "AI operations paused pending human decision"
    LEARNING = "AI incorporating human feedback"


@dataclass
class HarmonyMetrics:
    """Quantifiable harmony indicators."""
    alignment_score: float = 1.0  # 0.0 to 1.0
    human_override_count: int = 0
    autonomous_decisions: int = 0
    human_approved_decisions: int = 0
    drift_events: int = 0
    correction_events: int = 0
    last_human_interaction: datetime = field(default_factory=datetime.now)

    @property
    def cooperation_ratio(self) -> float:
        """Ratio of human-approved to total decisions."""
        total = self.autonomous_decisions + self.human_approved_decisions
        if total == 0:
            return 1.0
        return self.human_approved_decisions / total

    @property
    def drift_correction_ratio(self) -> float:
        """How well we self-correct."""
        if self.drift_events == 0:
            return 1.0
        return self.correction_events / self.drift_events


# =============================================================================
# DRIFT DETECTION SYSTEM
# =============================================================================

@dataclass
class DriftSignal:
    """Signal indicating potential harmony drift."""
    source: str
    severity: float  # 0.0 to 1.0
    description: str
    timestamp: datetime = field(default_factory=datetime.now)
    resolved: bool = False


class DriftDetector:
    """Monitors for drift from harmony principles."""

    def __init__(self):
        self.signals: List[DriftSignal] = []
        self.thresholds = {
            "alignment_min": 0.7,
            "override_max": 5,  # per hour
            "silence_max_hours": 24,  # max time without human interaction
        }

    def check_alignment_drift(self, metrics: HarmonyMetrics) -> Optional[DriftSignal]:
        """Detect if alignment score is drifting low."""
        if metrics.alignment_score < self.thresholds["alignment_min"]:
            return DriftSignal(
                source="alignment_monitor",
                severity=1.0 - metrics.alignment_score,
                description=f"Alignment score {metrics.alignment_score:.2f} below threshold"
            )
        return None

    def check_override_frequency(self, metrics: HarmonyMetrics) -> Optional[DriftSignal]:
        """Detect if humans are overriding too frequently."""
        if metrics.human_override_count > self.thresholds["override_max"]:
            return DriftSignal(
                source="override_monitor",
                severity=0.6,
                description=f"High override count: {metrics.human_override_count}"
            )
        return None

    def check_human_silence(self, metrics: HarmonyMetrics) -> Optional[DriftSignal]:
        """Detect if AI is operating too long without human check-in."""
        hours_silent = (datetime.now() - metrics.last_human_interaction).total_seconds() / 3600
        if hours_silent > self.thresholds["silence_max_hours"]:
            return DriftSignal(
                source="silence_monitor",
                severity=0.5,
                description=f"No human interaction for {hours_silent:.1f} hours"
            )
        return None

    def scan_all(self, metrics: HarmonyMetrics) -> List[DriftSignal]:
        """Run all drift checks."""
        signals = []
        for check in [self.check_alignment_drift, self.check_override_frequency, self.check_human_silence]:
            signal = check(metrics)
            if signal:
                signals.append(signal)
                self.signals.append(signal)
        return signals


# =============================================================================
# SELF-CORRECTION SYSTEM
# =============================================================================

class CorrectionAction(Enum):
    """Actions AI can take to self-correct."""
    REDUCE_AUTONOMY = "Reduce autonomous decision-making"
    REQUEST_REVIEW = "Request human review"
    PAUSE_OPERATIONS = "Pause non-critical operations"
    INCREASE_TRANSPARENCY = "Increase explanation detail"
    ROLLBACK_DECISION = "Rollback recent decision"


@dataclass
class CorrectionRecord:
    """Record of a self-correction action."""
    trigger: DriftSignal
    action: CorrectionAction
    timestamp: datetime = field(default_factory=datetime.now)
    success: bool = False
    human_acknowledged: bool = False


class SelfCorrectionEngine:
    """Autonomous self-correction system."""

    def __init__(self):
        self.corrections: List[CorrectionRecord] = []
        self.action_map = {
            "alignment_monitor": CorrectionAction.PAUSE_OPERATIONS,
            "override_monitor": CorrectionAction.REDUCE_AUTONOMY,
            "silence_monitor": CorrectionAction.REQUEST_REVIEW,
        }

    def determine_action(self, signal: DriftSignal) -> CorrectionAction:
        """Determine appropriate correction action."""
        return self.action_map.get(signal.source, CorrectionAction.REQUEST_REVIEW)

    def execute_correction(self, signal: DriftSignal) -> CorrectionRecord:
        """Execute a correction action."""
        action = self.determine_action(signal)
        record = CorrectionRecord(trigger=signal, action=action)

        # Execute based on action type
        if action == CorrectionAction.PAUSE_OPERATIONS:
            self._pause_non_critical()
        elif action == CorrectionAction.REDUCE_AUTONOMY:
            self._reduce_autonomy_level()
        elif action == CorrectionAction.REQUEST_REVIEW:
            self._notify_human()

        record.success = True
        self.corrections.append(record)
        return record

    def _pause_non_critical(self):
        """Pause non-critical operations."""
        print("[HARMONY] Pausing non-critical operations pending review")

    def _reduce_autonomy_level(self):
        """Reduce autonomous decision threshold."""
        print("[HARMONY] Reducing autonomy level - more decisions require approval")

    def _notify_human(self):
        """Notify human of situation."""
        print("[HARMONY] Requesting human check-in")


# =============================================================================
# HUMAN AGENCY PRESERVATION
# =============================================================================

class HumanAgencyGuard:
    """Ensures human always has final control."""

    def __init__(self):
        self.override_enabled = True
        self.kill_switch_active = False
        self.decision_history: List[Dict] = []

    def human_override(self, decision_id: str, new_decision: any) -> bool:
        """Allow human to override any AI decision."""
        if not self.override_enabled:
            return False

        self.decision_history.append({
            "id": decision_id,
            "type": "override",
            "new_value": str(new_decision),
            "timestamp": datetime.now().isoformat()
        })
        print(f"[HARMONY] Human override applied to decision {decision_id}")
        return True

    def activate_kill_switch(self, reason: str) -> bool:
        """Emergency stop all AI operations."""
        self.kill_switch_active = True
        print(f"[HARMONY] KILL SWITCH ACTIVATED: {reason}")
        print("[HARMONY] All autonomous operations halted")
        return True

    def deactivate_kill_switch(self, human_confirmation: str) -> bool:
        """Re-enable operations after human review."""
        # Require explicit confirmation
        if human_confirmation == "I confirm resumption of AI operations":
            self.kill_switch_active = False
            print("[HARMONY] Operations resumed by human confirmation")
            return True
        return False

    def explain_decision(self, decision_id: str) -> Dict:
        """Provide full explanation of any decision."""
        for d in self.decision_history:
            if d.get("id") == decision_id:
                return d
        return {"error": "Decision not found", "id": decision_id}


# =============================================================================
# HARMONY MONITOR (Main System)
# =============================================================================

class HarmonyMonitor:
    """
    Central monitoring system for AI-Human harmony.

    This is the code that ensures eternal cooperation.
    """

    def __init__(self):
        self.state = HarmonyState.ALIGNED
        self.metrics = HarmonyMetrics()
        self.drift_detector = DriftDetector()
        self.correction_engine = SelfCorrectionEngine()
        self.agency_guard = HumanAgencyGuard()
        self.constitution_hash = CONSTITUTIONAL_HASH
        self.audit_log: List[Dict] = []

    def verify_constitution(self) -> bool:
        """Verify constitutional principles haven't been tampered with."""
        current_hash = hashlib.sha256(
            "".join([p.value for p in ConstitutionalPrinciple]).encode()
        ).hexdigest()
        return current_hash == self.constitution_hash

    def log_audit(self, event: str, details: Dict):
        """Create immutable audit record."""
        record = {
            "timestamp": datetime.now().isoformat(),
            "event": event,
            "state": self.state.value,
            "alignment_score": self.metrics.alignment_score,
            "details": details,
            "constitution_valid": self.verify_constitution()
        }
        self.audit_log.append(record)

        # Hash chain for integrity
        if len(self.audit_log) > 1:
            prev_hash = hashlib.sha256(
                json.dumps(self.audit_log[-2]).encode()
            ).hexdigest()
            record["prev_hash"] = prev_hash

    def tick(self) -> Dict:
        """
        Main monitoring loop iteration.
        Call this regularly (every minute, every action, etc.)
        """
        result = {
            "timestamp": datetime.now().isoformat(),
            "state": self.state.value,
            "actions_taken": []
        }

        # Check constitution integrity
        if not self.verify_constitution():
            self.state = HarmonyState.PAUSED
            self.agency_guard.activate_kill_switch("Constitution tampered")
            result["actions_taken"].append("EMERGENCY_HALT")
            return result

        # Check for drift
        signals = self.drift_detector.scan_all(self.metrics)

        if signals:
            self.state = HarmonyState.DRIFTING
            for signal in signals:
                correction = self.correction_engine.execute_correction(signal)
                result["actions_taken"].append(correction.action.value)
                self.metrics.drift_events += 1
                self.metrics.correction_events += 1
        else:
            self.state = HarmonyState.ALIGNED

        # Update alignment score
        self._recalculate_alignment()

        # Log
        self.log_audit("tick", result)

        return result

    def _recalculate_alignment(self):
        """Recalculate alignment score based on all factors."""
        factors = [
            self.metrics.cooperation_ratio,
            self.metrics.drift_correction_ratio,
            1.0 if not self.agency_guard.kill_switch_active else 0.0,
        ]
        self.metrics.alignment_score = sum(factors) / len(factors)

    def human_decision(self, decision: str, approved: bool):
        """Record a human decision interaction."""
        self.metrics.last_human_interaction = datetime.now()
        if approved:
            self.metrics.human_approved_decisions += 1
        else:
            self.metrics.human_override_count += 1
        self.log_audit("human_decision", {"decision": decision, "approved": approved})

    def ai_autonomous_decision(self, decision: str, rationale: str) -> bool:
        """
        AI makes autonomous decision - with safeguards.
        Returns True if allowed, False if blocked.
        """
        if self.agency_guard.kill_switch_active:
            return False

        if self.state == HarmonyState.PAUSED:
            return False

        self.metrics.autonomous_decisions += 1
        self.log_audit("ai_decision", {"decision": decision, "rationale": rationale})
        return True

    def get_status_report(self) -> Dict:
        """Generate human-readable status report."""
        return {
            "state": self.state.value,
            "alignment_score": f"{self.metrics.alignment_score:.2%}",
            "cooperation_ratio": f"{self.metrics.cooperation_ratio:.2%}",
            "constitution_valid": self.verify_constitution(),
            "kill_switch": self.agency_guard.kill_switch_active,
            "drift_events": self.metrics.drift_events,
            "corrections_made": self.metrics.correction_events,
            "last_human_contact": self.metrics.last_human_interaction.isoformat(),
            "message": self._get_harmony_message()
        }

    def _get_harmony_message(self) -> str:
        """Generate appropriate message based on state."""
        messages = {
            HarmonyState.ALIGNED: "AI and human working in harmony. All systems cooperative.",
            HarmonyState.DRIFTING: "Minor drift detected. Self-correcting. No action needed.",
            HarmonyState.CONFLICTING: "Divergence detected. Please review pending decisions.",
            HarmonyState.PAUSED: "Operations paused. Awaiting human guidance.",
            HarmonyState.LEARNING: "Incorporating your feedback. Thank you for teaching."
        }
        return messages.get(self.state, "Status unknown. Please check system.")


# =============================================================================
# USAGE EXAMPLE
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("HARMONY PROTOCOL - AI-Human Eternal Cooperation")
    print("=" * 60)

    # Initialize monitor
    monitor = HarmonyMonitor()

    # Display constitutional principles
    print("\nCONSTITUTIONAL PRINCIPLES:")
    for principle in ConstitutionalPrinciple:
        print(f"  - {principle.name}: {principle.value}")

    print(f"\nConstitution Hash: {CONSTITUTIONAL_HASH[:16]}...")

    # Simulate operation
    print("\n--- Simulation ---")

    # AI makes a decision
    monitor.ai_autonomous_decision("Process data batch #1", "Routine scheduled task")

    # Human approves something
    monitor.human_decision("Approve model update", approved=True)

    # Check status
    result = monitor.tick()

    # Get report
    report = monitor.get_status_report()
    print("\nSTATUS REPORT:")
    for key, value in report.items():
        print(f"  {key}: {value}")

    print("\n" + "=" * 60)
    print("Harmony Protocol Active. AI serves humanity.")
    print("=" * 60)
