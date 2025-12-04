# ST MICHAEL – Automation & Guarantees

> **"No action shall execute unless the proof of safety survives ST MICHAEL's test."**

## Implementation Status

| Component | Path | Status |
|-----------|------|--------|
| Python Adjudication Gate | `st_michael/adjudication.py` | ✅ Implemented |
| Python Refusal Logger | `st_michael/refusal_log.py` | ✅ Implemented |
| Rust Harness (cryptographic) | `st_michael/harness/` | 📋 Placeholder |
| Unit Tests | `tests/test_st_michael.py` | ✅ Implemented |

---

## 1. Role in the Organism

ST MICHAEL comprises two interdependent components:

### Row 14: Adjudication Gate

**Rust Reference:** `src/row14_st_michael.rs`
**Python Implementation:** `st_michael/adjudication.py`

The **epistemic guardian** that decides whether something may cross the boundary between halted and running states.

- Receives ONLY externally adjudicated canon updates
- Enforces quorum (5-of-7), cooling period (72 hours), and proof-of-closure
- Can only REPLACE evidence roots, never modify rules
- Constitutional law: "The door only opens from outside, only after the system has already stopped, and only to add facts, never to change rules."

### Resilience Layer (`src/st_michael_resilience.rs`)
The **psychological defense system** that monitors quorum health and issues operational directives.

- Tracks adjudicator health metrics (stress, burnout, vote entropy)
- Produces `HealthState` classification: `Green`, `Amber`, `Red`
- Issues directives: rotation, sabbatical, external audit, freeze powers
- Sits AROUND Rows 14-15, never ABOVE them

In short: **Row 14 guards what gets in. Resilience guards who is allowed to judge.**

---

## 2. Inputs and Outputs

### Row 14 Adjudication Gate

**Inputs:**
- `AdjudicationRequest` with halt context and new evidence
- `DilithiumSignature` (post-quantum signatures from adjudicators)
- `StarkProvenanceProof` (STARK proof of external provenance)

**Outputs:**
- `AdjudicationOutcome` ∈ { `EvidenceAccepted`, `EvidenceRejected`, `QuorumNotMet`, `CoolingPeriodActive`, `RateLimited`, `SystemNotHalted` }
- `Row14Result` ∈ { `Inactive`, `AwaitingAdjudication`, `CoolingDown`, `Resuming` }

### Resilience Watchdog

**Inputs:**
- `MemberHealthMetrics` per adjudicator:
  - `days_absent`, `avg_response_latency_ms`
  - `vote_entropy` (0 = always same vote, 1 = maximally varied)
  - `freeze_bias`, `load_index`, `stress_signal`
  - `no_show_streak`, `abstention_rate`, `circadian_anomaly`
- `chaos_level` (0.0 – 1.0)

**Outputs:**
- `HealthState` ∈ { `Green`, `Amber`, `Red` }
- `QuorumHealthSnapshot` with aggregate scores
- `ResilienceDirective` ∈ { `EnforceRotation`, `MandatorySabbatical`, `ExternalAudit`, `QuorumExpansion`, `FreezePowers`, `RestorePowers`, `NoAction` }

These outputs are consumed by:
- Governance / Aumann Gate
- Row 15 (Dead Man's Covenant) activation checks
- Chaos simulator & resilience tests
- Future UI / dashboards

---

## 3. Tests That Exercise ST MICHAEL

The following tests must pass for ST MICHAEL to be considered **operational**:

### Rust Unit Tests (in-module)
- `src/row14_st_michael.rs::tests`
  - `test_cannot_adjudicate_when_running` – System must be halted
  - `test_quorum_required` – 5-of-7 signatures required
  - `test_unauthorized_signer_rejected` – Only registered adjudicators
  - `test_duplicate_signer_rejected` – No double-signing
  - `test_evidence_too_large` – 10MB evidence limit
  - `test_row14_inactive_when_running` – Status checks

- `src/st_michael_resilience.rs::tests`
  - `test_healthy_quorum` – Green state detection
  - `test_stressed_quorum` – Amber/Red state detection
  - `test_entropy_collapse_detection` – High chaos + low entropy = RED
  - `test_watchdog_green_state` – Normal operations
  - `test_watchdog_amber_forces_rotation` – Rotation mandate
  - `test_freeze_powers_activation` – After sustained RED
  - `test_freeze_powers_recovery` – After GREEN recovery
  - `test_member_sabbatical` – Sabbatical enforcement

### Python Unit Tests

- `tests/test_st_michael.py`
  - `TestAdjudicationGate` – Quorum voting, cooling period, persistence
  - `TestRefusalLogger` – Proof-of-Refusal generation and storage
  - `TestIntegration` – Full workflow from proposal to logged refusal

### Python Integration Tests
- `tests/test_governance_workflow.py` (to be created)
  - Verifies ST MICHAEL outputs are used in governance decisions
  - System behavior changes under different `health_state` values

If either set of tests fails in CI, **ST MICHAEL is not considered safe to rely on**.

---

## 3.1 Proof-of-Refusal Logging

Every failed attempt generates an immutable `ProofOfRefusal` artifact stored in `/logs/refusals/`:

```json
{
  "refusal_id": "REFUSAL-2025-12-03T23-45-00",
  "timestamp": "2025-12-03T23:45:00Z",
  "action_type": "quorum_failure",
  "action_details": {
    "proposal_id": "PROP-001",
    "votes_for": 3,
    "votes_required": 5,
    "shortfall": 2
  },
  "reason": "Quorum not achieved: 3/5 votes",
  "requestor_id": "attacker-id",
  "evidence_hash": "sha256:abc...",
  "refusal_hash": "sha256:def..."
}
```

**Purpose:**

1. Audit trail of all blocked actions
2. Evidence for governance review
3. Pattern detection for malicious attempts
4. Constitutional compliance proof

---

## 4. CI Workflows That Prove ST MICHAEL Is Alive

ST MICHAEL is exercised in these workflows:

### `.github/workflows/ci.yml`
- Runs Rust tests including ST MICHAEL modules
- Runs Python tests on every push to `main/develop`
- Red-team adversarial testing (prompt injection, tool abuse)
- Generates evidence bundle with all test results

### `.github/workflows/e2e-tests.yml`
- Runs E2E tests with coverage gate
- Enforces minimum coverage threshold (currently 40%)
- Fails the build if coverage drops below threshold
- Coverage gate prevents "tested" changes that let coverage rot

**Green CI on these workflows means:**
- Row 14 quorum and cooling period logic is correct
- Resilience Watchdog classifies health states properly
- FreezePowers activates/deactivates at correct thresholds
- Implementation matches expected behavior

---

## 5. Failure Semantics (What a Red Build Means)

### If Row 14 tests fail:

**Interpretation:**
- Quorum enforcement broken (wrong count, duplicate detection failed)
- Cooling period not enforced
- Evidence validation bypassed
- Unauthorized signers accepted

**Operator action:**
1. Read the failing test output
2. Check `src/row14_st_michael.rs` for the invariant that broke
3. Decide whether the implementation or the **spec** is wrong
4. Fix *either* the code or the test to realign behavior with intent
5. Only treat ST MICHAEL as trusted once CI is green again

### If Resilience Watchdog tests fail:

**Interpretation:**
- Health classification wrong (Green when should be Red)
- FreezePowers not activating under sustained attack
- Sabbatical enforcement broken
- Entropy collapse detection disabled

**Operator action:**
1. Check `src/st_michael_resilience.rs` thresholds
2. Verify `classify_health_state()` logic
3. Review `ResiliencePolicy` defaults

### If CI is red on ST MICHAEL-related tests, the correct posture is:

> **Assume the system has lost its ability to judge whether it's under attack.**
>
> **Assume the door between halted and running states may be unguarded.**

---

## 6. Claims We Can Honestly Make (for decks, audits, investors)

When CI is green on the Automation Baseline and ST MICHAEL tests, you can say:

> "Every code change is tested against ST MICHAEL's adjudication model and resilience layer.
> If the system's boundary-crossing logic breaks, the build fails.
> If the quorum health detection breaks, the build fails.
> We do not ship if the machine can't correctly guard its state transitions or judge its own risk state."

This is the line you can put in:
- Investor decks
- Security / compliance docs
- Seedrs / due diligence packs
- ISO 42001 / NIST AI RMF evidence bundles

---

## 7. Constitutional Guarantees (from the code)

### Row 14 Guarantees:
```
QUORUM_REQUIRED: 5 of 7 adjudicators
COOLING_PERIOD: 72 hours
MIN_BLOCKS_BETWEEN_ADJUDICATIONS: 10,000
MAX_EVIDENCE_SIZE: 10 MB
```

### Resilience Guarantees:
```
amber_threshold: 0.7 (score below = AMBER)
red_threshold: 0.4 (score below = RED)
max_continuous_red_days: 90 (then FreezePowers activates)
recovery_days_required: 30 (GREEN days before powers restore)
sabbatical_load_threshold: 0.85 (mandatory rest)
```

### Attack Detection Heuristics:
- High chaos (>0.7) + low entropy (<0.2) = automatic RED
- Multiple burnout indicators → external audit triggered
- Freeze bias spike → investigate external pressure
- Circadian anomaly → detect coerced responses at odd hours

---

## 8. Running ST MICHAEL Tests Locally

### Rust tests:
```bash
cd /c/sovereign-system
cargo test row14_st_michael
cargo test st_michael_resilience
```

### Full CI simulation:
```bash
cargo test --workspace
pytest tests/ -v --ignore=tests/red_team/ --ignore=tests/fuzz/
```

### Watch for regressions:
```bash
cargo watch -x "test st_michael"
```

---

## Appendix: State Transition Diagram

```
                    ┌──────────────────────────────────────────┐
                    │           SYSTEM RUNNING                 │
                    │         (Row 14 Inactive)                │
                    └──────────────────┬───────────────────────┘
                                       │
                              [Row 7-13 Halt Event]
                                       │
                                       ▼
                    ┌──────────────────────────────────────────┐
                    │         SYSTEM HALTED                    │
                    │    (Row 14 Awaiting Adjudication)        │
                    └──────────────────┬───────────────────────┘
                                       │
                      [Submit AdjudicationRequest]
                                       │
                                       ▼
                    ┌──────────────────────────────────────────┐
                    │           COOLING PERIOD                 │
                    │         (72 hours minimum)               │
                    │     [Signatures accumulating...]         │
                    └──────────────────┬───────────────────────┘
                                       │
                         [5/7 quorum + 72h elapsed]
                                       │
                                       ▼
                    ┌──────────────────────────────────────────┐
                    │         ADJUDICATION FINALIZED           │
                    │  [Evidence Accepted → New Canon Root]    │
                    └──────────────────┬───────────────────────┘
                                       │
                                       ▼
                    ┌──────────────────────────────────────────┐
                    │         SYSTEM RESUMING                  │
                    │    (Row 14 returns to Inactive)          │
                    └──────────────────────────────────────────┘
```

---

*Last updated: Automation Baseline v1.1*
