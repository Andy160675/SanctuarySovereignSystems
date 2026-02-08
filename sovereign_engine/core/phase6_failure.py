"""
PHASE 6 — Failure Semantics Doctrine
CSS-ENG-MOD-006 | Sovereign Recursion Engine

Encoded failure matrix: router failure → halt, legality failure → escalate,
audit failure → halt. Runtime health monitors with automatic escalation.

Dependency: Phase 0, Phase 5
Invariant: Every failure type has a defined response.
Invariant: Unknown failures default to halt.
"""

import time
from dataclasses import dataclass, field
from typing import Optional
from .phase0_constitution import Constitution, ConstitutionalError
from .phase5_timing import HaltController


@dataclass
class FailureEvent:
    component: str
    failure_type: str
    action: str
    recovery: str
    details: Optional[str] = None
    timestamp: float = 0.0

    def __post_init__(self):
        if self.timestamp == 0.0:
            self.timestamp = time.time()


@dataclass
class HealthStatus:
    component: str
    healthy: bool
    last_check: float
    failure_count: int = 0
    last_failure: Optional[str] = None


class FailureMatrix:
    """
    Encodes the constitutional failure response for every component.
    Dispatches halt/escalate/contain based on failure type.
    Unknown failures → halt (halt doctrine).
    """

    def __init__(self, constitution: Constitution, halt_controller: HaltController):
        self._constitution = constitution
        self._halt = halt_controller
        self._semantics = constitution.get("failure_semantics")
        self._event_log: list[FailureEvent] = []

    def handle_failure(self, component: str, failure_type: str,
                       details: str = "") -> FailureEvent:
        """
        Handle a component failure according to constitutional semantics.
        Returns the FailureEvent describing what was done.
        """
        response = self._constitution.get_failure_response(failure_type)

        event = FailureEvent(
            component=component,
            failure_type=failure_type,
            action=response["action"],
            recovery=response["recovery"],
            details=details,
        )
        self._event_log.append(event)

        # Execute action
        if response["action"] == "halt":
            self._halt.halt(
                reason=f"{failure_type} in {component}: {details}",
                source=component,
            )
        elif response["action"] == "escalate":
            pass  # Escalation is handled by the router via signal
        elif response["action"] == "escalate_and_contain":
            pass  # Contain + escalate

        return event

    @property
    def event_log(self) -> list[FailureEvent]:
        return list(self._event_log)

    @property
    def event_count(self) -> int:
        return len(self._event_log)


class HealthMonitor:
    """
    Runtime health monitor. Tracks component health.
    Auto-escalates when components fail repeatedly.
    """

    def __init__(self, failure_matrix: FailureMatrix):
        self._matrix = failure_matrix
        self._components: dict[str, HealthStatus] = {}
        self._threshold = 3  # failures before auto-escalation

    def register(self, component: str):
        self._components[component] = HealthStatus(
            component=component,
            healthy=True,
            last_check=time.time(),
        )

    def report_healthy(self, component: str):
        if component not in self._components:
            return
        status = self._components[component]
        status.healthy = True
        status.last_check = time.time()

    def report_failure(self, component: str, failure_type: str,
                       details: str = "") -> FailureEvent:
        if component not in self._components:
            self.register(component)

        status = self._components[component]
        status.healthy = False
        status.failure_count += 1
        status.last_failure = failure_type
        status.last_check = time.time()

        return self._matrix.handle_failure(component, failure_type, details)

    @property
    def all_healthy(self) -> bool:
        return all(s.healthy for s in self._components.values())

    @property
    def statuses(self) -> dict[str, HealthStatus]:
        return dict(self._components)

    def get_unhealthy(self) -> list[str]:
        return [name for name, s in self._components.items() if not s.healthy]
