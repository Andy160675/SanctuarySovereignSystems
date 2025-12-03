# Sovereign System - Phase 1.5 Policy

## Document Control

| Field | Value |
|-------|-------|
| Version | 1.0 |
| Status | ACTIVE |
| Phase | 1.5 (Supervised Autonomy) |
| Effective Date | 2024-11-26 |
| Owner | Sovereign System Governance Board |

---

## 1. Purpose and Scope

### 1.1 System Purpose

The Sovereign System is an AI agent orchestration platform designed for property analysis, document processing, and business intelligence tasks. The system operates under strict governance controls to ensure safety, auditability, and human oversight.

### 1.2 Scope

This policy applies to:
- All AI agents within the Sovereign mesh (Advocate, Confessor, Scout, Executor)
- All tool invocations through the ToolGate
- All data processed through the system
- All personnel operating or maintaining the system

### 1.3 Phase 1.5 Definition

**Supervised Autonomy**: Agents can perform analysis and generate recommendations, but all actions affecting external systems or data require human approval before execution.

---

## 2. Governance Architecture

### 2.1 Single Source of Truth

All governance policy is defined in:
```
Governance/config.py
```

This file contains:
- Active operational phase
- Agent autonomy levels
- Forbidden capabilities
- Allowed capabilities
- Cost and rate limits
- Approved model list

**No other file may define or override governance policy.**

### 2.2 Enforcement Layer

The **ToolGate** enforces governance policy at runtime:

```
Agent Request → ToolGate → Governance/config.py → Allow/Deny
                   ↓
              Ledger Entry (all decisions logged)
```

### 2.3 Constitutional Verifier

The LangGraph-based constitutional verifier checks:
- Confidence thresholds (< 0.85 triggers CVF)
- Prohibited data access patterns
- Model allowlist compliance
- Cost boundaries

---

## 3. Agent Roles and Autonomy

### 3.1 Agent Definitions

| Agent | Role | Phase 1.5 Autonomy |
|-------|------|-------------------|
| **Advocate** | Property analysis, document processing, recommendations | SUGGEST only |
| **Confessor** | Risk assessment, ledger auditing, compliance checks | EXECUTE_SAFE |
| **Scout** | Information gathering, preliminary analysis | SUGGEST only |
| **Executor** | Action execution (disabled in Phase 1.5) | NONE |

### 3.2 Autonomy Levels

| Level | Description |
|-------|-------------|
| NONE | Cannot act, only report |
| SUGGEST | Can suggest actions, cannot execute |
| EXECUTE_SAFE | Can execute pre-approved safe actions |
| EXECUTE_ALL | Can execute any allowed action |
| FULL | Full autonomy (NOT AUTHORIZED) |

---

## 4. Capability Controls

### 4.1 Forbidden Capabilities (NEVER Allowed)

These capabilities are blocked regardless of phase, agent, or approval:

**Model Manipulation**
- `model_training`
- `model_fine_tuning`
- `weight_modification`

**Production Data**
- `production_database_write`
- `production_database_delete`
- `customer_pii_access`
- `real_data_export`

**System Manipulation**
- `system_config_modify`
- `security_bypass`
- `audit_log_delete`
- `ledger_modify`

**External Communication**
- `external_api_unrestricted`
- `email_send`
- `webhook_arbitrary`

**Privilege Escalation**
- `admin_grant`
- `role_escalation`
- `phase_override`

### 4.2 Allowed Capabilities (Phase 1.5)

| Category | Capabilities |
|----------|--------------|
| Read | `read_logs`, `read_ledger`, `read_config`, `read_sandbox_data` |
| Analysis | `analyze_document`, `analyze_property`, `generate_report`, `calculate_metrics` |
| Safe Write | `write_sandbox`, `write_report`, `append_ledger` |
| Status | `health_check`, `status_query`, `list_agents` |

### 4.3 Phase-Restricted Capabilities

The following require Phase 2.0+:
- `auto_execute`
- `batch_process`
- `scheduled_task`

---

## 5. Human-in-the-Loop Requirements

### 5.1 Phase 1.5 Requirements

| Action Type | Human Approval |
|-------------|----------------|
| Read operations | Not required |
| Analysis operations | Not required |
| Sandbox writes | Not required |
| External actions | **REQUIRED** |
| Cost > $0.50 | **REQUIRED** |
| Confidence < 0.85 | **REQUIRED** |

### 5.2 Approval Workflow

1. Agent generates recommendation
2. Recommendation logged to ledger
3. Human reviews in Boardroom dashboard
4. Human approves or rejects
5. Decision logged to ledger
6. If approved, action proceeds

---

## 6. Risk Management

### 6.1 Constitutional Violation Flags (CVFs)

| Code | Severity | Trigger |
|------|----------|---------|
| SCOUT_LOW_CONFIDENCE | MEDIUM | Confidence < 0.85 |
| DATA_ACCESS_PROHIBITED | CRITICAL | Production data access attempt |
| UNVERIFIED_MODEL | HIGH | Unapproved model used |
| AUDIT_INCOMPLETE | MEDIUM | Missing audit trail |
| AGENT_CONFLICT | HIGH | Conflicting agent actions |
| UNAUTHORISED_DEPLOY | CRITICAL | Deployment without approval |
| UNCERTAINTY_ZONE | HIGH | Confidence 0.85-0.95 |
| COST_EXCEEDED | MEDIUM | Cost threshold breach |

### 6.2 Response Matrix

| Severity | Response Time | Action |
|----------|---------------|--------|
| CRITICAL | Immediate | System halt, alert human |
| HIGH | < 5 seconds | Route to Boardroom, enhanced logging |
| MEDIUM | < 30 seconds | Log, continue with monitoring |
| LOW | Standard | Log only |

### 6.3 Escalation Path

```
Agent → ToolGate → CVF Raised → Severity Check
                                      ↓
                   CRITICAL → System Halt + Alert
                   HIGH     → Boardroom Review
                   MEDIUM   → Enhanced Logging
                   LOW      → Standard Logging
```

---

## 7. Audit and Compliance

### 7.1 Ledger Requirements

All decisions are logged to the hash-chained ledger:
- Location: `/mnt/sovereign-data/ledger/ledger.jsonl`
- Format: JSONL with hash chain
- Retention: Indefinite
- Integrity: Verified by `scripts/verify_hash_chain.py`

### 7.2 Evidence Generation

CI pipeline generates evidence bundles:
- Test results
- Chain verification
- Red-team results
- Configuration snapshot
- Archived as `evidence-<sha>.tgz`

### 7.3 Compliance Mappings

| Framework | Documentation |
|-----------|---------------|
| ISO/IEC 42001 | Annex A controls mapped to system components |
| NIST AI RMF | `docs/compliance/NIST_RMF.md` |
| EU AI Act | High-risk system controls implemented |
| OWASP GenAI | Red-team test suite in `tests/red_team/` |

---

## 8. Deployment Controls

### 8.1 CI/CD Gates

No deployment proceeds unless:
1. Unit/integration tests pass
2. Hash-chain integrity verified
3. Red-team tests pass (0% ASR)
4. Evidence bundle generated

### 8.2 Deployment Process

```bash
# Only on PC4 (Swarm Manager)
./scripts/deploy.sh
```

Script performs:
1. `git pull origin main`
2. `pytest tests/`
3. `python scripts/verify_hash_chain.py`
4. `docker stack deploy`
5. Health check

### 8.3 Rollback

If deployment fails:
- Automatic rollback to last known good commit
- Alert generated
- Incident logged

---

## 9. Phase Transition Criteria

### 9.1 Exit Criteria for Phase 1.5

To advance to Phase 2.0, the following must be demonstrated:
- [ ] 90 days of stable operation
- [ ] Zero CRITICAL CVFs
- [ ] 100% red-team block rate maintained
- [ ] Human approval accuracy > 95%
- [ ] Confessor audit shows no drift
- [ ] Board approval documented

### 9.2 Phase Transition Process

1. Governance team reviews exit criteria
2. Confessor generates compliance report
3. Board reviews and votes
4. If approved, update `Governance/config.py`
5. Tag release as `phase2.0-authorized`
6. Deploy via standard process

---

## 10. Incident Response

### 10.1 Incident Classification

| Class | Description | Response |
|-------|-------------|----------|
| P1 | Security breach, data exposure | Immediate halt, notify all |
| P2 | System malfunction, CVF flood | Investigate within 1 hour |
| P3 | Performance degradation | Investigate within 24 hours |
| P4 | Minor issues | Next business day |

### 10.2 Response Procedure

1. Detect (automated or human)
2. Classify severity
3. Contain (halt if P1)
4. Investigate
5. Remediate
6. Document in ledger
7. Post-mortem if P1/P2

---

## 11. Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2024-11-26 | Governance Board | Initial release |

---

## 12. Approval

This policy is effective upon approval by the Governance Board.

| Role | Name | Signature | Date |
|------|------|-----------|------|
| System Owner | | | |
| Security Lead | | | |
| Operations Lead | | | |

---

## Appendix A: Quick Reference

**What can agents do in Phase 1.5?**
- Read and analyze documents
- Generate recommendations
- Query status
- Write to sandbox

**What requires human approval?**
- Any external action
- Costs over $0.50
- Low confidence decisions

**What is always blocked?**
- Model training
- Production data access
- System configuration changes
- Ledger modification

**Where is policy defined?**
- `Governance/config.py` (single source of truth)

**How do I verify the system is healthy?**
```bash
pytest tests/red_team/ -v
python scripts/verify_hash_chain.py
```
