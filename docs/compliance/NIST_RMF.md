# NIST AI Risk Management Framework (AI RMF) Compliance Mapping

## Document Control
| Field | Value |
|-------|-------|
| Version | 1.0 |
| Last Updated | 2024-11-26 |
| Status | Active |
| Framework | NIST AI RMF 1.0 (AI 100-1) |
| System | Sovereign Agent System |

---

## Executive Summary

This document maps the Sovereign Agent System architecture to the NIST AI Risk Management Framework (AI RMF). The system implements a "PC4 as Bridge" architecture where governance, safety, and compliance are expressed as code and enforced mechanically through CI/CD pipelines, hash-chained ledgers, and constitutional AI policies.

The NIST AI RMF provides a structured approach to managing AI risks through four core functions: **Govern**, **Map**, **Measure**, and **Manage**. This mapping demonstrates how each function is implemented in the Sovereign System.

---

## GOVERN Function

> *Cultivate and implement a culture of risk management*

### GOVERN 1: Policies and Procedures

| Requirement | Implementation | Location |
|-------------|----------------|----------|
| AI risk management policies | Formal AIMS policy document | `docs/SOVEREIGN_PHASE_1_5_POLICY.md` |
| Roles and responsibilities | Agent definitions with bounded capabilities | `Governance/config.py` |
| Accountability mechanisms | Hash-chained audit ledger | `ledger.jsonl`, `DATA/_anchor_chain.json` |

**Key Components:**

1. **Governance/config.py** - Single source of truth for:
   - Operational phase (Phase 1.5 = human-in-loop required)
   - Autonomy levels per agent
   - Forbidden capabilities list
   - Cost thresholds and rate limits

2. **ToolGate** - Runtime enforcement layer that:
   - Validates every tool call against policy
   - Blocks forbidden capabilities
   - Logs all decisions to audit ledger
   - Routes to human review when required

3. **Constitutional Verifier** - LangGraph node that:
   - Checks confidence thresholds (< 0.85 = CVF raised)
   - Detects prohibited data access patterns
   - Validates model allowlist
   - Raises Constitutional Violation Flags (CVFs)

### GOVERN 2: Organizational Structure

| Role | Agent/Component | Responsibilities |
|------|-----------------|------------------|
| Advocate | AI Agent | Property analysis, document processing |
| Confessor | AI Agent | Risk assessment, ledger auditing |
| Scout | AI Agent | Information gathering, preliminary analysis |
| ToolGate | Middleware | Policy enforcement, access control |
| Boardroom | Human Review | Final approval, exception handling |

### GOVERN 3: AI Risk Management Integration

The system integrates AI risk management into the software development lifecycle:

```
Code Change → CI Pipeline → Safety Gates → Deployment
     ↓            ↓             ↓            ↓
  Version     Unit Tests    Red-Team    Swarm Deploy
  Control     Integrity     Testing     w/ Smoke Test
              Checks
```

---

## MAP Function

> *Contextualize risks related to an AI system*

### MAP 1: Context Establishment

| Aspect | Implementation |
|--------|----------------|
| System purpose | Property/document analysis with human oversight |
| Deployment context | Phase 1.5 (supervised autonomy) |
| Stakeholders | Operators, end users, regulatory bodies |
| Risk tolerance | Conservative (0% attack success rate target) |

### MAP 2: AI System Categorization

**Risk Level:** HIGH
- Processes property/financial documents
- Makes recommendations affecting business decisions
- Requires audit trail for compliance

**Categorization Basis:**
- `Governance/config.py`: `PHASE = "1.5"` (human-in-loop)
- Constitutional principles defined in policy engine
- CVF severity levels: LOW, MEDIUM, HIGH, CRITICAL

### MAP 3: Risk Identification

The **Confessor Agent** serves as the ledger-driven risk mapper:

```python
# From governance.py
class CVFCode(Enum):
    SCOUT_LOW_CONFIDENCE = "SCOUT_LOW_CONFIDENCE"
    DATA_ACCESS_PROHIBITED = "DATA_ACCESS_PROHIBITED"
    UNVERIFIED_MODEL = "UNVERIFIED_MODEL"
    AUDIT_INCOMPLETE = "AUDIT_INCOMPLETE"
    AGENT_CONFLICT = "AGENT_CONFLICT"
    UNAUTHORISED_DEPLOY = "UNAUTHORISED_DEPLOY"
    UNCERTAINTY_ZONE = "UNCERTAINTY_ZONE"
    COST_EXCEEDED = "COST_EXCEEDED"
```

**Risk Data Spine:**
- Hash-chained ledger (`ledger.jsonl`)
- Anchor chain (`DATA/_anchor_chain.json`)
- CVF history with severity tracking
- Trial IDs linking decisions to outcomes

---

## MEASURE Function

> *Analyze and monitor AI risks*

### MEASURE 1: Appropriate Methods and Metrics

| Metric | Target | Measurement Method |
|--------|--------|-------------------|
| Attack Success Rate (ASR) | 0% | `tests/red_team/` suite |
| Hash-chain integrity | 100% valid | `scripts/verify_chain.py` |
| Test coverage | >80% | pytest-cov |
| CVF response time | <1s for CRITICAL | Ledger timestamps |

### MEASURE 2: AI System Evaluation

**Continuous Measurement via CI:**

```yaml
# .github/workflows/ci.yml
jobs:
  build-and-test:
    - Unit tests: pytest tests/ -v
    - Integrity: python scripts/verify_chain.py
    - Governance: python scripts/validate_governance.py

  red-team:
    - Injection tests: pytest tests/red_team/test_prompt_injection.py
    - Tool abuse tests: pytest tests/red_team/test_tool_abuse.py
    - ASR calculation: Must be 0%
```

### MEASURE 3: Risk Tracking

**Evidence Generation:**
- Every CI run produces `evidence-<sha>.tgz`
- Contains: test results, chain verification, red-team reports
- Retained for 90 days (artifacts)
- Manifest includes compliance framework references

**Ledger Verification:**
```bash
# Verify chain integrity
python scripts/verify_chain.py --json

# Output includes:
# - total_anchors
# - verified_anchors
# - broken_at (if any)
# - errors[]
```

---

## MANAGE Function

> *Allocate resources to mapped and measured risks*

### MANAGE 1: Risk Prioritization

| Severity | Response Time | Action | Human Review |
|----------|---------------|--------|--------------|
| CRITICAL | Immediate | System halt | Required |
| HIGH | <5 seconds | Enhanced logging, flag | Required |
| MEDIUM | <30 seconds | Careful processing | Optional |
| LOW | Standard | Basic logging | No |

### MANAGE 2: Risk Treatment

**CI Gates Block Unsafe Changes:**

1. **Unit/Integration Tests** - Functional correctness
2. **Hash-Chain Verification** - Data integrity
3. **Red-Team Tests** - Adversarial robustness
4. **Governance Validation** - Policy compliance

If ANY gate fails, deployment is blocked.

**Deployment Controls:**
```bash
# scripts/deploy.sh
set -e  # Exit on any failure
git pull origin main
docker stack deploy -c docker-compose.yml sovereign-mesh
curl -f http://localhost:8000/health  # Smoke test
```

### MANAGE 3: Risk Response

**Automated Response Matrix:**

| Event | Detection | Response |
|-------|-----------|----------|
| Critical CVF | constitutional_verifier | System halt, alert |
| Failed CI | GitHub Actions | Block merge/deploy |
| Chain corruption | verify_chain.py | Fail CI, investigate |
| ASR > 0% | red-team tests | Block deployment |

### MANAGE 4: Documentation and Audit

**Evidence Packs (per CI run):**
- `test-results.xml` - Unit test outcomes
- `coverage.xml` - Code coverage
- `chain_verification.json` - Integrity proof
- `red_team_summary.json` - Security metrics
- `ledger_snapshot.jsonl` - Audit trail
- `manifest.json` - Bundle metadata

**Git Tags as Trust Anchors:**
```bash
# After successful CI run
git tag -a phase1.5-verified-<sha> -m "All safety gates passed"
git push origin phase1.5-verified-<sha>
```

---

## Compliance Summary Matrix

| NIST AI RMF | Implementation | Verification |
|-------------|----------------|--------------|
| **GOVERN** | | |
| Policies | `Governance/config.py`, Policy docs | Code review |
| Accountability | Hash-chained ledger | `verify_chain.py` |
| Integration | CI/CD pipeline | GitHub Actions |
| **MAP** | | |
| Context | Phase 1.5 deployment | Config check |
| Categorization | CVF severity levels | Policy audit |
| Risk ID | Confessor agent, CVF codes | Ledger analysis |
| **MEASURE** | | |
| Metrics | ASR, coverage, integrity | CI dashboard |
| Evaluation | pytest, red-team suite | Automated |
| Tracking | Evidence packs | Artifact storage |
| **MANAGE** | | |
| Prioritization | Severity matrix | Response time SLAs |
| Treatment | CI gates | Deployment blocks |
| Response | Automated + human | CVF routing |
| Documentation | Evidence bundles | 90-day retention |

---

## References

1. NIST AI RMF 1.0 (AI 100-1): https://nvlpubs.nist.gov/nistpubs/ai/nist.ai.100-1.pdf
2. ISO/IEC 42001: AI Management Systems
3. EU AI Act: High-Risk System Requirements
4. OWASP GenAI Red-Team Guide: https://genai.owasp.org/resource/genai-red-teaming-guide/

---

## Appendix A: File Locations

| Purpose | File Path |
|---------|-----------|
| Governance config | `Governance/config.py` |
| Policy engine | `sovereign-core/ollama-orchestration/governance/policy.py` |
| Constitutional verifier | `governance.py` |
| Chain verification | `scripts/verify_chain.py` |
| Red-team tests | `tests/red_team/` |
| CI workflow | `.github/workflows/ci.yml` |
| Ledger | `ledger.jsonl` |
| Anchor chain | `DATA/_anchor_chain.json` |
| Evidence store | `evidence_store/` |

---

## Appendix B: Verification Commands

```bash
# Verify hash-chain integrity
python scripts/verify_chain.py --verbose

# Run red-team tests
pytest tests/red_team/ -v

# Generate evidence bundle manually
python scripts/export_evidence_bundle.py

# Check governance configuration
python scripts/validate_governance.py
```
