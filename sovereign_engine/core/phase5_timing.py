"""
PHASE 5 — Timing & Halt Enforcement
CSS-ENG-MOD-005 | Sovereign Recursion Engine

Routing latency contracts. Watchdog heartbeat.
Ambiguity or audit failure → containment halt.
Restart validates ledger before reopening routing.

Dependency: Phase 0, Phase 4
Invariant: Routing exceeding timing contract → escalation.
Invariant: Watchdog failure → halt.
"""

import time
from dataclasses import dataclass
from typing import Callable, Optional
from .phase0_constitution import Constitution, ConstitutionalError


@dataclass
class TimingBreach:
    component: str
    contract_ms: int
    actual_ms: float
    timestamp: float


class TimingEnforcer:
    """
    Enforces timing contracts on routing and subsystem operations.
    Tracks breaches. Triggers escalation or halt on violation.
    """

    def __init__(self, constitution: Constitution):
        self._contracts = constitution.get("timing_contracts")
        self._breaches: list[TimingBreach] = []

    def measure(self, component: str, contract_key: str, fn: Callable, *args, **kwargs):
        """
        Execute fn and check against timing contract.
        Returns (result, breach_or_none).
        """
        max_ms = self._contracts.get(contract_key)
        if max_ms is None:
            raise ConstitutionalError(f"No timing contract: {contract_key}")

        start = time.perf_counter()
        result = fn(*args, **kwargs)
        elapsed_ms = (time.perf_counter() - start) * 1000

        if elapsed_ms > max_ms:
            breach = TimingBreach(
                component=component,
                contract_ms=max_ms,
                actual_ms=round(elapsed_ms, 2),
                timestamp=time.time(),
            )
            self._breaches.append(breach)
            return result, breach

        return result, None

    @property
    def breaches(self) -> list[TimingBreach]:
        return list(self._breaches)

    @property
    def breach_count(self) -> int:
        return len(self._breaches)


@dataclass
class WatchdogState:
    component: str
    last_heartbeat: float
    alive: bool = True


class Watchdog:
    """
    Heartbeat monitor for subsystems.
    Components must check in within the watchdog interval.
    Missed heartbeats → halt signal.
    """

    def __init__(self, constitution: Constitution):
        self._interval_ms = constitution.get_timing("watchdog_interval_ms")
        self._components: dict[str, WatchdogState] = {}
        self._halt_triggered = False

    def register(self, component: str):
        """Register a component for monitoring."""
        self._components[component] = WatchdogState(
            component=component,
            last_heartbeat=time.time(),
        )

    def heartbeat(self, component: str):
        """Record a heartbeat from a component."""
        if component not in self._components:
            raise ConstitutionalError(f"Unknown component: {component}")
        self._components[component].last_heartbeat = time.time()
        self._components[component].alive = True

    def check(self) -> list[str]:
        """
        Check all components. Returns list of dead components.
        Dead = no heartbeat within interval.
        """
        now = time.time()
        threshold_s = self._interval_ms / 1000.0
        dead = []

        for name, state in self._components.items():
            if (now - state.last_heartbeat) > threshold_s:
                state.alive = False
                dead.append(name)

        return dead

    @property
    def all_alive(self) -> bool:
        return all(s.alive for s in self._components.values())

    @property
    def states(self) -> dict[str, WatchdogState]:
        return dict(self._components)


class HaltController:
    """
    Centralised halt coordination.
    Any subsystem can trigger halt. Resume requires ledger validation.
    """

    def __init__(self):
        self._halted = False
        self._halt_reason: Optional[str] = None
        self._halt_time: Optional[float] = None
        self._halt_history: list[dict] = []

    def halt(self, reason: str, source: str = "unknown"):
        """Trigger system halt."""
        self._halted = True
        self._halt_reason = reason
        self._halt_time = time.time()
        self._halt_history.append({
            "reason": reason,
            "source": source,
            "timestamp": self._halt_time,
        })

    def resume(self, ledger_valid: bool) -> dict:
        """
        Resume after halt. REQUIRES ledger validation.
        
        INVARIANT: Cannot resume with invalid ledger.
        """
        if not ledger_valid:
            return {
                "resumed": False,
                "reason": "Ledger validation failed — cannot resume",
            }
        self._halted = False
        self._halt_reason = None
        return {"resumed": True, "timestamp": time.time()}

    @property
    def is_halted(self) -> bool:
        return self._halted

    @property
    def halt_reason(self) -> Optional[str]:
        return self._halt_reason

    @property
    def halt_history(self) -> list[dict]:
        return list(self._halt_history)
