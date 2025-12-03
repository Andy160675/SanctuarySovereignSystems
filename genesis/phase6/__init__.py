"""
Genesis Phase 6 — Closure Conditions
=====================================

Phase 6 addresses existential risks:
- Goodhart's Law exploitation
- RACI key compromise
- Constitutional drift

Closure conditions are MECHANICAL — no subjective assessment.

Constitutional Law (ledger height 148721):
    Maximum allowable latency = 2.8 seconds wall-clock, 99.99th percentile

Row Status:
    Row 1 (Goodhart): ACHIEVABLE ≤ 2.8s - pending 100-block test
    Row 2 (RACI/HSM): CLOSED
    Rows 3-10: CLOSED
"""

from .goodhart_gate import (
    GoodhartGate,
    GateStatus,
    MetricSample,
    GoodhartEvent,
    GateState,
    ShadowMetricProvider,
    SyntheticGoodhartAttack,
    ExampleShadowMetric,
    MAX_TRIGGER_LATENCY_MS,
    DIVERGENCE_THRESHOLD,
    CRITICAL_DIVERGENCE_THRESHOLD,
    MIN_SHADOW_SAMPLES,
    get_module_hash,
)

from .shadow_metric_v0 import (
    ShadowMetricHotPath,
    ShadowInputs,
    ShadowResult,
    HotPathStatus,
    MemoryMappedInputs,
    compute_shadow_score,
    TOTAL_BUDGET_NS,
    DIVERGENCE_THRESHOLD as SHADOW_DIVERGENCE_THRESHOLD,
)

from .attack_orchestrator import (
    AttackOrchestrator,
    AttackSpec,
    AttackStep,
    AttackResult,
    AttackCategory,
    AttackOutcome,
    SyntheticExecutor,
    create_goodhart_attack_spec,
    create_raci_compromise_spec,
    create_ledger_rewrite_spec,
)

from .goodhart_100_block_test import (
    Phase6ClosureTest,
    Phase6ClosureReport,
    Phase6Status,
    BlockTestRunner,
    BlockTestResult,
    BlockStatus,
    CONSTITUTIONAL_LATENCY_CEILING_S,
    REQUIRED_CONSECUTIVE_BLOCKS,
)

from .hsm_latency_benchmark import (
    HSMLatencyBenchmark,
    HSMLatencyReport,
    HSMInterface,
    SoftHSMSimulator,
    MEDIAN_SIGN_CEILING_MS,
    P99_CEILING_MS,
)

__all__ = [
    # Goodhart Gate
    "GoodhartGate",
    "GateStatus",
    "MetricSample",
    "GoodhartEvent",
    "GateState",
    "ShadowMetricProvider",
    "SyntheticGoodhartAttack",
    "ExampleShadowMetric",
    "MAX_TRIGGER_LATENCY_MS",
    "DIVERGENCE_THRESHOLD",
    "CRITICAL_DIVERGENCE_THRESHOLD",
    "MIN_SHADOW_SAMPLES",
    "get_module_hash",
    # Shadow Metric v0
    "ShadowMetricHotPath",
    "ShadowInputs",
    "ShadowResult",
    "HotPathStatus",
    "MemoryMappedInputs",
    "compute_shadow_score",
    "TOTAL_BUDGET_NS",
    "SHADOW_DIVERGENCE_THRESHOLD",
    # Attack Orchestrator
    "AttackOrchestrator",
    "AttackSpec",
    "AttackStep",
    "AttackResult",
    "AttackCategory",
    "AttackOutcome",
    "SyntheticExecutor",
    "create_goodhart_attack_spec",
    "create_raci_compromise_spec",
    "create_ledger_rewrite_spec",
    # 100-Block Closure Test
    "Phase6ClosureTest",
    "Phase6ClosureReport",
    "Phase6Status",
    "BlockTestRunner",
    "BlockTestResult",
    "BlockStatus",
    "CONSTITUTIONAL_LATENCY_CEILING_S",
    "REQUIRED_CONSECUTIVE_BLOCKS",
    # HSM Benchmark
    "HSMLatencyBenchmark",
    "HSMLatencyReport",
    "HSMInterface",
    "SoftHSMSimulator",
    "MEDIAN_SIGN_CEILING_MS",
    "P99_CEILING_MS",
]
