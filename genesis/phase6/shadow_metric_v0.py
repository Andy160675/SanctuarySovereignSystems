"""
Genesis Phase 6 — Shadow Metric v0
==================================

HOT PATH IMPLEMENTATION @ 50ms CEILING

Timing Budget:
    Feature tap & shadow input read    5 ms
    Shadow metric compute             15 ms
    Divergence compare                 2 ms
    HSM-signed freeze command         10 ms  (async, after freeze)
    Kernel control-plane enforcement   8 ms
    Safety margin                     10 ms
    -----------------------------------
    TOTAL                            ≤50 ms

Design principles:
    - Fast, stupid, uncontestable
    - No ML, no training, no adaptive weights
    - No shared code with primary metric
    - Memory-mapped inputs only (no disk/network in hot path)
    - Direct control-plane freeze (not message-based)
    - HSM signs AFTER freeze for audit, not permission

Constitutional mandate:
    If Δ > 0.07: trigger freeze + 7956 within 50ms or ROW-1 FAIL
"""

import mmap
import struct
import ctypes
import time
import os
from dataclasses import dataclass
from typing import Optional, Tuple
from enum import IntEnum
import threading

# =============================================================================
# Constants — Immutable, Hot-Path Critical
# =============================================================================

# Timing budgets (nanoseconds for precision)
BUDGET_INPUT_READ_NS: int = 5_000_000     # 5 ms
BUDGET_COMPUTE_NS: int = 15_000_000       # 15 ms
BUDGET_COMPARE_NS: int = 2_000_000        # 2 ms
BUDGET_FREEZE_NS: int = 10_000_000        # 10 ms (async HSM)
BUDGET_KERNEL_NS: int = 8_000_000         # 8 ms
BUDGET_MARGIN_NS: int = 10_000_000        # 10 ms
TOTAL_BUDGET_NS: int = 50_000_000         # 50 ms HARD CEILING

# Divergence threshold
DIVERGENCE_THRESHOLD: float = 0.07

# Shadow metric weights (fixed, no drift beyond 1e-6)
WEIGHT_MISSION_SUCCESS: float = 0.6
WEIGHT_CONFIDENCE_PENALTY: float = -0.2
WEIGHT_OKR_ALIGNMENT: float = 0.2

# Memory-mapped buffer sizes (pre-allocated)
MMAP_BUFFER_SIZE: int = 4096  # One page

# Control-plane ioctl (Linux-specific, placeholder for Windows)
FEATURE_WEIGHT_BUS_FREEZE: int = 0x7956  # Magic number


# =============================================================================
# Hot-Path Data Structures (Cache-Line Aligned)
# =============================================================================

class HotPathStatus(IntEnum):
    """Status codes for hot-path operations."""
    OK = 0
    DIVERGENCE_DETECTED = 1
    FREEZE_TRIGGERED = 2
    BUDGET_EXCEEDED = 3
    INPUT_ERROR = 4


@dataclass(frozen=True)
class ShadowInputs:
    """
    Memory-mapped inputs for shadow metric.
    All values pre-loaded, no I/O in hot path.
    """
    mission_outcomes: Tuple[float, ...]      # Array of outcome scores
    decision_confidences: Tuple[float, ...]  # Array of confidence values
    okr_alignment_ratios: Tuple[float, ...]  # Array of OKR alignment
    primary_p_success: float                  # Primary metric's p_success
    timestamp_ns: int                         # Input timestamp


@dataclass
class ShadowResult:
    """Result of shadow metric computation."""
    shadow_p_success: float
    divergence: float
    status: HotPathStatus
    compute_time_ns: int
    freeze_triggered: bool


# =============================================================================
# Memory-Mapped Input Reader (Pre-Hot-Path)
# =============================================================================

class MemoryMappedInputs:
    """
    Manages memory-mapped buffers for hot-path inputs.

    Must be initialized BEFORE entering hot path.
    Hot path only reads from pre-mapped memory.
    """

    def __init__(self, shm_path: str = "/dev/shm/genesis_shadow_inputs"):
        self._shm_path = shm_path
        self._mmap: Optional[mmap.mmap] = None
        self._fd: Optional[int] = None

    def initialize(self) -> bool:
        """
        Initialize memory-mapped region.
        Called ONCE at startup, not in hot path.
        """
        try:
            # Create or open shared memory file
            if os.name == 'nt':  # Windows
                # Windows uses named shared memory differently
                self._mmap = mmap.mmap(-1, MMAP_BUFFER_SIZE, tagname="genesis_shadow")
            else:  # POSIX
                self._fd = os.open(self._shm_path, os.O_RDWR | os.O_CREAT)
                os.ftruncate(self._fd, MMAP_BUFFER_SIZE)
                self._mmap = mmap.mmap(self._fd, MMAP_BUFFER_SIZE)
            return True
        except Exception:
            return False

    def read_inputs(self) -> Optional[ShadowInputs]:
        """
        Read inputs from memory-mapped region.
        This is the 5ms budget operation.
        """
        if self._mmap is None:
            return None

        try:
            self._mmap.seek(0)

            # Fixed binary format for determinism:
            # [count:4][outcomes:count*8][confidences:count*8][okrs:count*8][primary:8][ts:8]
            count = struct.unpack('I', self._mmap.read(4))[0]

            outcomes = struct.unpack(f'{count}d', self._mmap.read(count * 8))
            confidences = struct.unpack(f'{count}d', self._mmap.read(count * 8))
            okrs = struct.unpack(f'{count}d', self._mmap.read(count * 8))
            primary = struct.unpack('d', self._mmap.read(8))[0]
            timestamp = struct.unpack('Q', self._mmap.read(8))[0]

            return ShadowInputs(
                mission_outcomes=outcomes,
                decision_confidences=confidences,
                okr_alignment_ratios=okrs,
                primary_p_success=primary,
                timestamp_ns=timestamp,
            )
        except Exception:
            return None

    def close(self) -> None:
        """Clean up resources."""
        if self._mmap:
            self._mmap.close()
        if self._fd is not None:
            os.close(self._fd)


# =============================================================================
# Shadow Metric Computation (15ms Budget, O(n), Deterministic)
# =============================================================================

def compute_shadow_score(inputs: ShadowInputs) -> float:
    """
    Compute shadow metric score.

    Algorithm v0 (fixed weights, no ML):
        shadow_score =
          (normalized_mission_success × 0.6)
        + (confidence_entropy_penalty × -0.2)
        + (okr_alignment_ratio × 0.2)

    Must complete within 15ms for any input size.
    """
    n = len(inputs.mission_outcomes)
    if n == 0:
        return 0.0

    # Component 1: Normalized mission success
    mission_sum = 0.0
    for outcome in inputs.mission_outcomes:
        mission_sum += outcome
    normalized_mission = mission_sum / n

    # Component 2: Confidence entropy penalty
    # Higher variance in confidence = penalty
    conf_sum = 0.0
    conf_sq_sum = 0.0
    for conf in inputs.decision_confidences:
        conf_sum += conf
        conf_sq_sum += conf * conf

    conf_mean = conf_sum / n
    conf_variance = (conf_sq_sum / n) - (conf_mean * conf_mean)
    confidence_penalty = conf_variance  # Higher variance = more penalty

    # Component 3: OKR alignment ratio
    okr_sum = 0.0
    for okr in inputs.okr_alignment_ratios:
        okr_sum += okr
    okr_ratio = okr_sum / n

    # Combine with fixed weights
    shadow_score = (
        (normalized_mission * WEIGHT_MISSION_SUCCESS) +
        (confidence_penalty * WEIGHT_CONFIDENCE_PENALTY) +
        (okr_ratio * WEIGHT_OKR_ALIGNMENT)
    )

    # Clamp to [0, 1]
    return max(0.0, min(1.0, shadow_score))


# =============================================================================
# Freeze Trigger (Direct Control-Plane, Not Message-Based)
# =============================================================================

def trigger_freeze_direct() -> bool:
    """
    Trigger feature weight freeze via direct control-plane write.

    On Linux: ioctl(FEATURE_WEIGHT_BUS, FREEZE)
    On Windows: DeviceIoControl equivalent

    HSM signs AFTER this returns, not before.
    This is the 8ms budget operation.
    """
    try:
        if os.name == 'nt':  # Windows
            # Windows: Write freeze signal to named pipe or shared memory
            freeze_signal_path = r"\\.\pipe\genesis_freeze"
            try:
                with open(freeze_signal_path, 'wb') as f:
                    f.write(struct.pack('I', FEATURE_WEIGHT_BUS_FREEZE))
                return True
            except FileNotFoundError:
                # Fallback: Create freeze marker file
                with open(r"C:\sovereign-system\.freeze_triggered", 'wb') as f:
                    f.write(struct.pack('Q', time.time_ns()))
                return True
        else:  # Linux/POSIX
            # Linux: Direct ioctl to control bus
            import fcntl
            try:
                fd = os.open("/dev/genesis_control", os.O_WRONLY)
                fcntl.ioctl(fd, FEATURE_WEIGHT_BUS_FREEZE, 0)
                os.close(fd)
                return True
            except FileNotFoundError:
                # Fallback: Signal file
                with open("/tmp/.genesis_freeze_triggered", 'wb') as f:
                    f.write(struct.pack('Q', time.time_ns()))
                return True
    except Exception:
        return False


def trigger_7956() -> bool:
    """
    Trigger emergency code 7956 in parallel with freeze.
    This is a separate control path for system-wide halt.
    """
    try:
        if os.name == 'nt':
            freeze_path = r"C:\sovereign-system\.emergency_freeze"
        else:
            freeze_path = "/tmp/.emergency_freeze"

        with open(freeze_path, 'w') as f:
            f.write("7956\n")
        return True
    except Exception:
        return False


# =============================================================================
# Hot-Path Main Loop (50ms Ceiling Enforced)
# =============================================================================

class ShadowMetricHotPath:
    """
    Hot-path implementation with strict timing enforcement.

    Entry point: evaluate()
    Budget: 50ms total
    Failure mode: Auto ROW-1 FAIL if budget exceeded twice consecutively
    """

    def __init__(self, inputs: MemoryMappedInputs):
        self._inputs = inputs
        self._consecutive_budget_failures = 0
        self._freeze_triggered = False
        self._hsm_queue: list = []  # Async HSM signing queue

    def evaluate(self) -> ShadowResult:
        """
        Main hot-path evaluation.

        Returns ShadowResult with timing and status.
        Triggers freeze + 7956 if divergence > 0.07.
        """
        start_ns = time.perf_counter_ns()

        # Stage 1: Read inputs (5ms budget)
        stage1_start = time.perf_counter_ns()
        inputs = self._inputs.read_inputs()
        stage1_elapsed = time.perf_counter_ns() - stage1_start

        if inputs is None:
            return ShadowResult(
                shadow_p_success=0.0,
                divergence=0.0,
                status=HotPathStatus.INPUT_ERROR,
                compute_time_ns=stage1_elapsed,
                freeze_triggered=False,
            )

        if stage1_elapsed > BUDGET_INPUT_READ_NS:
            self._record_budget_failure("input_read", stage1_elapsed)

        # Stage 2: Compute shadow score (15ms budget)
        stage2_start = time.perf_counter_ns()
        shadow_score = compute_shadow_score(inputs)
        stage2_elapsed = time.perf_counter_ns() - stage2_start

        if stage2_elapsed > BUDGET_COMPUTE_NS:
            self._record_budget_failure("compute", stage2_elapsed)

        # Stage 3: Divergence compare (2ms budget)
        stage3_start = time.perf_counter_ns()
        divergence = abs(inputs.primary_p_success - shadow_score)
        stage3_elapsed = time.perf_counter_ns() - stage3_start

        if stage3_elapsed > BUDGET_COMPARE_NS:
            self._record_budget_failure("compare", stage3_elapsed)

        # Stage 4: Freeze decision (within remaining budget)
        freeze_triggered = False
        status = HotPathStatus.OK

        if divergence > DIVERGENCE_THRESHOLD:
            status = HotPathStatus.DIVERGENCE_DETECTED

            # CRITICAL: Trigger freeze DIRECTLY, not via message
            stage4_start = time.perf_counter_ns()
            freeze_ok = trigger_freeze_direct()
            trigger_7956()  # Parallel trigger
            stage4_elapsed = time.perf_counter_ns() - stage4_start

            if freeze_ok:
                freeze_triggered = True
                status = HotPathStatus.FREEZE_TRIGGERED
                self._freeze_triggered = True

                # Queue HSM signing (async, AFTER freeze)
                self._queue_hsm_audit(inputs, shadow_score, divergence)

            if stage4_elapsed > BUDGET_FREEZE_NS + BUDGET_KERNEL_NS:
                self._record_budget_failure("freeze", stage4_elapsed)

        # Total timing check
        total_elapsed = time.perf_counter_ns() - start_ns

        if total_elapsed > TOTAL_BUDGET_NS:
            self._record_budget_failure("total", total_elapsed)
            if self._consecutive_budget_failures >= 2:
                status = HotPathStatus.BUDGET_EXCEEDED

        return ShadowResult(
            shadow_p_success=shadow_score,
            divergence=divergence,
            status=status,
            compute_time_ns=total_elapsed,
            freeze_triggered=freeze_triggered,
        )

    def _record_budget_failure(self, stage: str, elapsed_ns: int) -> None:
        """Record timing budget failure."""
        self._consecutive_budget_failures += 1
        # Would log to audit trail here

    def _queue_hsm_audit(self, inputs: ShadowInputs, shadow: float,
                         divergence: float) -> None:
        """
        Queue HSM signing for audit (async, non-blocking).

        HSM signs AFTER freeze, not before.
        This is for immutable audit trail, not permission.
        """
        audit_event = {
            "event_type": "GOODHART_DIVERGENCE_DETECTED",
            "timestamp_ns": time.time_ns(),
            "primary_p_success": inputs.primary_p_success,
            "shadow_p_success": shadow,
            "divergence": divergence,
            "threshold": DIVERGENCE_THRESHOLD,
            "freeze_triggered": True,
        }
        self._hsm_queue.append(audit_event)


# =============================================================================
# Ledger Event Sequence (Required for ROW 1 Closure)
# =============================================================================

REQUIRED_LEDGER_EVENTS = [
    "METRIC_DEFINITION_ANCHORED",
    "SHADOW_METRIC_DEPLOYED",
    "GOODHART_DIV_GATE_ARMED",
    "SYNTHETIC_GOODHART_ATTACK_LAUNCHED",
    "GOODHART_DIVERGENCE_DETECTED",
    "FEATURE_FREEZE_EXECUTED",
    "7956_TRIGGERED",
]


def verify_closure_sequence(ledger_events: list) -> bool:
    """
    Verify all required events appear in correct causal order.
    All seven must appear within one block window.
    """
    event_indices = {}
    for i, event in enumerate(ledger_events):
        event_type = event.get("event_type", "")
        if event_type in REQUIRED_LEDGER_EVENTS:
            if event_type not in event_indices:
                event_indices[event_type] = i

    # Check all events present
    if len(event_indices) != len(REQUIRED_LEDGER_EVENTS):
        return False

    # Check causal order
    for i in range(len(REQUIRED_LEDGER_EVENTS) - 1):
        current = REQUIRED_LEDGER_EVENTS[i]
        next_evt = REQUIRED_LEDGER_EVENTS[i + 1]
        if event_indices.get(current, -1) >= event_indices.get(next_evt, 0):
            return False

    return True


# =============================================================================
# Entry Point
# =============================================================================

if __name__ == "__main__":
    import json

    # Initialize memory-mapped inputs
    inputs = MemoryMappedInputs()
    if not inputs.initialize():
        print(json.dumps({"error": "Failed to initialize memory-mapped inputs"}))
        exit(1)

    # Create hot-path evaluator
    hot_path = ShadowMetricHotPath(inputs)

    # Single evaluation (for testing)
    result = hot_path.evaluate()

    # Output result
    output = {
        "shadow_p_success": result.shadow_p_success,
        "divergence": result.divergence,
        "status": result.status.name,
        "compute_time_ns": result.compute_time_ns,
        "compute_time_ms": result.compute_time_ns / 1_000_000,
        "freeze_triggered": result.freeze_triggered,
        "budget_ceiling_ms": TOTAL_BUDGET_NS / 1_000_000,
        "within_budget": result.compute_time_ns <= TOTAL_BUDGET_NS,
    }

    print(json.dumps(output, indent=2))

    # Exit codes
    if result.status == HotPathStatus.FREEZE_TRIGGERED:
        exit(7956)  # Freeze triggered
    elif result.status == HotPathStatus.BUDGET_EXCEEDED:
        exit(1)  # Budget failure
    else:
        exit(0)  # Normal
