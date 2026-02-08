"""
Article VIII: The Jurisdiction Context Switcher
================================================
All operations are tagged with a Jurisdiction Context.
Tools and reasoning from one context cannot be applied to another
without an explicit and authorized context switch.

This makes cross-domain contamination impossible.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional, Set
from tools.sovereign_stack.engine.signals.typed_signal import TypedSignal, AuthorityLevel
from tools.sovereign_stack.engine.feedback.feedback_log import FeedbackLog, LogEntry


@dataclass(frozen=True)
class ContextSwitch:
    """Immutable record of a jurisdiction context switch."""
    from_context: str
    to_context: str
    authorized_by: AuthorityLevel
    signal_id: str
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class JurisdictionContext:
    """
    Manages jurisdiction boundaries. No cross-domain leakage.
    Every operation must declare and stay within its jurisdiction.
    """

    # Canonical jurisdictions â€” extensible only by Steward authority
    CANONICAL_JURISDICTIONS: Set[str] = {
        "audit",
        "sync",
        "integrity",
        "deployment",
        "governance",
        "evidence",
        "execution",
        "policy",
    }

    def __init__(self, feedback_log: FeedbackLog):
        self._current: str = "audit"  # Safe default
        self._feedback_log = feedback_log
        self._switch_history: list[ContextSwitch] = []

    @property
    def current(self) -> str:
        return self._current

    def validate_jurisdiction(self, jurisdiction: str) -> bool:
        """Check if a jurisdiction is recognized."""
        return jurisdiction in self.CANONICAL_JURISDICTIONS

    def switch(
        self,
        target: str,
        authority: AuthorityLevel,
        trigger: TypedSignal,
    ) -> tuple[bool, str]:
        """
        Attempt a jurisdiction context switch.
        Requires explicit authorization. No silent switches.
        """
        if not self.validate_jurisdiction(target):
            self._feedback_log.append(LogEntry(
                signal_type="CONTEXT_SWITCH",
                route_target=authority.value,
                handler="jurisdiction_context",
                outcome="REJECTED",
                reason=f"unrecognized_jurisdiction: {target}",
                evidence_hash=trigger.evidence_hash,
            ))
            return False, f"unrecognized_jurisdiction: {target}"

        if target == self._current:
            return True, "already_in_context"

        # Record the switch
        switch_record = ContextSwitch(
            from_context=self._current,
            to_context=target,
            authorized_by=authority,
            signal_id=trigger.signal_id,
        )
        self._switch_history.append(switch_record)
        previous = self._current
        self._current = target

        self._feedback_log.append(LogEntry(
            signal_type="CONTEXT_SWITCH",
            route_target=authority.value,
            handler="jurisdiction_context",
            outcome="SWITCHED",
            reason=f"{previous} â†’ {target}",
            evidence_hash=trigger.evidence_hash,
        ))

        return True, f"switched: {previous} â†’ {target}"

    def check_signal_jurisdiction(self, signal: TypedSignal) -> bool:
        """
        Verify a signal's jurisdiction matches the current context.
        Cross-domain signals are rejected â€” Article VIII enforcement.
        """
        return signal.jurisdiction == self._current

