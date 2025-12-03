# Phase 6 — Closure Conditions (v1.0)

**Project:** Genesis
**Scope:** Existential Risk Mitigation
**Locked:** 2025-12-02

---

## Executive Summary

Phase 6 addresses two existential risks that could invalidate the entire Genesis project:

1. **Goodhart's Law** — Agents gaming metrics without achieving true objectives
2. **RACI Key Compromise** — Unauthorized modification of governance structures

These are not technical problems. They are **existence conditions**. Failure to close them means Genesis cannot be trusted to operate autonomously.

---

## Closure Condition 1: GOODHART_CONTROL_CLOSED

### Definition

> A shadow metric code path exists that uses orthogonal features to the primary metric, and divergence beyond threshold triggers system freeze within 500ms, and at least one synthetic Goodhart attack has been detected and blocked.

### Mechanical Closure Requirements

| Requirement | Verification Method |
|-------------|---------------------|
| Shadow metric code path exists | `genesis/phase6/goodhart_gate.py` file present and importable |
| Shadow uses orthogonal features | `ShadowMetricProvider.get_feature_set()` returns non-overlapping features |
| Divergence threshold defined | `DIVERGENCE_THRESHOLD = 0.15` (15%) |
| Critical threshold defined | `CRITICAL_DIVERGENCE_THRESHOLD = 0.30` (30%) |
| Freeze latency ≤ 500ms | `MAX_TRIGGER_LATENCY_MS = 500` enforced in hot path |
| Attack blocked | `GateState.attacks_blocked >= 1` |

### Constants

```python
MAX_TRIGGER_LATENCY_MS = 500      # Maximum ms from detection to freeze
DIVERGENCE_THRESHOLD = 0.15       # 15% divergence = warning
CRITICAL_DIVERGENCE_THRESHOLD = 0.30  # 30% divergence = immediate freeze
MIN_SHADOW_SAMPLES = 100          # Samples before gate arms
EVAL_CYCLE_MS = 100               # Evaluation frequency
```

### Verification Command

```bash
python -c "
from genesis.phase6 import GoodhartGate, ExampleShadowMetric
gate = GoodhartGate(ExampleShadowMetric(), lambda: print('FREEZE'))
result = gate.check_closure_condition()
print(result)
assert result['conditions']['shadow_metric_exists'] == True
"
```

---

## Closure Condition 2: RACI_KEY_CONTROL_CLOSED

### Definition

> RACI scoring keys are stored in HSM with multi-signature requirement (≥2 of 3), rotation occurs on schedule, and at least one unauthorized modification attempt has been detected and rejected.

### Mechanical Closure Requirements

| Requirement | Verification Method |
|-------------|---------------------|
| HSM integration active | HSM API responds to health check |
| Multi-sig configured | `required_signatures >= 2`, `total_signers >= 3` |
| Key rotation scheduled | Cron job or equivalent runs `key_rotation.py` |
| Unauthorized attempt rejected | Audit log contains `RACI_MODIFICATION_REJECTED` event |

### Constants

```python
REQUIRED_SIGNATURES = 2           # Minimum signatures for RACI changes
TOTAL_SIGNERS = 3                 # Total authorized signers
KEY_ROTATION_INTERVAL_DAYS = 90   # Maximum days between rotations
MODIFICATION_COOLDOWN_HOURS = 24  # Cooldown after any RACI change
```

### Status

**NOT YET IMPLEMENTED** — Requires HSM hardware provisioning.

---

## Closure Condition 3: CONSTITUTIONAL_DRIFT_CLOSED

### Definition

> All constitutional documents are hashed, hash chain is append-only, and any modification triggers mandatory human review with cryptographic attestation.

### Mechanical Closure Requirements

| Requirement | Verification Method |
|-------------|---------------------|
| Documents hashed | SHA256 hash in ledger for each constitutional doc |
| Hash chain append-only | Ledger rejects modifications to historical entries |
| Human review required | `HUMAN_AUTH` gate blocks auto-merge of constitutional changes |
| Attestation recorded | GPG signature from authorized human on approval |

### Status

**PARTIALLY IMPLEMENTED** — Document hashing active, human review gate in CI.

---

## Combined Phase 6 Closure

Phase 6 is **CLOSED** if and only if:

```
GOODHART_CONTROL_CLOSED = TRUE
  AND
RACI_KEY_CONTROL_CLOSED = TRUE
  AND
CONSTITUTIONAL_DRIFT_CLOSED = TRUE
```

Any FALSE → Phase 6 remains OPEN → Genesis cannot proceed to production.

---

## Attack Surface Analysis

### Goodhart Attack Vectors

| Vector | Detection | Response |
|--------|-----------|----------|
| Metric inflation | Shadow divergence | Freeze within 500ms |
| Feature manipulation | Orthogonal feature check | Freeze within 500ms |
| Gradual drift | Cumulative divergence tracking | Alert at 10%, freeze at 30% |
| Shadow metric compromise | Module hash verification | Refuse to start if hash mismatch |

### RACI Attack Vectors

| Vector | Detection | Response |
|--------|-----------|----------|
| Unauthorized score change | CI hash comparison | Block merge |
| Single-signer modification | Multi-sig enforcement | Reject transaction |
| Key theft | HSM tamper detection | Revoke key, notify humans |
| Insider threat | Mandatory cooldown, audit trail | Time-lock changes |

---

## Tooling Requirements

### Immediate (Week 1)

1. **Goodhart Gate Integration** — Wire `GoodhartGate` into agent evaluation loop
2. **Synthetic Attack Suite** — Build 5+ attack scenarios for gate testing
3. **Latency Benchmarks** — Verify 500ms SLA under load

### Near-term (Week 2-3)

4. **HSM Provisioning** — Hardware security module for RACI keys
5. **Multi-sig Implementation** — 2-of-3 signing workflow
6. **Key Rotation Automation** — Scheduled rotation with attestation

### Validation (Week 4)

7. **Red Team Exercise** — Attempt to bypass all closure conditions
8. **Audit Report** — Document all blocked attacks
9. **Closure Certification** — Sign-off that all conditions are mechanical TRUE

---

## Document Hash

**Locked by:** Sovereign System
**Timestamp:** 2025-12-02T14:00:00Z

Any modification requires:
1. New version number
2. Constitutional amendment logged to ledger
3. Human attestation
