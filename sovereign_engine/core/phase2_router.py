"""
PHASE 2 — Router & Authority Kernel
CSS-ENG-MOD-002 | Sovereign Recursion Engine

Deterministic hierarchical router with operator → innovator → steward escalation.
Ambiguity resolves to halt. Cross-authority calls blocked except via router.
Each authority handler runs in isolation with defined jurisdiction.

Dependency: Phase 0, Phase 1
Invariant: No signal reaches a handler outside its jurisdiction.
Invariant: Ambiguity → halt, never guess.
"""

import re
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Optional
from .phase0_constitution import Constitution, ConstitutionalError
from .phase1_signals import Signal


class AuthorityError(Exception):
    """Raised on authority boundary violations."""
    pass


@dataclass
class RouterStats:
    routed: int = 0
    escalated: int = 0
    halted: int = 0
    ambiguous: int = 0


@dataclass
class RoutingDecision:
    signal_id: str
    signal_type: str
    signal_domain: str
    action: str              # routed | escalated | halt | system_halt | rejected
    target: Optional[str]
    reason: Optional[str]
    handler_result: Optional[dict]
    timestamp: float


class AuthorityHandler:
    """
    Isolated execution context for a single authority level.
    Knows its jurisdiction. Refuses to process signals outside it.
    """

    def __init__(self, level: str, jurisdiction: set[str]):
        self.level = level
        self.jurisdiction = frozenset(jurisdiction)
        self._active = True
        self._processed = 0
        self._handler_fn: Optional[Callable] = None

    def set_handler(self, fn: Callable):
        """Set processing function. Must accept (signal) → {outcome, data?}"""
        if not callable(fn):
            raise ConstitutionalError(f"Handler for {self.level} must be callable")
        self._handler_fn = fn

    def has_jurisdiction(self, signal: Signal) -> bool:
        """Check domain jurisdiction or explicit authority targeting."""
        return signal.domain in self.jurisdiction or signal.authority == self.level

    def process(self, signal: Signal) -> dict:
        """
        Process a signal within jurisdiction.
        Raises on inactive handler, jurisdiction violation, or missing handler.
        """
        if not self._active:
            raise AuthorityError(f"Handler {self.level} is not active")
        if not self.has_jurisdiction(signal):
            raise AuthorityError(
                f"Handler {self.level} has no jurisdiction over "
                f"domain='{signal.domain}' / authority='{signal.authority}'"
            )
        if not self._handler_fn:
            raise AuthorityError(f"Handler {self.level} has no processing function")

        self._processed += 1

        try:
            result = self._handler_fn(signal)
            return {
                "handler": self.level,
                "signal_id": signal.id,
                "outcome": result.get("outcome", "processed"),
                "data": result.get("data"),
                "timestamp": time.time(),
            }
        except Exception as e:
            return {
                "handler": self.level,
                "signal_id": signal.id,
                "outcome": "error",
                "data": {"error": str(e)},
                "timestamp": time.time(),
            }

    def deactivate(self):
        self._active = False

    def activate(self):
        self._active = True

    @property
    def is_active(self) -> bool:
        return self._active

    @property
    def processed_count(self) -> int:
        return self._processed


class Router:
    """
    Deterministic hierarchical router.

    Rules are priority-ordered. First match wins.
    No match → halt (halt doctrine).
    Handler failure → escalate up authority ladder.
    Escalation exhausted → halt.
    """

    def __init__(self, constitution: Constitution):
        self._constitution = constitution
        self._grammar = constitution.get("routing_grammar")
        self._authority_ladder = constitution.get("authority_ladder")
        self._handlers: dict[str, AuthorityHandler] = {}
        self._halted = False
        self._stats = RouterStats()

        # Parse routing rules
        self._rules = [
            {"evaluator": self._parse_condition(r["condition"]),
             "target": r["target"],
             "raw": r["condition"]}
            for r in self._grammar["rules"]
        ]

    def register_handler(self, level: str, handler: AuthorityHandler):
        """Register an authority handler. Level must match handler.level."""
        if not isinstance(handler, AuthorityHandler):
            raise ConstitutionalError(f"Must be AuthorityHandler, got {type(handler)}")
        if handler.level != level:
            raise ConstitutionalError(
                f"Handler level mismatch: registered as '{level}', handler says '{handler.level}'"
            )
        self._handlers[level] = handler

    def route(self, signal: Signal) -> RoutingDecision:
        """
        Route a signal to its target handler.

        INVARIANT: No match → halt.
        INVARIANT: Handler failure → escalate.
        INVARIANT: Escalation exhausted → halt.
        """
        if self._halted:
            return self._decision(signal, "rejected", None, "Router is halted")

        # Find matching rules
        matching = [r for r in self._rules if r["evaluator"](signal)]

        # No match → ambiguity → halt
        if not matching:
            self._stats.ambiguous += 1
            self._stats.halted += 1
            return self._decision(
                signal, "halt", None,
                "No routing rule matched — ambiguity halt"
            )

        target = matching[0]["target"]

        # System signal
        if target == "system":
            return self._handle_system(signal)

        # Try target handler
        handler = self._handlers.get(target)
        if not handler:
            self._stats.halted += 1
            return self._decision(signal, "halt", None, f"No handler for: {target}")

        if not handler.is_active:
            return self._escalate(signal, target, "handler inactive")

        if not handler.has_jurisdiction(signal):
            return self._escalate(signal, target, "jurisdiction mismatch")

        # Route
        self._stats.routed += 1
        signal.routed = True

        try:
            result = handler.process(signal)
            signal.handled = True
            signal.outcome = result["outcome"]
            return self._decision(signal, "routed", target, None, result)
        except Exception as e:
            return self._escalate(signal, target, str(e))

    def _escalate(self, signal: Signal, from_level: str, reason: str) -> RoutingDecision:
        """Escalate up the authority ladder."""
        levels = self._authority_ladder["levels"]
        from_idx = levels.index(from_level) if from_level in levels else -1

        for i in range(from_idx + 1, len(levels)):
            next_level = levels[i]
            handler = self._handlers.get(next_level)

            if handler and handler.is_active:
                self._stats.escalated += 1
                signal.routed = True

                try:
                    result = handler.process(signal)
                    signal.handled = True
                    signal.outcome = result["outcome"]
                    return self._decision(
                        signal, "escalated", next_level,
                        f"Escalated from {from_level}: {reason}",
                        result
                    )
                except Exception:
                    continue  # Try next level

        # Exhausted
        self._stats.halted += 1
        return self._decision(
            signal, "halt", None,
            f"Escalation exhausted from {from_level}: {reason}"
        )

    def _handle_system(self, signal: Signal) -> RoutingDecision:
        if signal.type == "halt":
            self._halted = True
            self._stats.halted += 1
            return self._decision(signal, "system_halt", "system", "Halt signal received")
        return self._decision(signal, "system_processed", "system", None)

    def _decision(
        self, signal, action, target, reason, handler_result=None
    ) -> RoutingDecision:
        return RoutingDecision(
            signal_id=signal.id,
            signal_type=signal.type,
            signal_domain=signal.domain,
            action=action,
            target=target,
            reason=reason,
            handler_result=handler_result,
            timestamp=time.time(),
        )

    def _parse_condition(self, cond_str: str) -> Callable:
        """Parse condition string into evaluator function."""
        def evaluator(signal: Signal) -> bool:
            parts = [p.strip() for p in cond_str.split(" AND ")]
            for part in parts:
                # field == value
                m = re.match(r'^(\w+)\s*==\s*(\w+)$', part)
                if m:
                    f, v = m.group(1), m.group(2)
                    if getattr(signal, f, None) != v:
                        return False
                    continue

                # field != value
                m = re.match(r'^(\w+)\s*!=\s*(\w+)$', part)
                if m:
                    f, v = m.group(1), m.group(2)
                    if getattr(signal, f, None) == v:
                        return False
                    continue

                # Unparseable → no match
                return False
            return True

        return evaluator

    def halt(self, reason: str):
        self._halted = True

    def resume(self):
        self._halted = False

    @property
    def is_halted(self) -> bool:
        return self._halted

    @property
    def stats(self) -> RouterStats:
        return self._stats
