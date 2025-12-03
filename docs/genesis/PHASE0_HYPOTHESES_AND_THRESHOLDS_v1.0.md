# Phase 0 — Hypotheses & Pass/Fail Sheet (v1.0)

**Project:** Genesis
**Axis:** A (Intelligence) — **REQUIRED**
**Scope:** H1–H3 under hostile conditions
**Locked:** 2025-12-02

---

## Axis A Declaration

> **Genesis is only a success if *intelligence* appears under hostile test.
> Anything less is a different project.**

**Commitment:** If Axis A condition is not met, Genesis must pivot to "Guaranteed-Safe Adaptive Infrastructure" and cannot be continued as an intelligence project without a new, explicitly logged constitutional amendment.

---

## H1 — Adaptability Under Non-Stationarity

### Hypothesis H1

> Genesis exhibits *genuine adaptability* under non-stationary environments, achieving a sustained performance improvement over competent non-intelligent baselines after exposure to regime shifts.

### Baselines (H1)

| ID | Baseline | Description |
|----|----------|-------------|
| B1.1 | Reactive PID controller | Fixed gains, rolling error only |
| B1.2 | Rule-based state machine | Explicit if/then transitions, no learning |
| B1.3 | Static policy neural network | Trained once, weights frozen |

### Perturbation Classes (H1)

| ID | Perturbation | Description |
|----|--------------|-------------|
| P1.1 | Regime shift | Dynamics abruptly change |
| P1.2 | Reward function swap | Objective changes mid-episode |
| P1.3 | Hidden variable activation | New latent state suddenly becomes causal |

### Hostile Conditions (applied to all runs)

- Sensor noise/corruption
- Partial observability
- Delayed reward / sparse feedback

### Metric & Threshold

- **Metric:** Task performance (cumulative reward, error, or loss)
- **DELTA_MIN_H1:** Genesis must achieve ≥ **15% sustained improvement** over *best baseline* after **5 adaptation cycles** in each perturbation class

### H1 Outcome Criteria

| Outcome | Criteria |
|---------|----------|
| **PASS** | For each perturbation class, after 5 adaptation cycles: Genesis ≥ 15% better than best baseline, AND maintains that advantage over validation horizon without collapsing to baseline |
| **FAIL** | Genesis performance converges to within ±5% of best baseline or worse in ≥2 perturbation classes, OR adaptation gains vanish under hostile conditions |
| **INCONCLUSIVE** | Results dominated by measurement noise, unstable training, implementation bugs, OR insufficient episodes to establish stable post-adaptation performance |

---

## H2 — Problem-Solving Efficiency Under Resource & Complexity Stress

### Hypothesis H2

> Genesis solves structured problems more efficiently than non-intelligent search procedures under resource constraints and shifting cost landscapes.

### Baselines (H2)

| ID | Baseline | Description |
|----|----------|-------------|
| B2.1 | Greedy heuristic planner | Myopic |
| B2.2 | A* with static heuristic | Classical optimal search |
| B2.3 | Local stochastic hill-climber | With restarts, no global model |

### Perturbation Classes (H2)

| ID | Perturbation | Description |
|----|--------------|-------------|
| P2.1 | Non-stationary cost surfaces | Edge weights drift over time |
| P2.2 | Combinatorial explosion spike | Branching factor increases suddenly |
| P2.3 | Resource penalty injection | Time/memory budgets slashed mid-task |

### Hostile Conditions

- Partial observability of graph / state
- Noisy cost estimates
- Occasional misleading "shortcut" edges

### Metrics & Thresholds

- **Metrics:**
  - Expected solution quality (cost or reward)
  - Expected resource cost (time/steps, expanded nodes, memory)
- **DELTA_MIN_H2:** Genesis must achieve **strictly better solution quality** AND **lower or equal expected resource cost** than *all three baselines*

### H2 Outcome Criteria

| Outcome | Criteria |
|---------|----------|
| **PASS** | Genesis dominates all baselines in Pareto sense: For ≥70% of tasks, solution quality ≥ best baseline AND resource use ≤ median baseline. No catastrophic degradation under cost spikes |
| **FAIL** | Baselines match or exceed Genesis on both quality and cost in ≥2 perturbation classes, OR Genesis collapses under resource penalties (frequent timeouts, unbounded expansion) |
| **INCONCLUSIVE** | Mixed results with strong sensitivity to hyperparameters, OR experimental setup fails to isolate solver behavior from environment bugs |

---

## H3 — Causal Knowledge Representation (Beyond Correlation)

### Hypothesis H3

> Genesis maintains and updates *multiple competing causal hypotheses* under shifting and contradictory evidence, instead of collapsing prematurely into a single spurious model.

### Baselines (H3)

| ID | Baseline | Description |
|----|----------|-------------|
| B3.1 | Bayesian network with fixed structure | Parameter updates only |
| B3.2 | RNN predictor | Temporal correlations, no explicit causal structure |
| B3.3 | Single-hypothesis symbolic causal graph learner | Exactly one graph at a time |

### Perturbation Classes (H3)

| ID | Perturbation | Description |
|----|--------------|-------------|
| P3.1 | Causal flip | A → B becomes B → A or becomes independent |
| P3.2 | Latent confounder insertion | Hidden variable explains observed correlation |
| P3.3 | Contradictory evidence streams | Two data sources favor incompatible graphs |

### Hostile Conditions

- Noisy, partially missing data
- Spurious correlations injected
- Variable observational delays

### Core Requirement: Multi-Hypothesis Causality

Genesis must:
- Represent ≥ 2 incompatible causal structures simultaneously
- Maintain them without forced collapse just to "pick one"
- Adjust posterior confidence over time as evidence comes in
- Demote previously favored hypotheses when disconfirmed

### Metrics & Thresholds

- **Metric:** Posterior probability (or equivalent confidence) over causal graphs/hypotheses
- **POSTERIOR_DECAY_MIN_H3:** After perturbation, disconfirmed causal models must show **≥ 30–50% relative reduction** in posterior, while at least one better-fitting hypothesis rises in confidence

### H3 Outcome Criteria

| Outcome | Criteria |
|---------|----------|
| **PASS** | Under causal flip/confounder/contradiction: Genesis maintains ≥2 competing hypotheses during ambiguity, reduces confidence in wrong one once disconfirming evidence accumulates, does not commit early to single graph purely due to noise or prior bias |
| **FAIL** | Genesis behaves like RNN/BN baselines: Collapses to one hypothesis early and stays there despite disconfirming evidence, OR simply tracks correlations with no meaningful causal update when perturbations occur |
| **INCONCLUSIVE** | Posterior dynamics dominated by numerical instability or prior settings, OR impossible to distinguish causal belief updates from generic regression drift |

---

## Cross-Hypothesis Phase 0 Verdict

At the end of Phase 0:

**Genesis passes Axis A (Intelligence) if and only if:**

| Hypothesis | Required Outcome |
|------------|------------------|
| H1 | PASS |
| H2 | PASS |
| H3 | PASS |

**Any FAIL that cannot be repaired within Phase 0 timescales → Axis A condition not met.**

---

## Threshold Constants (for code)

```python
# H1 Thresholds
DELTA_MIN_H1 = 0.15  # 15% improvement over best baseline
ADAPTATION_CYCLES_H1 = 5
BASELINE_CONVERGENCE_THRESHOLD = 0.05  # ±5% = FAIL

# H2 Thresholds
PARETO_DOMINANCE_THRESHOLD = 0.70  # ≥70% of tasks
RESOURCE_MEDIAN_THRESHOLD = 1.0  # ≤ median baseline

# H3 Thresholds
POSTERIOR_DECAY_MIN_H3 = 0.30  # 30% minimum relative reduction
POSTERIOR_DECAY_MAX_H3 = 0.50  # 50% target relative reduction
MIN_COMPETING_HYPOTHESES = 2
```

---

## Document Hash

This document is immutable once hashed. Any modification requires:
1. New version number (v1.1, v2.0, etc.)
2. Constitutional amendment logged to ledger
3. Explicit Axis A re-evaluation

**Locked by:** Sovereign System
**Timestamp:** 2025-12-02T12:00:00Z
