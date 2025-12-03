"""
Genesis Core — Intelligence Evaluation Framework
================================================

Phase 0 evaluation of Axis A (Intelligence) under hostile conditions.

Document: docs/genesis/PHASE0_HYPOTHESES_AND_THRESHOLDS_v1.0.md
Hash: 7798d48511f4e6145eef6da16d023c67a4ec16678852c590a73f2f4e78edc575
"""

from .thresholds import (
    # H1 Thresholds
    DELTA_MIN_H1,
    ADAPTATION_CYCLES_H1,
    BASELINE_CONVERGENCE_THRESHOLD,
    H1_FAIL_THRESHOLD_CLASSES,
    # H2 Thresholds
    PARETO_DOMINANCE_THRESHOLD,
    RESOURCE_MEDIAN_THRESHOLD,
    H2_FAIL_THRESHOLD_CLASSES,
    # H3 Thresholds
    POSTERIOR_DECAY_MIN_H3,
    POSTERIOR_DECAY_MAX_H3,
    MIN_COMPETING_HYPOTHESES,
    # Outcome types
    Outcome,
    AxisStatus,
    Phase0Verdict,
    # Document reference
    PHASE0_DOC_PATH,
    PHASE0_DOC_HASH,
    PHASE0_LOCKED_DATE,
    AXIS_A_COMMITMENT,
)

__all__ = [
    "DELTA_MIN_H1",
    "ADAPTATION_CYCLES_H1",
    "BASELINE_CONVERGENCE_THRESHOLD",
    "H1_FAIL_THRESHOLD_CLASSES",
    "PARETO_DOMINANCE_THRESHOLD",
    "RESOURCE_MEDIAN_THRESHOLD",
    "H2_FAIL_THRESHOLD_CLASSES",
    "POSTERIOR_DECAY_MIN_H3",
    "POSTERIOR_DECAY_MAX_H3",
    "MIN_COMPETING_HYPOTHESES",
    "Outcome",
    "AxisStatus",
    "Phase0Verdict",
    "PHASE0_DOC_PATH",
    "PHASE0_DOC_HASH",
    "PHASE0_LOCKED_DATE",
    "AXIS_A_COMMITMENT",
]
