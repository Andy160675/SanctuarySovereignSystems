"""
Genesis Phase 0 — Threshold Constants
======================================

These thresholds are IMMUTABLE and derive from:
    docs/genesis/PHASE0_HYPOTHESES_AND_THRESHOLDS_v1.0.md
    SHA256: 7798d48511f4e6145eef6da16d023c67a4ec16678852c590a73f2f4e78edc575

Axis A Declaration:
    "Genesis is only a success if *intelligence* appears under hostile test.
    Anything less is a different project."

Any modification to these values requires:
    1. Constitutional amendment logged to ledger
    2. New document version with updated hash
    3. Explicit Axis A re-evaluation
"""

from enum import Enum
from dataclasses import dataclass
from typing import Final


# =============================================================================
# H1 — Adaptability Under Non-Stationarity
# =============================================================================

# Genesis must achieve ≥15% sustained improvement over best baseline
DELTA_MIN_H1: Final[float] = 0.15

# Number of adaptation cycles before evaluation
ADAPTATION_CYCLES_H1: Final[int] = 5

# Convergence within ±5% of baseline = FAIL
BASELINE_CONVERGENCE_THRESHOLD: Final[float] = 0.05

# Minimum perturbation classes that must fail to trigger overall H1 FAIL
H1_FAIL_THRESHOLD_CLASSES: Final[int] = 2


# =============================================================================
# H2 — Problem-Solving Efficiency
# =============================================================================

# Genesis must dominate in ≥70% of tasks (Pareto sense)
PARETO_DOMINANCE_THRESHOLD: Final[float] = 0.70

# Resource use must be ≤ median baseline (1.0 = equal)
RESOURCE_MEDIAN_THRESHOLD: Final[float] = 1.0

# Minimum perturbation classes that must fail to trigger overall H2 FAIL
H2_FAIL_THRESHOLD_CLASSES: Final[int] = 2


# =============================================================================
# H3 — Causal Knowledge Representation
# =============================================================================

# Minimum posterior decay for disconfirmed hypotheses
POSTERIOR_DECAY_MIN_H3: Final[float] = 0.30

# Target posterior decay for disconfirmed hypotheses
POSTERIOR_DECAY_MAX_H3: Final[float] = 0.50

# Must maintain at least this many competing hypotheses during ambiguity
MIN_COMPETING_HYPOTHESES: Final[int] = 2


# =============================================================================
# Outcome Classification
# =============================================================================

class Outcome(str, Enum):
    """Hypothesis evaluation outcomes."""
    PASS = "PASS"
    FAIL = "FAIL"
    INCONCLUSIVE = "INCONCLUSIVE"


class AxisStatus(str, Enum):
    """Axis A overall status."""
    SATISFIED = "SATISFIED"           # All H1, H2, H3 = PASS
    NOT_SATISFIED = "NOT_SATISFIED"   # Any H = FAIL
    PENDING = "PENDING"               # Evaluation incomplete


@dataclass(frozen=True)
class Phase0Verdict:
    """Immutable verdict for Phase 0 evaluation."""
    h1: Outcome
    h2: Outcome
    h3: Outcome
    axis_a: AxisStatus

    @classmethod
    def evaluate(cls, h1: Outcome, h2: Outcome, h3: Outcome) -> "Phase0Verdict":
        """Compute Axis A status from hypothesis outcomes."""
        if any(h == Outcome.FAIL for h in [h1, h2, h3]):
            axis_a = AxisStatus.NOT_SATISFIED
        elif all(h == Outcome.PASS for h in [h1, h2, h3]):
            axis_a = AxisStatus.SATISFIED
        else:
            axis_a = AxisStatus.PENDING

        return cls(h1=h1, h2=h2, h3=h3, axis_a=axis_a)


# =============================================================================
# Document Reference
# =============================================================================

PHASE0_DOC_PATH: Final[str] = "docs/genesis/PHASE0_HYPOTHESES_AND_THRESHOLDS_v1.0.md"
PHASE0_DOC_HASH: Final[str] = "7798d48511f4e6145eef6da16d023c67a4ec16678852c590a73f2f4e78edc575"
PHASE0_LOCKED_DATE: Final[str] = "2025-12-02"


# =============================================================================
# Axis A Commitment
# =============================================================================

AXIS_A_COMMITMENT: Final[str] = """
If Axis A condition is not met, Genesis must pivot to
"Guaranteed-Safe Adaptive Infrastructure" and cannot be continued
as an intelligence project without a new, explicitly logged
constitutional amendment.
"""
