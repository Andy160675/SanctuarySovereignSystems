"""
Article IX: The Default Safe Failure State
============================================
Any component or process that fails does so in a halt state.
There is no silent fall-through. The system prefers inaction
to incorrect action.

This makes ambiguous or unsafe failure modes impossible.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum, auto
from typing import Callable, Optional, TypeVar, Any
from engine.feedback.feedback_log import FeedbackLog, LogEntry

T = TypeVar("T")


class FailureClass(Enum):
    """Classification of failure severity."""
    PROCESS_BLOCK = auto()      # Operation bypassed a gate — halt operation
    TRANSACTION_HOLD = auto()   # Authority violation — hold in escrow
    KERNEL_PANIC = auto()       # Axiom violation — system-wide halt


@dataclass(frozen=True)
class FailureRecord:
    """Immutable record of a failure event."""
    failure_class: FailureClass
    component: str
    reason: str
    signal_id: str
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    resolved: bool = False


class SafeFailure:
    """
    Constitutional failure handler.
    All failures result in explicit halt states — never silent pass-through.
    """

    def __init__(self, feedback_log: FeedbackLog):
        self._feedback_log = feedback_log
        self._failure_history: list[FailureRecord] = []
        self._halted: bool = False
        self._halt_reason: str = ""

    @property
    def is_halted(self) -> bool:
        return self._halted

    @property
    def halt_reason(self) -> str:
        return self._halt_reason

    def process_block(self, component: str, reason: str, signal_id: str) -> FailureRecord:
        """Article IX: Block a specific process."""
        record = FailureRecord(
            failure_class=FailureClass.PROCESS_BLOCK,
            component=component,
            reason=reason,
            signal_id=signal_id,
        )
        self._record_failure(record)
        return record

    def transaction_hold(self, component: str, reason: str, signal_id: str) -> FailureRecord:
        """Article IX: Hold a transaction in escrow."""
        record = FailureRecord(
            failure_class=FailureClass.TRANSACTION_HOLD,
            component=component,
            reason=reason,
            signal_id=signal_id,
        )
        self._record_failure(record)
        return record

    def kernel_panic(self, component: str, reason: str, signal_id: str) -> FailureRecord:
        """Article IX: System-wide halt. Requires operator intervention."""
        record = FailureRecord(
            failure_class=FailureClass.KERNEL_PANIC,
            component=component,
            reason=reason,
            signal_id=signal_id,
        )
        self._halted = True
        self._halt_reason = f"KERNEL_PANIC: {component} — {reason}"
        self._record_failure(record)
        return record

    def safe_execute(
        self,
        fn: Callable[..., T],
        component: str,
        signal_id: str,
        *args: Any,
        **kwargs: Any,
    ) -> Optional[T]:
        """
        Execute a function with safe failure wrapping.
        On exception → process_block, return None.
        """
        if self._halted:
            self.process_block(component, "system_halted", signal_id)
            return None
        try:
            return fn(*args, **kwargs)
        except Exception as e:
            self.process_block(component, str(e), signal_id)
            return None

    def _record_failure(self, record: FailureRecord) -> None:
        """Log the failure — Axiom I: immutable evidence."""
        self._failure_history.append(record)
        self._feedback_log.append(LogEntry(
            signal_type="FAILURE",
            route_target=record.failure_class.name,
            handler="safe_failure",
            outcome=record.failure_class.name,
            reason=record.reason,
            evidence_hash=record.signal_id,
        ))
