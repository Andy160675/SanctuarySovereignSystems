"""
Article V: The Escalation Protocol
====================================
Escalation is not ad-hoc. The system state dictates the routing path:
  stable â†’ operator
  degraded â†’ innovator
  constitutional â†’ steward

This makes intuitive or arbitrary escalation impossible.
"""

from __future__ import annotations
from dataclasses import dataclass
from tools.sovereign_stack.engine.signals.typed_signal import (
    TypedSignal, AuthorityLevel, SystemState, SignalType, create_signal,
)
from tools.sovereign_stack.engine.feedback.feedback_log import FeedbackLog, LogEntry


@dataclass(frozen=True)
class EscalationDecision:
    """Record of an escalation decision â€” immutable evidence."""
    from_state: SystemState
    to_state: SystemState
    trigger_signal_id: str
    resolved_authority: AuthorityLevel
    reason: str


class EscalationProtocol:
    """
    Deterministic escalation engine.
    State transitions follow strict rules â€” no intuition permitted.
    """

    # Valid state transitions (current â†’ allowed next states)
    VALID_TRANSITIONS = {
        SystemState.STABLE: {SystemState.STABLE, SystemState.DEGRADED},
        SystemState.DEGRADED: {SystemState.STABLE, SystemState.DEGRADED, SystemState.CONSTITUTIONAL},
        SystemState.CONSTITUTIONAL: {SystemState.DEGRADED, SystemState.CONSTITUTIONAL},
    }

    STATE_AUTHORITY = {
        SystemState.STABLE: AuthorityLevel.OPERATOR,
        SystemState.DEGRADED: AuthorityLevel.INNOVATOR,
        SystemState.CONSTITUTIONAL: AuthorityLevel.STEWARD,
    }

    def __init__(self, feedback_log: FeedbackLog):
        self._current_state = SystemState.STABLE
        self._feedback_log = feedback_log
        self._history: list[EscalationDecision] = []

    @property
    def current_state(self) -> SystemState:
        return self._current_state

    @property
    def current_authority(self) -> AuthorityLevel:
        return self.STATE_AUTHORITY[self._current_state]

    def escalate(
        self, target_state: SystemState, trigger: TypedSignal, reason: str
    ) -> EscalationDecision:
        """
        Attempt a state transition. Only valid transitions are permitted.
        Invalid transitions trigger containment (Axiom II).
        """
        valid_targets = self.VALID_TRANSITIONS.get(self._current_state, set())

        if target_state not in valid_targets:
            decision = EscalationDecision(
                from_state=self._current_state,
                to_state=self._current_state,  # No change â€” containment
                trigger_signal_id=trigger.signal_id,
                resolved_authority=self.current_authority,
                reason=f"BLOCKED: invalid transition {self._current_state.value} â†’ {target_state.value}",
            )
        else:
            previous = self._current_state
            self._current_state = target_state
            decision = EscalationDecision(
                from_state=previous,
                to_state=target_state,
                trigger_signal_id=trigger.signal_id,
                resolved_authority=self.STATE_AUTHORITY[target_state],
                reason=reason,
            )

        self._history.append(decision)
        self._feedback_log.append(LogEntry(
            signal_type="ESCALATION",
            route_target=decision.resolved_authority.value,
            handler="escalation_protocol",
            outcome="TRANSITIONED" if decision.from_state != decision.to_state else "CONTAINED",
            reason=decision.reason,
            evidence_hash=trigger.evidence_hash,
        ))

        return decision

    def de_escalate(self, trigger: TypedSignal, reason: str) -> EscalationDecision:
        """
        Step down one level. Constitutional â†’ Degraded â†’ Stable.
        Cannot de-escalate from Stable.
        """
        de_escalation_map = {
            SystemState.CONSTITUTIONAL: SystemState.DEGRADED,
            SystemState.DEGRADED: SystemState.STABLE,
            SystemState.STABLE: SystemState.STABLE,
        }
        target = de_escalation_map[self._current_state]
        return self.escalate(target, trigger, reason)

