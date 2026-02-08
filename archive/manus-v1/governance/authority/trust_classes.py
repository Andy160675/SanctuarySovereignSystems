"""
Trust-to-Action Interface
==========================
Governance bridge from verified artifacts to production execution.
Four Trust Classes enforce graduated autonomy under constitutional law.

T0: ADVISORY    — Manual Only. Human decides, human executes.
T1: CONDITIONAL — Auto-check, Manual trigger. System recommends, human approves.
T2: PRE_APPROVED — Automatic within bounds. System executes within pre-defined limits.
T3: AUTO_EXECUTABLE — Immediate autonomous response. Defense-grade automation.

Every trust class evaluation is a mandatory step before ledger entry.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum, auto
from typing import Callable, Optional, Any
from engine.signals.typed_signal import TypedSignal, AuthorityLevel
from engine.feedback.feedback_log import FeedbackLog, LogEntry


class TrustClass(Enum):
    """Four graduated trust levels for autonomous execution."""
    T0_ADVISORY = 0         # Manual only
    T1_CONDITIONAL = 1      # Auto-check, manual trigger
    T2_PRE_APPROVED = 2     # Automatic within bounds
    T3_AUTO_EXECUTABLE = 3  # Immediate autonomous response


# Trust class → minimum authority required to assign
TRUST_AUTHORITY_MAP = {
    TrustClass.T0_ADVISORY: AuthorityLevel.OPERATOR,
    TrustClass.T1_CONDITIONAL: AuthorityLevel.OPERATOR,
    TrustClass.T2_PRE_APPROVED: AuthorityLevel.INNOVATOR,
    TrustClass.T3_AUTO_EXECUTABLE: AuthorityLevel.STEWARD,
}


@dataclass(frozen=True)
class TrustEvaluation:
    """Immutable record of a trust class evaluation."""
    signal_id: str
    assigned_class: TrustClass
    evaluated_by: AuthorityLevel
    approved: bool
    reason: str
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class TrustToActionInterface:
    """
    Mandatory governance gate before any action reaches the ledger.
    No signal may bypass trust evaluation.
    """

    def __init__(self, feedback_log: FeedbackLog):
        self._feedback_log = feedback_log
        self._evaluations: list[TrustEvaluation] = []
        self._action_bounds: dict[str, dict] = {}

    def set_action_bounds(self, action_name: str, bounds: dict) -> None:
        """Define pre-approved execution bounds for T2 actions."""
        self._action_bounds[action_name] = bounds

    def evaluate(
        self,
        signal: TypedSignal,
        requested_class: TrustClass,
        evaluator_authority: AuthorityLevel,
    ) -> TrustEvaluation:
        """
        Evaluate whether a signal meets the requested trust class.
        This is a MANDATORY step — no bypass permitted.
        """
        # Check: Does the evaluator have sufficient authority?
        required_authority = TRUST_AUTHORITY_MAP[requested_class]
        authority_rank = {
            AuthorityLevel.OPERATOR: 0,
            AuthorityLevel.INNOVATOR: 1,
            AuthorityLevel.STEWARD: 2,
        }

        if authority_rank[evaluator_authority] < authority_rank[required_authority]:
            evaluation = TrustEvaluation(
                signal_id=signal.signal_id,
                assigned_class=TrustClass.T0_ADVISORY,  # Downgrade to safest
                evaluated_by=evaluator_authority,
                approved=False,
                reason=f"insufficient_authority: need {required_authority.value} for {requested_class.name}",
            )
        else:
            evaluation = TrustEvaluation(
                signal_id=signal.signal_id,
                assigned_class=requested_class,
                evaluated_by=evaluator_authority,
                approved=True,
                reason=f"trust_class_assigned: {requested_class.name}",
            )

        self._evaluations.append(evaluation)
        self._feedback_log.append(LogEntry(
            signal_type="TRUST_EVALUATION",
            route_target=evaluator_authority.value,
            handler="trust_to_action",
            outcome="APPROVED" if evaluation.approved else "DOWNGRADED",
            reason=evaluation.reason,
            evidence_hash=signal.evidence_hash,
        ))

        return evaluation

    def can_auto_execute(self, evaluation: TrustEvaluation) -> bool:
        """Check if an evaluated signal may auto-execute."""
        if not evaluation.approved:
            return False
        return evaluation.assigned_class in {
            TrustClass.T2_PRE_APPROVED,
            TrustClass.T3_AUTO_EXECUTABLE,
        }

    def requires_manual_trigger(self, evaluation: TrustEvaluation) -> bool:
        """Check if an evaluated signal requires human approval."""
        return evaluation.assigned_class in {
            TrustClass.T0_ADVISORY,
            TrustClass.T1_CONDITIONAL,
        }
