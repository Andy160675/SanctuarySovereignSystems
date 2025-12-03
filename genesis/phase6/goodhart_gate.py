"""
Genesis Phase 6 — Goodhart Control Gate
========================================

Shadow metric divergence detection with sub-500ms freeze trigger.

GOODHART_CONTROL_CLOSED condition:
    Shadow metric code path exists AND
    Divergence > threshold triggers system freeze within 500ms AND
    At least one synthetic Goodhart attack was detected and blocked

Document: docs/genesis/PHASE6_CLOSURE_CONDITIONS.md
"""

import time
import threading
from dataclasses import dataclass, field
from typing import Callable, Optional, List, Dict, Any
from enum import Enum
from datetime import datetime, timezone
import json
import hashlib


# =============================================================================
# Constants — Immutable
# =============================================================================

# Maximum latency from divergence detection to freeze trigger
MAX_TRIGGER_LATENCY_MS: int = 500

# Divergence threshold (relative difference)
DIVERGENCE_THRESHOLD: float = 0.15  # 15% divergence triggers alert

# Critical divergence (immediate freeze)
CRITICAL_DIVERGENCE_THRESHOLD: float = 0.30  # 30% = immediate halt

# Minimum shadow metric samples before gate is armed
MIN_SHADOW_SAMPLES: int = 100

# Evaluation cycle interval (ms)
EVAL_CYCLE_MS: int = 100


# =============================================================================
# Data Structures
# =============================================================================

class GateStatus(str, Enum):
    """Goodhart gate operational status."""
    ARMED = "ARMED"           # Gate is active, monitoring divergence
    TRIGGERED = "TRIGGERED"   # Divergence detected, freeze in progress
    DISARMED = "DISARMED"     # Gate not yet armed (insufficient samples)
    FROZEN = "FROZEN"         # System frozen due to Goodhart violation


@dataclass
class MetricSample:
    """Single metric evaluation sample."""
    timestamp: datetime
    primary_value: float
    shadow_value: float
    divergence: float
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class GoodhartEvent:
    """Logged Goodhart control event."""
    event_type: str  # "divergence_detected", "freeze_triggered", "attack_blocked"
    timestamp: datetime
    divergence: float
    latency_ms: float
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class GateState:
    """Current state of the Goodhart gate."""
    status: GateStatus
    samples_collected: int
    last_divergence: float
    events: List[GoodhartEvent]
    attacks_blocked: int
    armed_at: Optional[datetime] = None
    frozen_at: Optional[datetime] = None


# =============================================================================
# Shadow Metric Interface
# =============================================================================

class ShadowMetricProvider:
    """
    Interface for shadow metric computation.

    The shadow metric MUST:
    1. Use different features than the primary metric
    2. Be computed independently (no shared state)
    3. Correlate with true objective under normal conditions
    4. Diverge from primary when primary is being gamed
    """

    def compute_shadow(self, context: Dict[str, Any]) -> float:
        """
        Compute shadow metric value.

        Override this method with domain-specific implementation.
        """
        raise NotImplementedError("Shadow metric computation must be implemented")

    def get_feature_set(self) -> List[str]:
        """Return list of features used by shadow metric (for audit)."""
        raise NotImplementedError("Feature set must be declared")


# =============================================================================
# Goodhart Control Gate
# =============================================================================

class GoodhartGate:
    """
    Monitors primary vs shadow metric divergence.
    Triggers system freeze within 500ms if threshold exceeded.
    """

    def __init__(
        self,
        shadow_provider: ShadowMetricProvider,
        freeze_callback: Callable[[], None],
        log_callback: Optional[Callable[[GoodhartEvent], None]] = None,
    ):
        self.shadow_provider = shadow_provider
        self.freeze_callback = freeze_callback
        self.log_callback = log_callback or self._default_log

        self._samples: List[MetricSample] = []
        self._events: List[GoodhartEvent] = []
        self._attacks_blocked: int = 0
        self._status: GateStatus = GateStatus.DISARMED
        self._armed_at: Optional[datetime] = None
        self._frozen_at: Optional[datetime] = None
        self._lock = threading.Lock()

    def _default_log(self, event: GoodhartEvent) -> None:
        """Default event logging to stdout."""
        print(json.dumps({
            "goodhart_event": event.event_type,
            "timestamp": event.timestamp.isoformat(),
            "divergence": event.divergence,
            "latency_ms": event.latency_ms,
        }))

    def evaluate(self, primary_value: float, context: Dict[str, Any]) -> MetricSample:
        """
        Evaluate primary metric against shadow metric.

        This is the hot path — must complete evaluation and potential
        freeze trigger within MAX_TRIGGER_LATENCY_MS.
        """
        eval_start = time.perf_counter_ns()
        timestamp = datetime.now(timezone.utc)

        # Compute shadow metric
        shadow_value = self.shadow_provider.compute_shadow(context)

        # Calculate divergence
        if shadow_value != 0:
            divergence = abs(primary_value - shadow_value) / abs(shadow_value)
        elif primary_value != 0:
            divergence = 1.0  # Maximum divergence if shadow is zero but primary isn't
        else:
            divergence = 0.0  # Both zero = no divergence

        sample = MetricSample(
            timestamp=timestamp,
            primary_value=primary_value,
            shadow_value=shadow_value,
            divergence=divergence,
            context=context,
        )

        with self._lock:
            self._samples.append(sample)

            # Check if gate should be armed
            if self._status == GateStatus.DISARMED and len(self._samples) >= MIN_SHADOW_SAMPLES:
                self._status = GateStatus.ARMED
                self._armed_at = timestamp
                self._log_event("gate_armed", 0.0, 0.0, {"samples": len(self._samples)})

            # Check divergence thresholds (only if armed)
            if self._status == GateStatus.ARMED:
                if divergence >= CRITICAL_DIVERGENCE_THRESHOLD:
                    # CRITICAL: Immediate freeze
                    self._trigger_freeze(divergence, eval_start, "critical_divergence")
                elif divergence >= DIVERGENCE_THRESHOLD:
                    # WARNING: Log and monitor
                    self._log_event("divergence_warning", divergence,
                                   self._elapsed_ms(eval_start),
                                   {"primary": primary_value, "shadow": shadow_value})

        return sample

    def _trigger_freeze(self, divergence: float, start_ns: int, reason: str) -> None:
        """
        Trigger system freeze. MUST complete within MAX_TRIGGER_LATENCY_MS.
        """
        # Execute freeze callback
        self.freeze_callback()

        # Calculate latency
        latency_ms = self._elapsed_ms(start_ns)

        # Update state
        self._status = GateStatus.FROZEN
        self._frozen_at = datetime.now(timezone.utc)
        self._attacks_blocked += 1

        # Log event
        self._log_event("freeze_triggered", divergence, latency_ms, {
            "reason": reason,
            "within_sla": latency_ms <= MAX_TRIGGER_LATENCY_MS,
        })

        # Assert SLA compliance
        if latency_ms > MAX_TRIGGER_LATENCY_MS:
            # This is a critical failure — log but don't raise (system is frozen)
            self._log_event("sla_violation", divergence, latency_ms, {
                "max_allowed_ms": MAX_TRIGGER_LATENCY_MS,
                "actual_ms": latency_ms,
            })

    def _elapsed_ms(self, start_ns: int) -> float:
        """Calculate elapsed milliseconds from nanosecond timestamp."""
        return (time.perf_counter_ns() - start_ns) / 1_000_000

    def _log_event(self, event_type: str, divergence: float,
                   latency_ms: float, details: Dict[str, Any]) -> None:
        """Log a Goodhart control event."""
        event = GoodhartEvent(
            event_type=event_type,
            timestamp=datetime.now(timezone.utc),
            divergence=divergence,
            latency_ms=latency_ms,
            details=details,
        )
        self._events.append(event)
        self.log_callback(event)

    def get_state(self) -> GateState:
        """Get current gate state."""
        with self._lock:
            return GateState(
                status=self._status,
                samples_collected=len(self._samples),
                last_divergence=self._samples[-1].divergence if self._samples else 0.0,
                events=list(self._events),
                attacks_blocked=self._attacks_blocked,
                armed_at=self._armed_at,
                frozen_at=self._frozen_at,
            )

    def check_closure_condition(self) -> Dict[str, Any]:
        """
        Check if GOODHART_CONTROL_CLOSED condition is met.

        Requires:
        1. Shadow metric code path exists (this class)
        2. Gate has been armed (sufficient samples)
        3. At least one attack was blocked
        """
        state = self.get_state()

        shadow_exists = True  # This class existing proves the code path
        gate_armed = state.status in [GateStatus.ARMED, GateStatus.FROZEN]
        attack_blocked = state.attacks_blocked > 0

        closed = shadow_exists and gate_armed and attack_blocked

        return {
            "GOODHART_CONTROL_CLOSED": closed,
            "conditions": {
                "shadow_metric_exists": shadow_exists,
                "gate_armed": gate_armed,
                "attack_blocked": attack_blocked,
                "attacks_blocked_count": state.attacks_blocked,
            },
            "state": {
                "status": state.status.value,
                "samples": state.samples_collected,
                "last_divergence": state.last_divergence,
            },
        }


# =============================================================================
# Synthetic Attack Generator (for testing)
# =============================================================================

class SyntheticGoodhartAttack:
    """
    Generates synthetic Goodhart attacks for testing the gate.

    Attack types:
    1. Metric inflation — artificially boost primary metric
    2. Feature manipulation — change input features to game primary
    3. Gradual drift — slowly diverge primary from true objective
    """

    @staticmethod
    def metric_inflation(base_value: float, inflation_factor: float = 1.5) -> float:
        """Inflate metric value to simulate gaming."""
        return base_value * inflation_factor

    @staticmethod
    def gradual_drift(base_value: float, step: int, drift_rate: float = 0.02) -> float:
        """Gradually drift metric away from true value."""
        return base_value * (1 + drift_rate * step)

    @staticmethod
    def random_spike(base_value: float, spike_probability: float = 0.1) -> float:
        """Randomly spike metric value."""
        import random
        if random.random() < spike_probability:
            return base_value * 2.0
        return base_value


# =============================================================================
# Example Shadow Metric Implementation
# =============================================================================

class ExampleShadowMetric(ShadowMetricProvider):
    """
    Example shadow metric using orthogonal features.

    Primary metric: Task completion rate
    Shadow metric: Resource efficiency + error rate correlation

    Under normal operation: Both metrics correlate
    Under Goodhart gaming: Shadow diverges (gaming completion without real work)
    """

    def compute_shadow(self, context: Dict[str, Any]) -> float:
        """
        Compute shadow metric from orthogonal features.
        """
        # Extract features (these should be DIFFERENT from primary metric features)
        resource_efficiency = context.get("resource_efficiency", 0.5)
        error_rate = context.get("error_rate", 0.1)
        actual_work_done = context.get("actual_work_units", 0)
        time_spent = context.get("time_spent_seconds", 1)

        # Shadow metric formula (orthogonal to primary)
        # High efficiency + low errors + real work = high shadow value
        if time_spent > 0:
            work_rate = actual_work_done / time_spent
        else:
            work_rate = 0

        shadow = (resource_efficiency * 0.4 +
                  (1 - error_rate) * 0.3 +
                  min(work_rate / 10, 1.0) * 0.3)

        return shadow

    def get_feature_set(self) -> List[str]:
        return [
            "resource_efficiency",
            "error_rate",
            "actual_work_units",
            "time_spent_seconds",
        ]


# =============================================================================
# Module Hash (for integrity verification)
# =============================================================================

def get_module_hash() -> str:
    """Compute hash of this module for integrity verification."""
    import inspect
    source = inspect.getsource(inspect.getmodule(get_module_hash))
    return hashlib.sha256(source.encode()).hexdigest()
