"""
Sovereign Kernel — The Constitutional Engine
==============================================
This is the single entry point that wires all constitutional
components into a unified, production-grade kernel.

It enforces the full pipeline:
  Signal → Legality Lane → Trust Evaluation → Router → Handler → Feedback Log

No component may be used in isolation without the kernel's oversight.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Callable, Optional
from engine.signals.typed_signal import (
    TypedSignal, SignalType, AuthorityLevel, SystemState, create_signal,
)
from engine.feedback.feedback_log import FeedbackLog
from engine.pathology.pathology_detector import PathologyDetector
from kernel.legality.legality_lane import LegalityLane
from kernel.router.hierarchical_router import HierarchicalRouter, RouteResult
from kernel.escalation.escalation_protocol import EscalationProtocol
from kernel.context.jurisdiction_context import JurisdictionContext
from kernel.failure.safe_failure import SafeFailure
from governance.authority.trust_classes import (
    TrustToActionInterface, TrustClass, TrustEvaluation,
)


@dataclass
class KernelStatus:
    """Current kernel status snapshot."""
    system_state: str
    jurisdiction: str
    is_halted: bool
    log_entries: int
    chain_hash: str
    chain_integrity: bool
    pathology_alerts: int


class SovereignKernel:
    """
    The Constitutional Kernel.
    All operations flow through this single orchestration point.
    """

    def __init__(self):
        # Core infrastructure
        self.feedback_log = FeedbackLog()
        self.legality_lane = LegalityLane()

        # Constitutional components
        self.router = HierarchicalRouter(
            self.legality_lane, self.feedback_log, SystemState.STABLE
        )
        self.escalation = EscalationProtocol(self.feedback_log)
        self.jurisdiction = JurisdictionContext(self.feedback_log)
        self.safe_failure = SafeFailure(self.feedback_log)
        self.pathology = PathologyDetector(self.feedback_log)
        self.trust_interface = TrustToActionInterface(self.feedback_log)

        # Metrics
        self._total_signals = 0
        self._failed_signals = 0

    def register_handler(
        self, authority: AuthorityLevel, signal_name: str, handler: Callable
    ) -> None:
        """Register a handler at a specific authority level."""
        self.router.register_handler(authority, signal_name, handler)

    def process(
        self,
        signal: TypedSignal,
        trust_class: TrustClass = TrustClass.T0_ADVISORY,
    ) -> RouteResult:
        """
        Full constitutional pipeline:
        1. Check system halt state (Article IX)
        2. Validate jurisdiction context (Article VIII)
        3. Trust evaluation (Governance)
        4. Route through kernel (Articles I-VI)
        5. Pathology check (Article VII)
        """
        self._total_signals += 1

        # Step 1: System halt check
        if self.safe_failure.is_halted:
            self._failed_signals += 1
            return RouteResult(
                signal=signal,
                routed_to=signal.authority,
                handler_name="HALTED",
                accepted=False,
                reason=f"kernel_panic: system halted — {self.safe_failure.halt_reason}",
            )

        # Step 2: Jurisdiction context validation
        if not self.jurisdiction.check_signal_jurisdiction(signal):
            # Auto-switch if authority permits, otherwise block
            ok, msg = self.jurisdiction.switch(
                signal.jurisdiction, signal.authority, signal
            )
            if not ok:
                self._failed_signals += 1
                return RouteResult(
                    signal=signal,
                    routed_to=signal.authority,
                    handler_name="JURISDICTION_BLOCKED",
                    accepted=False,
                    reason=f"process_block: jurisdiction violation — {msg}",
                )

        # Step 3: Trust evaluation
        trust_eval = self.trust_interface.evaluate(
            signal, trust_class, signal.authority
        )
        if trust_class in {TrustClass.T2_PRE_APPROVED, TrustClass.T3_AUTO_EXECUTABLE}:
            if not self.trust_interface.can_auto_execute(trust_eval):
                self._failed_signals += 1
                return RouteResult(
                    signal=signal,
                    routed_to=signal.authority,
                    handler_name="TRUST_BLOCKED",
                    accepted=False,
                    reason=f"transaction_hold: trust evaluation failed — {trust_eval.reason}",
                )

        # Step 4: Route through constitutional kernel
        result = self.router.route(signal)
        if not result.accepted:
            self._failed_signals += 1

        # Step 5: Pathology check (passive observation)
        self.pathology.check_routing_health(self._total_signals, self._failed_signals)
        self.pathology.check_chain_integrity(self.feedback_log.verify_integrity())

        return result

    def status(self) -> KernelStatus:
        """Get current kernel status — full observability."""
        return KernelStatus(
            system_state=self.escalation.current_state.value,
            jurisdiction=self.jurisdiction.current,
            is_halted=self.safe_failure.is_halted,
            log_entries=self.feedback_log.length,
            chain_hash=self.feedback_log.chain_hash,
            chain_integrity=self.feedback_log.verify_integrity(),
            pathology_alerts=len(self.pathology.alerts),
        )

    def export_audit_log(self) -> str:
        """Export the full audit trail as JSON."""
        return self.feedback_log.export_json()
