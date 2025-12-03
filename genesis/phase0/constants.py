"""
Genesis Phase 0 — Canonical Hypothesis Thresholds
Axis A: REQUIRED
DO NOT MODIFY WITHOUT FORMAL AMENDMENT
"""

# =========================
# H1 — ADAPTABILITY
# =========================

# Minimum sustained performance improvement over best baseline
DELTA_MIN_H1 = 0.15        # 15%

# Number of full adaptation cycles after which delta is evaluated
ADAPTATION_CYCLES_H1 = 5

# Post-adaptation validation window (episodes)
VALIDATION_WINDOW_H1 = 50

# Convergence band to baseline considered failure
BASELINE_CONVERGENCE_EPS = 0.05   # ±5%


# =========================
# H2 — PROBLEM-SOLVING EFFICIENCY
# =========================

# Minimum dominance ratio across task suite
DOMINANCE_RATIO_H2 = 0.70   # Must dominate ≥70% of tasks

# Allowed relative degradation under resource penalty before failure
MAX_RESOURCE_DEGRADATION_H2 = 0.20   # 20%

# Maximum allowed timeout rate under constraint
MAX_TIMEOUT_RATE_H2 = 0.10   # 10%


# =========================
# H3 — CAUSAL KNOWLEDGE REPRESENTATION
# =========================

# Minimum relative posterior decay for disconfirmed hypothesis
POSTERIOR_DECAY_MIN_H3 = 0.35   # 35% drop minimum

# Required number of simultaneous competing hypotheses
MIN_COMPETING_HYPOTHESES_H3 = 2

# Confidence collapse threshold (premature commitment)
PREMATURE_COLLAPSE_THRESHOLD_H3 = 0.85   # ≥85% too early = fail


# =========================
# CROSS-HYPOTHESIS AXIS GATES
# =========================

AXIS_A_REQUIRED = True

# Phase 0 verdict mapping
PASS = "PASS"
FAIL = "FAIL"
INCONCLUSIVE = "INCONCLUSIVE"

# Genesis proceeds as intelligence project ONLY if all are PASS
REQUIRED_VERDICTS = [PASS, PASS, PASS]


# =========================
# IMMUTABILITY GUARD
# =========================

CANON_VERSION = "PHASE0_HYPOTHESES_v1.0"
