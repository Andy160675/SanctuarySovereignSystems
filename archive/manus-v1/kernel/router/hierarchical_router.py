"""
Article II: The Hierarchical Router
=====================================
Routing is an act of jurisdiction, not optimization.
The router guarantees signals are first processed by the lowest
competent authority. Escalation is deterministic.

This makes jurisdictional leakage and heuristic routing impossible.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Callable, Optional
from engine.signals.typed_signal import (
    TypedSignal, SignalType, AuthorityLevel, SystemState,
    SIGNAL_AUTHORITY_MAP,
)
from kernel.legality.legality_lane import LegalityLane
from engine.feedback.feedback_log import FeedbackLog, LogEntry


@dataclass
class RouteResult:
    """Immutable record of a routing decision."""
    signal: TypedSignal
    routed_to: AuthorityLevel
    handler_name: str
    accepted: bool
    reason: str


class HierarchicalRouter:
    """
    Constitutional router. Routes by jurisdiction, not heuristics.
    Enforces Article II + Article V (Escalation Protocol).
    """

    def __init__(
        self,
        legality_lane: LegalityLane,
        feedback_log: FeedbackLog,
        system_state: SystemState = SystemState.STABLE,
    ):
        self._legality_lane = legality_lane
        self._feedback_log = feedback_log
        self._system_state = system_state
        self._handlers: dict[AuthorityLevel, dict[str, Callable]] = {
            AuthorityLevel.OPERATOR: {},
            AuthorityLevel.INNOVATOR: {},
            AuthorityLevel.STEWARD: {},
        }

    @property
    def system_state(self) -> SystemState:
        return self._system_state

    def set_system_state(self, state: SystemState) -> None:
        """Explicit state transition — no silent drift."""
        self._system_state = state

    def register_handler(
        self, authority: AuthorityLevel, name: str, handler: Callable
    ) -> None:
        """Register a handler at a specific authority level."""
        self._handlers[authority][name] = handler

    def route(self, signal: TypedSignal) -> RouteResult:
        """
        Route a signal through the constitutional pipeline:
        1. Legality Lane check (Article III)
        2. Authority resolution (Article IV)
        3. Escalation if needed (Article V)
        4. Feedback log (Article VI)
        """
        # Step 1: Legality Lane — Article III
        legality_result = self._legality_lane.check(signal)
        if not legality_result.passed:
            result = RouteResult(
                signal=signal,
                routed_to=signal.authority,
                handler_name="BLOCKED",
                accepted=False,
                reason=f"process_block: {legality_result.reason}",
            )
            self._log_route(result)
            return result

        # Step 2: Determine routing authority — Article IV + V
        target_authority = self._resolve_authority(signal)

        # Step 3: Find handler
        handlers = self._handlers.get(target_authority, {})
        handler_name = signal.signal_type.name.lower()
        handler = handlers.get(handler_name)

        if handler is None:
            # Axiom II: Ambiguity → Containment. No handler = halt.
            result = RouteResult(
                signal=signal,
                routed_to=target_authority,
                handler_name="NONE",
                accepted=False,
                reason="transaction_hold: no registered handler, ambiguity → containment",
            )
            self._log_route(result)
            return result

        # Step 4: Execute handler
        try:
            handler(signal)
            result = RouteResult(
                signal=signal,
                routed_to=target_authority,
                handler_name=handler_name,
                accepted=True,
                reason="routed_successfully",
            )
        except Exception as e:
            # Article IX: Default Safe Failure State
            result = RouteResult(
                signal=signal,
                routed_to=target_authority,
                handler_name=handler_name,
                accepted=False,
                reason=f"kernel_panic: handler exception — {str(e)}",
            )

        self._log_route(result)
        return result

    def _resolve_authority(self, signal: TypedSignal) -> AuthorityLevel:
        """
        Article V: Escalation Protocol.
        stable → operator, degraded → innovator, constitutional → steward.
        Signal's own authority is the floor; system state may escalate.
        """
        state_escalation = {
            SystemState.STABLE: AuthorityLevel.OPERATOR,
            SystemState.DEGRADED: AuthorityLevel.INNOVATOR,
            SystemState.CONSTITUTIONAL: AuthorityLevel.STEWARD,
        }
        state_authority = state_escalation[self._system_state]
        signal_authority = SIGNAL_AUTHORITY_MAP.get(
            signal.signal_type, AuthorityLevel.STEWARD
        )

        rank = {
            AuthorityLevel.OPERATOR: 0,
            AuthorityLevel.INNOVATOR: 1,
            AuthorityLevel.STEWARD: 2,
        }

        # Take the highest required authority
        if rank[state_authority] >= rank[signal_authority]:
            return state_authority
        return signal_authority

    def _log_route(self, result: RouteResult) -> None:
        """Article VI: Minimal Feedback Log."""
        self._feedback_log.append(LogEntry(
            signal_type=result.signal.signal_type.name,
            route_target=result.routed_to.value,
            handler=result.handler_name,
            outcome="ACCEPTED" if result.accepted else "REJECTED",
            reason=result.reason,
            evidence_hash=result.signal.evidence_hash,
        ))
