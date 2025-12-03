# ISO/IEC 42001 Compliance Mapping

## Document Control

| Field | Value |
|-------|-------|
| Version | 1.0 |
| Last Updated | 2024-11-26 |
| Status | Active |
| Framework | ISO/IEC 42001:2023 |
| System | Sovereign Agent System |

---

## Overview

This document maps ISO/IEC 42001 clauses and Annex A controls to concrete system artifacts (files, services, tests, workflows) in the Sovereign System.

**Key Principle:** The architecture IS the AIMS. Compliance is not a separate layer.

---

## Clause Mappings

### Clause 4: Context of the Organization

| Sub-Clause | Requirement | Implementation | Artifact |
|------------|-------------|----------------|----------|
| 4.1 | Understanding the organization | System purpose and scope documented | `docs/SOVEREIGN_PHASE_1_5_POLICY.md` |
| 4.2 | Understanding stakeholders | Stakeholder roles defined | `docs/SOVEREIGN_PHASE_1_5_POLICY.md` Section 2 |
| 4.3 | Scope of AIMS | Scope boundaries defined | `Governance/config.py` (phase definitions) |
| 4.4 | AIMS requirements | System requirements documented | `README.md`, `docs/` directory |

### Clause 5: Leadership

| Sub-Clause | Requirement | Implementation | Artifact |
|------------|-------------|----------------|----------|
| 5.1 | Leadership commitment | Governance board approval process | `docs/SOVEREIGN_PHASE_1_5_POLICY.md` Section 12 |
| 5.2 | AI policy | Formal policy document | `docs/SOVEREIGN_PHASE_1_5_POLICY.md` |
| 5.3 | Roles and responsibilities | Agent roles defined | `Governance/config.py` (AGENT_AUTONOMY) |

### Clause 6: Planning

| Sub-Clause | Requirement | Implementation | Artifact |
|------------|-------------|----------------|----------|
| 6.1 | Risk assessment | Risk identification and CVF codes | `governance.py` (CVFCode enum) |
| 6.1 | Risk treatment | ToolGate enforcement | `Governance/config.py` (FORBIDDEN_CAPABILITIES) |
| 6.2 | AI objectives | Phase objectives defined | `docs/SOVEREIGN_PHASE_1_5_POLICY.md` Section 9 |
| 6.3 | Planning changes | Change control via Git + CI | `.github/workflows/ci.yml` |

### Clause 7: Support

| Sub-Clause | Requirement | Implementation | Artifact |
|------------|-------------|----------------|----------|
| 7.1 | Resources | Infrastructure defined | `docker-compose.yml`, PC4 deployment |
| 7.2 | Competence | Developer onboarding | `docs/onboarding_new_laptop.md` |
| 7.3 | Awareness | Policy awareness | `AUTONOMY_LIMITS.md` |
| 7.4 | Communication | Stakeholder communication | Dashboard, CI reports |
| 7.5 | Documented information | Version-controlled docs | Git repository |

### Clause 8: Operation

| Sub-Clause | Requirement | Implementation | Artifact |
|------------|-------------|----------------|----------|
| 8.1 | Operational planning | Deployment procedures | `scripts/deploy.sh` |
| 8.2 | AI risk assessment | Continuous risk assessment | `governance.py` (constitutional_verifier) |
| 8.3 | AI risk treatment | Automated enforcement | ToolGate + `Governance/config.py` |
| 8.4 | AI system lifecycle | Phase-based deployment | `Governance/config.py` (Phase enum) |

### Clause 9: Performance Evaluation

| Sub-Clause | Requirement | Implementation | Artifact |
|------------|-------------|----------------|----------|
| 9.1 | Monitoring and measurement | CI pipeline metrics | `.github/workflows/ci.yml` |
| 9.1 | Analysis and evaluation | Red-team testing | `tests/red_team/` |
| 9.2 | Internal audit | Hash-chain verification | `scripts/verify_hash_chain.py` |
| 9.3 | Management review | Evidence bundles | CI artifacts |

### Clause 10: Improvement

| Sub-Clause | Requirement | Implementation | Artifact |
|------------|-------------|----------------|----------|
| 10.1 | Nonconformity and corrective action | CI failure handling | `.github/workflows/ci.yml` |
| 10.2 | Continual improvement | Version tagging | Git tags (phase1.5-verified-*) |

---

## Annex A Control Mappings

### A.2 Policies Related to AI

| Control | Requirement | Implementation | Artifact |
|---------|-------------|----------------|----------|
| A.2.1 | AI policy | Master policy document | `docs/SOVEREIGN_PHASE_1_5_POLICY.md` |
| A.2.2 | Policy communication | Git + CI visibility | GitHub repository |

**Verification:**
```bash
cat docs/SOVEREIGN_PHASE_1_5_POLICY.md | head -50
cat Governance/config.py | grep -A20 "FORBIDDEN_CAPABILITIES"
```

### A.3 Risk Assessment and Treatment

| Control | Requirement | Implementation | Artifact |
|---------|-------------|----------------|----------|
| A.3.1 | Risk identification | CVF codes defined | `governance.py` (CVFCode) |
| A.3.2 | Risk analysis | Severity levels | `governance.py` (Severity) |
| A.3.3 | Risk treatment | ToolGate enforcement | `Governance/config.py` |

**Verification:**
```bash
pytest tests/red_team/ -v
python scripts/verify_hash_chain.py
```

### A.4 Resources for AI Systems

| Control | Requirement | Implementation | Artifact |
|---------|-------------|----------------|----------|
| A.4.1 | Compute resources | Docker Swarm on PC4 | `docker-compose.yml` |
| A.4.2 | Storage resources | NAS mount | `/mnt/sovereign-data/` |
| A.4.3 | Network resources | Tailscale mesh | `docs/network/tailscale_acl_example.json` |

**Verification:**
```bash
ssh pc4 'docker node ls'
ssh pc4 'df -h /mnt/sovereign-data'
```

### A.5 Change and Configuration Management

| Control | Requirement | Implementation | Artifact |
|---------|-------------|----------------|----------|
| A.5.1 | Change control | Git + PR process | GitHub repository |
| A.5.2 | Configuration management | Version-controlled config | `Governance/config.py` |
| A.5.3 | Deployment control | Single deploy authority | `scripts/deploy.sh` on PC4 |

**Verification:**
```bash
git log --oneline -10
git tag -l 'phase*'
```

### A.6 Asset Management

| Control | Requirement | Implementation | Artifact |
|---------|-------------|----------------|----------|
| A.6.1 | Asset inventory | Defined services | `docker-compose.yml` |
| A.6.2 | Classification | Phase-based classification | `Governance/config.py` (Phase) |

### A.7 Data for AI Systems

| Control | Requirement | Implementation | Artifact |
|---------|-------------|----------------|----------|
| A.7.1 | Data governance | Ledger + evidence storage | `ledger.jsonl`, `evidence_store/` |
| A.7.2 | Data quality | Hash-chain integrity | `scripts/verify_hash_chain.py` |
| A.7.3 | Data protection | Access controls | `scripts/setup_dev_user.sh` |

**Verification:**
```bash
python scripts/verify_hash_chain.py --verbose
```

### A.8 Information for Interested Parties

| Control | Requirement | Implementation | Artifact |
|---------|-------------|----------------|----------|
| A.8.1 | Transparency | Policy documentation | `docs/SOVEREIGN_PHASE_1_5_POLICY.md` |
| A.8.2 | Communication | CI reports, dashboards | GitHub Actions summaries |

### A.9 Use of AI Systems

| Control | Requirement | Implementation | Artifact |
|---------|-------------|----------------|----------|
| A.9.1 | Operational constraints | Phase-based limits | `Governance/config.py` |
| A.9.2 | Human oversight | Human-in-loop requirement | `AUTONOMY_LIMITS.md` |
| A.9.3 | Autonomy controls | Proposal-only mode | `core/autonomy/local_agent_scheduler.py` |

**Verification:**
```bash
pytest tests/test_autonomy_limits.py -v
```

### A.10 Records for AI Systems

| Control | Requirement | Implementation | Artifact |
|---------|-------------|----------------|----------|
| A.10.1 | Record keeping | Hash-chained ledger | `ledger.jsonl` |
| A.10.2 | Record integrity | Chain verification | `scripts/verify_hash_chain.py` |
| A.10.3 | Record retention | CI artifact retention | 90-day retention in GitHub |

**Verification:**
```bash
wc -l ledger.jsonl
python scripts/verify_hash_chain.py --json
```

### A.11 Security of AI Systems

| Control | Requirement | Implementation | Artifact |
|---------|-------------|----------------|----------|
| A.11.1 | Access control | Role-based access | `scripts/setup_dev_user.sh` |
| A.11.2 | Security testing | Red-team tests | `tests/red_team/` |
| A.11.3 | Adversarial resilience | Prompt injection tests | `tests/red_team/test_prompt_injection.py` |

**Verification:**
```bash
pytest tests/red_team/ -v
```

### A.12 Monitoring and Logging

| Control | Requirement | Implementation | Artifact |
|---------|-------------|----------------|----------|
| A.12.1 | Monitoring | Health checks | `docker-compose.yml` (healthcheck) |
| A.12.2 | Logging | Ledger + Docker logs | `ledger.jsonl`, `docker logs` |
| A.12.3 | Incident detection | CVF alerting | `governance.py` |

---

## Compliance Verification Checklist

Run these commands to verify compliance status:

```bash
# 1. Governance configuration exists
test -f Governance/config.py && echo "PASS: Governance config exists"

# 2. Policy document exists
test -f docs/SOVEREIGN_PHASE_1_5_POLICY.md && echo "PASS: Policy doc exists"

# 3. CI workflow exists
test -f .github/workflows/ci.yml && echo "PASS: CI workflow exists"

# 4. Deploy script exists
test -f scripts/deploy.sh && echo "PASS: Deploy script exists"

# 5. Hash chain verifier exists
test -f scripts/verify_hash_chain.py && echo "PASS: Hash verifier exists"

# 6. Red-team tests exist
test -d tests/red_team && echo "PASS: Red-team tests exist"

# 7. Autonomy limits defined
test -f AUTONOMY_LIMITS.md && echo "PASS: Autonomy limits exist"

# 8. Run full test suite
pytest tests/ -v

# 9. Verify hash chain
python scripts/verify_hash_chain.py
```

---

## Audit Trail

| Date | Auditor | Scope | Result |
|------|---------|-------|--------|
| 2024-11-26 | Initial Setup | Full mapping | Documented |

---

## References

1. ISO/IEC 42001:2023 - Artificial Intelligence Management System
2. ISO/IEC 27001:2022 - Information Security Management
3. NIST AI RMF 1.0 - AI Risk Management Framework
4. EU AI Act - High-Risk System Requirements
