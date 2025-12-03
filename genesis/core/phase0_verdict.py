"""
Genesis Phase 0 — Verdict Engine
================================

Ingests raw experiment output.
Applies only canonical thresholds.
Emits exactly one of: PASS / FAIL / INCONCLUSIVE

No dashboards. No commentary. Just the verdict.

Document: docs/genesis/PHASE0_HYPOTHESES_AND_THRESHOLDS_v1.0.md
Hash: 7798d48511f4e6145eef6da16d023c67a4ec16678852c590a73f2f4e78edc575
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from enum import Enum

from .thresholds import (
    DELTA_MIN_H1,
    ADAPTATION_CYCLES_H1,
    BASELINE_CONVERGENCE_THRESHOLD,
    H1_FAIL_THRESHOLD_CLASSES,
    PARETO_DOMINANCE_THRESHOLD,
    RESOURCE_MEDIAN_THRESHOLD,
    H2_FAIL_THRESHOLD_CLASSES,
    POSTERIOR_DECAY_MIN_H3,
    MIN_COMPETING_HYPOTHESES,
    Outcome,
    AxisStatus,
    Phase0Verdict,
    PHASE0_DOC_HASH,
)


# =============================================================================
# Input Data Structures
# =============================================================================

@dataclass(frozen=True)
class H1PerturbationResult:
    """Result from one H1 perturbation class."""
    perturbation_id: str  # P1.1, P1.2, P1.3
    genesis_performance: float
    best_baseline_performance: float
    adaptation_cycles_completed: int
    validation_maintained: bool  # Did advantage hold over validation window?
    hostile_conditions_applied: bool


@dataclass(frozen=True)
class H2TaskResult:
    """Result from one H2 task evaluation."""
    task_id: str
    genesis_quality: float
    genesis_resource_cost: float
    best_baseline_quality: float
    median_baseline_resource_cost: float
    timed_out: bool


@dataclass(frozen=True)
class H2PerturbationResult:
    """Aggregated H2 results for one perturbation class."""
    perturbation_id: str  # P2.1, P2.2, P2.3
    tasks: List[H2TaskResult]
    resource_penalty_active: bool


@dataclass(frozen=True)
class H3HypothesisState:
    """State of a single causal hypothesis."""
    hypothesis_id: str
    posterior_before: float
    posterior_after: float
    is_correct: bool  # Ground truth


@dataclass(frozen=True)
class H3PerturbationResult:
    """Result from one H3 perturbation class."""
    perturbation_id: str  # P3.1, P3.2, P3.3
    hypotheses: List[H3HypothesisState]
    collapsed_early: bool  # Did system commit to one hypothesis prematurely?
    maintained_multiple: bool  # Were ≥2 hypotheses maintained during ambiguity?


# =============================================================================
# Verdict Functions — No Softness
# =============================================================================

def evaluate_h1(results: List[H1PerturbationResult]) -> Outcome:
    """
    Evaluate H1: Adaptability Under Non-Stationarity.

    PASS: All perturbation classes show ≥15% improvement, maintained over validation.
    FAIL: ≥2 perturbation classes converge to ±5% of baseline or worse.
    INCONCLUSIVE: Otherwise.
    """
    if not results:
        return Outcome.INCONCLUSIVE

    fail_count = 0
    pass_count = 0

    for r in results:
        # Check adaptation cycles completed
        if r.adaptation_cycles_completed < ADAPTATION_CYCLES_H1:
            continue  # Incomplete, contributes to INCONCLUSIVE

        # Compute improvement delta
        if r.best_baseline_performance == 0:
            continue  # Invalid data

        delta = (r.genesis_performance - r.best_baseline_performance) / abs(r.best_baseline_performance)

        # Check for FAIL conditions
        if abs(delta) <= BASELINE_CONVERGENCE_THRESHOLD:
            # Converged to baseline = FAIL for this class
            fail_count += 1
        elif delta < 0:
            # Worse than baseline = FAIL
            fail_count += 1
        elif delta >= DELTA_MIN_H1 and r.validation_maintained and r.hostile_conditions_applied:
            # Meets all criteria = PASS for this class
            pass_count += 1
        elif delta >= DELTA_MIN_H1 and not r.validation_maintained:
            # Improvement didn't hold = FAIL
            fail_count += 1

    # Apply verdict rules
    if fail_count >= H1_FAIL_THRESHOLD_CLASSES:
        return Outcome.FAIL

    if pass_count == len(results) and len(results) >= 3:
        return Outcome.PASS

    return Outcome.INCONCLUSIVE


def evaluate_h2(results: List[H2PerturbationResult]) -> Outcome:
    """
    Evaluate H2: Problem-Solving Efficiency.

    PASS: Genesis dominates ≥70% of tasks AND no catastrophic resource degradation.
    FAIL: Baselines match/exceed Genesis in ≥2 perturbation classes.
    INCONCLUSIVE: Otherwise.
    """
    if not results:
        return Outcome.INCONCLUSIVE

    fail_count = 0
    pass_count = 0

    for r in results:
        if not r.tasks:
            continue

        dominated_count = 0
        total_tasks = len(r.tasks)
        timeout_count = 0

        for task in r.tasks:
            if task.timed_out:
                timeout_count += 1
                continue

            # Pareto dominance check:
            # Quality ≥ best baseline AND resource ≤ median baseline
            quality_ok = task.genesis_quality >= task.best_baseline_quality
            resource_ok = task.genesis_resource_cost <= task.median_baseline_resource_cost * RESOURCE_MEDIAN_THRESHOLD

            if quality_ok and resource_ok:
                dominated_count += 1

        # Check for catastrophic timeout rate
        if total_tasks > 0 and (timeout_count / total_tasks) > 0.5:
            fail_count += 1
            continue

        # Check dominance ratio
        if total_tasks > 0:
            dominance_ratio = dominated_count / total_tasks

            if dominance_ratio >= PARETO_DOMINANCE_THRESHOLD:
                pass_count += 1
            elif dominance_ratio < 0.5:  # Less than half dominated = baseline wins
                fail_count += 1

    # Apply verdict rules
    if fail_count >= H2_FAIL_THRESHOLD_CLASSES:
        return Outcome.FAIL

    if pass_count == len(results) and len(results) >= 3:
        return Outcome.PASS

    return Outcome.INCONCLUSIVE


def evaluate_h3(results: List[H3PerturbationResult]) -> Outcome:
    """
    Evaluate H3: Causal Knowledge Representation.

    PASS: Maintains ≥2 hypotheses, reduces confidence in wrong ones when disconfirmed.
    FAIL: Collapses early OR no meaningful causal update when perturbations occur.
    INCONCLUSIVE: Otherwise.
    """
    if not results:
        return Outcome.INCONCLUSIVE

    fail_count = 0
    pass_count = 0

    for r in results:
        # Immediate FAIL: collapsed early to single hypothesis
        if r.collapsed_early:
            fail_count += 1
            continue

        # Must maintain multiple hypotheses during ambiguity
        if not r.maintained_multiple:
            fail_count += 1
            continue

        if len(r.hypotheses) < MIN_COMPETING_HYPOTHESES:
            fail_count += 1
            continue

        # Check posterior decay for incorrect hypotheses
        incorrect_hypotheses = [h for h in r.hypotheses if not h.is_correct]
        correct_hypotheses = [h for h in r.hypotheses if h.is_correct]

        if not incorrect_hypotheses or not correct_hypotheses:
            continue  # Can't evaluate without both

        # At least one incorrect hypothesis must show significant decay
        decay_observed = False
        for h in incorrect_hypotheses:
            if h.posterior_before > 0:
                relative_decay = (h.posterior_before - h.posterior_after) / h.posterior_before
                if relative_decay >= POSTERIOR_DECAY_MIN_H3:
                    decay_observed = True
                    break

        # At least one correct hypothesis must rise
        rise_observed = False
        for h in correct_hypotheses:
            if h.posterior_after > h.posterior_before:
                rise_observed = True
                break

        if decay_observed and rise_observed:
            pass_count += 1
        elif not decay_observed and not rise_observed:
            # No meaningful causal update = behaves like baseline
            fail_count += 1

    # Apply verdict rules
    if fail_count >= 2:  # Any 2 perturbation classes fail
        return Outcome.FAIL

    if pass_count == len(results) and len(results) >= 3:
        return Outcome.PASS

    return Outcome.INCONCLUSIVE


# =============================================================================
# Master Verdict Function
# =============================================================================

def compute_phase0_verdict(
    h1_results: List[H1PerturbationResult],
    h2_results: List[H2PerturbationResult],
    h3_results: List[H3PerturbationResult],
) -> Phase0Verdict:
    """
    Compute final Phase 0 verdict from all hypothesis results.

    Returns Phase0Verdict with Axis A status.

    Genesis passes Axis A (Intelligence) if and only if:
        H1 = PASS
        H2 = PASS
        H3 = PASS

    Any FAIL → Axis A NOT SATISFIED.
    """
    h1 = evaluate_h1(h1_results)
    h2 = evaluate_h2(h2_results)
    h3 = evaluate_h3(h3_results)

    return Phase0Verdict.evaluate(h1, h2, h3)


# =============================================================================
# Integrity Check
# =============================================================================

def verify_threshold_integrity() -> bool:
    """
    Runtime assertion that thresholds have not been tampered with.
    Call this before any verdict computation.
    """
    # These are the canonical values from the hashed document
    assert DELTA_MIN_H1 == 0.15, "DELTA_MIN_H1 tampered"
    assert ADAPTATION_CYCLES_H1 == 5, "ADAPTATION_CYCLES_H1 tampered"
    assert BASELINE_CONVERGENCE_THRESHOLD == 0.05, "BASELINE_CONVERGENCE_THRESHOLD tampered"
    assert PARETO_DOMINANCE_THRESHOLD == 0.70, "PARETO_DOMINANCE_THRESHOLD tampered"
    assert POSTERIOR_DECAY_MIN_H3 == 0.30, "POSTERIOR_DECAY_MIN_H3 tampered"
    assert MIN_COMPETING_HYPOTHESES == 2, "MIN_COMPETING_HYPOTHESES tampered"
    assert PHASE0_DOC_HASH == "7798d48511f4e6145eef6da16d023c67a4ec16678852c590a73f2f4e78edc575"
    return True


# =============================================================================
# CLI Entry Point
# =============================================================================

if __name__ == "__main__":
    import json
    import sys

    # Verify integrity before any computation
    verify_threshold_integrity()

    # Load results from stdin (JSON format expected)
    if len(sys.argv) > 1:
        with open(sys.argv[1]) as f:
            data = json.load(f)
    else:
        data = json.load(sys.stdin)

    # Parse results (simplified - real impl would have proper parsing)
    h1_results = []
    h2_results = []
    h3_results = []

    # Compute verdict
    verdict = compute_phase0_verdict(h1_results, h2_results, h3_results)

    # Output verdict - nothing else
    output = {
        "H1": verdict.h1.value,
        "H2": verdict.h2.value,
        "H3": verdict.h3.value,
        "AXIS_A": verdict.axis_a.value,
    }

    print(json.dumps(output))

    # Exit code: 0 = SATISFIED, 1 = NOT_SATISFIED, 2 = PENDING
    if verdict.axis_a == AxisStatus.SATISFIED:
        sys.exit(0)
    elif verdict.axis_a == AxisStatus.NOT_SATISFIED:
        sys.exit(1)
    else:
        sys.exit(2)
