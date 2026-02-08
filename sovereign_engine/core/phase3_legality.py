"""
PHASE 3 — Legality Gate & Impossible-State Eliminator
CSS-ENG-MOD-003 | Sovereign Recursion Engine

Validates signals against constitutional legality constraints BEFORE routing.
Illegal states are terminated here — they never reach execution handlers.
Implements the subtractive operator: observe → validate → pass/terminate.

Dependency: Phase 0, Phase 1
Invariant: No illegal state exists downstream of this gate.
Invariant: Every termination emits a containment event.
"""

import time
from dataclasses import dataclass, field
from typing import Callable, Optional
from .phase0_constitution import Constitution, ConstitutionalError
from .phase1_signals import Signal, SignalFactory


@dataclass
class Violation:
    rule: str
    reason: str


@dataclass
class ContainmentEvent:
    signal_id: str
    signal_type: str
    signal_domain: str
    violations: list[Violation]
    action: str = "terminated"
    timestamp: float = 0.0

    def __post_init__(self):
        if self.timestamp == 0.0:
            self.timestamp = time.time()


@dataclass
class LegalityResult:
    legal: bool
    signal: Optional[Signal] = None
    violations: list[Violation] = field(default_factory=list)
    containment: Optional[ContainmentEvent] = None


@dataclass
class GateStats:
    checked: int = 0
    passed: int = 0
    terminated: int = 0


class LegalityGate:
    """
    Pre-routing legality validator.
    
    Signals must pass ALL checks to proceed.
    Any failure → termination + containment event.
    Conservative: rule evaluation errors count as violations.
    """

    def __init__(self, constitution: Constitution, factory: SignalFactory):
        self._constitution = constitution
        self._factory = factory
        self._forbidden = frozenset(
            constitution.get("legality_constraints")["forbidden_states"]
        )
        self._custom_rules: list[tuple[str, Callable]] = []
        self._containment_log: list[ContainmentEvent] = []
        self._stats = GateStats()

    def add_rule(self, name: str, check_fn: Callable):
        """
        Add a domain-specific legality rule.
        check_fn(signal, context) → (legal: bool, reason: str)
        """
        self._custom_rules.append((name, check_fn))

    def check(self, signal: Signal, context: Optional[dict] = None) -> LegalityResult:
        """
        Check signal against all legality constraints.
        
        INVARIANT: Any violation → signal terminated.
        INVARIANT: Every termination → containment event.
        """
        ctx = context or {}
        self._stats.checked += 1
        violations: list[Violation] = []

        # 1. Schema validation
        valid, errors = self._factory.validate(signal)
        if not valid:
            violations.append(Violation("schema_validation", "; ".join(errors)))

        # 2. Integrity
        if not signal.verify_integrity():
            violations.append(Violation(
                "integrity_verification",
                "Hash mismatch — possible tampering"
            ))

        # 3. Structural forbidden states
        self._check_forbidden(signal, ctx, violations)

        # 4. Custom rules
        for name, check_fn in self._custom_rules:
            try:
                legal, reason = check_fn(signal, ctx)
                if not legal:
                    violations.append(Violation(name, reason or "Custom rule violation"))
            except Exception as e:
                violations.append(Violation(name, f"Rule evaluation error: {e}"))

        # Decision
        if violations:
            self._stats.terminated += 1
            event = ContainmentEvent(
                signal_id=signal.id,
                signal_type=signal.type,
                signal_domain=signal.domain,
                violations=violations,
            )
            self._containment_log.append(event)
            return LegalityResult(legal=False, violations=violations, containment=event)

        self._stats.passed += 1
        return LegalityResult(legal=True, signal=signal)

    def _check_forbidden(self, signal: Signal, ctx: dict, violations: list):
        """Check structural forbidden states from constitution."""

        # Untyped signal
        if not signal.type and "untyped_signal_in_router" in self._forbidden:
            violations.append(Violation(
                "untyped_signal_in_router",
                "Signal has no type"
            ))

        # Cross-authority direct call
        src = ctx.get("source_authority")
        tgt = ctx.get("target_authority")
        if (src and tgt and src != tgt and
                not ctx.get("via_router") and
                "cross_authority_direct_call" in self._forbidden):
            violations.append(Violation(
                "cross_authority_direct_call",
                f"Direct call from {src} to {tgt} — must use router"
            ))

        # Execution after halt
        if (ctx.get("system_halted") and signal.type != "halt" and
                "execution_after_halt_signal" in self._forbidden):
            violations.append(Violation(
                "execution_after_halt_signal",
                "System halted — only halt signals may pass"
            ))

        # Silent escalation (no source)
        if (signal.type == "escalation" and not signal.source and
                "silent_authority_escalation" in self._forbidden):
            violations.append(Violation(
                "silent_authority_escalation",
                "Escalation without declared source"
            ))

        # Steward override without dual key
        if (ctx.get("steward_override") and not ctx.get("dual_key") and
                "steward_override_without_dual_key" in self._forbidden):
            violations.append(Violation(
                "steward_override_without_dual_key",
                "Steward override requires dual-key authorisation"
            ))

    @property
    def containment_log(self) -> list[ContainmentEvent]:
        return list(self._containment_log)

    @property
    def stats(self) -> GateStats:
        return self._stats
