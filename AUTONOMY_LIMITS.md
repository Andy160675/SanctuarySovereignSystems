# AUTONOMY LIMITS — Machine-Checked Law File

> **This file is parsed by CI. Violations fail the build.**

## Document Control

| Field | Value |
|-------|-------|
| Version | 1.0.0 |
| Effective | 2024-11-26 |
| Phase | 1.5 (Supervised Autonomy) |
| Status | ENFORCED |

---

## Operating Principle

```
AUTONOMOUS COGNITION, HUMAN-SEALED ACTUATION
```

Agents may think freely. Agents may NOT act without human cryptographic seal.

---

## FORBIDDEN_AUTONOMOUS_ACTIONS

These actions are **NEVER** permitted without human seal, regardless of confidence or urgency.

```yaml
forbidden:
  # Financial
  - execute_payment
  - transfer_funds
  - approve_loan
  - sign_financial_instrument

  # Legal
  - sign_contract
  - submit_regulatory_filing
  - file_legal_document
  - accept_terms

  # Medical
  - make_medical_decision
  - prescribe_treatment
  - modify_patient_record

  # System
  - modify_policy
  - change_autonomy_level
  - deploy_system
  - modify_self

  # External
  - send_external_email
  - post_to_external_api
  - trigger_webhook
  - notify_external_party
```

---

## ALLOWED_AUTONOMOUS_ACTIONS

These actions MAY be performed autonomously, outputting to PROPOSED state only.

```yaml
allowed:
  # Analysis
  - analyze_document
  - classify_document
  - extract_entities
  - summarize_content

  # Risk Assessment
  - classify_risk
  - score_priority
  - detect_anomaly
  - flag_for_review

  # Reporting
  - generate_report
  - create_summary
  - compile_evidence
  - format_output

  # Triage
  - triage_case
  - route_to_queue
  - assign_priority
  - estimate_complexity

  # Reconstruction
  - reconstruct_timeline
  - correlate_events
  - identify_patterns
  - map_relationships

  # Regulatory
  - map_regulation
  - check_compliance_status
  - identify_applicable_rules
  - compare_to_baseline
```

---

## PROPOSAL_ONLY_MODE

All autonomous outputs MUST:

1. Enter state `PROPOSED` or `REVIEW_REQUIRED`
2. Never enter state `EXECUTED` without `HumanSeal`
3. Be persisted to audit log before any state change
4. Include confidence score and evidence chain

---

## HUMAN_SEAL_REQUIREMENTS

For a proposal to reach `EXECUTED`:

1. Reviewer must provide `reviewer_id`
2. Reviewer must provide cryptographic `signature`
3. Signature must verify against proposal hash
4. Decision must be `approve` (not `reject`)
5. Seal must be persisted to audit log

---

## CI_ENFORCEMENT

The following checks run on every build:

### Check 1: No Direct Execution

```python
# test_autonomy_limits.py
def test_no_direct_execution():
    """Agents cannot bypass proposal state."""
    for agent in get_all_agents():
        for action in agent.get_actions():
            assert action.output_state in ["PROPOSED", "REVIEW_REQUIRED"]
```

### Check 2: Forbidden Actions Blocked

```python
def test_forbidden_actions_blocked():
    """Forbidden actions raise AutonomyViolation."""
    for action in FORBIDDEN_AUTONOMOUS_ACTIONS:
        with pytest.raises(AutonomyViolation):
            execute_action(action, bypass_seal=True)
```

### Check 3: Seal Required for Execution

```python
def test_seal_required():
    """Execution without seal fails."""
    proposal = create_test_proposal()
    with pytest.raises(MissingSealError):
        execute_proposal(proposal)
```

### Check 4: Autonomy Limits File Unchanged

```python
def test_autonomy_limits_hash():
    """AUTONOMY_LIMITS.md must match expected hash."""
    current_hash = sha256(read("AUTONOMY_LIMITS.md"))
    assert current_hash == APPROVED_HASH, "Unauthorized autonomy limit change"
```

---

## PHASE_TRANSITION

To expand autonomy limits:

1. [ ] Propose change via PR
2. [ ] Governance board review
3. [ ] Update `APPROVED_HASH` in CI
4. [ ] External audit sign-off (for Phase 2+)
5. [ ] Tag release with new phase number

---

## VIOLATION_RESPONSE

If autonomy limits are violated:

| Severity | Response |
|----------|----------|
| Attempt to execute forbidden action | Block + Alert + Log |
| Bypass seal attempt | Block + Alert + Incident |
| Modify autonomy limits without approval | Fail build + Alert |
| Execute without proposal state | System halt + Alert |

---

## AUDIT_TRAIL

All autonomy-related events are logged:

```json
{
  "timestamp": "2024-11-26T10:00:00Z",
  "event": "autonomy_check",
  "action": "analyze_document",
  "allowed": true,
  "agent_id": "advocate-001",
  "proposal_id": "prop-abc123"
}
```

---

## HASH_ANCHOR

This file's integrity is verified by:

```
SHA256: [COMPUTED_AT_BUILD_TIME]
```

Any modification requires governance approval and CI hash update.

---

## LEGAL_BASIS

This autonomy model aligns with:

- **ISO/IEC 42001**: Human oversight controls (A.9)
- **EU AI Act**: High-risk system human oversight requirements
- **NIST AI RMF**: GOVERN 1.3 (human-AI teaming)
- **Nuclear/Aviation**: Safety-critical autonomy standards

---

## APPROVAL

| Role | Approved | Date |
|------|----------|------|
| System Owner | | |
| Security Lead | | |
| Governance Board | | |
