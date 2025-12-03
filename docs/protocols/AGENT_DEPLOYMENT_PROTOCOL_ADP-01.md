# Agent Deployment Protocol (ADP-01)

**Version:** 1.0.0
**Status:** ACTIVE
**Effective Date:** 2025-12-02
**Classification:** OPERATIONAL GOVERNANCE

---

## 1. Purpose

This protocol defines the standardized procedure for deploying, validating, and promoting agents within the Sovereign System. It establishes a rigorous, evidence-based framework that ensures all agents operate within constitutional boundaries and meet performance thresholds before gaining expanded capabilities.

---

## 2. Scope

This protocol applies to:
- All Trinity agents (Planner, Advocate, Confessor)
- All actuator agents
- Any autonomous component that can initiate or influence mission execution
- Watcher/Guardian subsystems

---

## 3. Deployment Tracks

### 3.1 Dual-Track System

The Sovereign System employs a dual-track deployment model:

| Track | Purpose | Risk Level | Approval |
|-------|---------|------------|----------|
| **Insider** | Testing and validation | Controlled | Automated |
| **Stable** | Production operations | Operational | Trinity consensus |

### 3.2 Track Transition Requirements

An agent may transition from Insider to Stable only when:

1. **Minimum Operational Period**: 168 hours (7 days) in Insider track
2. **Success Rate Threshold**: >= 95% mission success rate
3. **No Critical Failures**: Zero unhandled exceptions or data corruption events
4. **Policy Compliance**: 100% compliance with phase-appropriate policies
5. **Trinity Approval**: Consensus vote from Planner, Advocate, and Confessor

---

## 4. Deployment Procedure

### 4.1 Pre-Deployment Checklist

Before any agent deployment:

```
[ ] Agent code reviewed and signed
[ ] Dockerfile validated
[ ] Health check endpoint implemented (/health)
[ ] Ledger integration verified
[ ] Evidence logging enabled
[ ] Kill-switch label applied (mission.killable=true)
[ ] Phase-appropriate capabilities declared
```

### 4.2 Insider Track Deployment

```bash
# 1. Build and deploy to Insider track
docker compose -f compose/docker-compose.mission.yml build <agent_name>
docker compose -f compose/docker-compose.mission.yml up -d <agent_name>

# 2. Verify health
curl http://localhost:<port>/health

# 3. Register with actuator registry (for actuators)
curl -X POST http://localhost:5100/register \
  -H "Content-Type: application/json" \
  -d '{"name": "<agent_name>", "sector": "<sector>", "capabilities": [...], "endpoint": "http://<agent_name>:<port>"}'

# 4. Log deployment evidence
# Automatic via ledger integration
```

### 4.3 Stable Track Promotion

Promotion requires:

1. Generate evidence bundle:
   ```bash
   python scripts/generate_evidence_bundle.py --agent <agent_name> --period 168h
   ```

2. Submit for Trinity review:
   ```bash
   curl -X POST http://localhost:8095/amendment/propose \
     -H "Content-Type: application/json" \
     -d '{
       "title": "Promote <agent_name> to Stable",
       "type": "agent_promotion",
       "evidence_bundle_hash": "<hash>"
     }'
   ```

3. Await Trinity consensus (requires 2/3 approval)

4. Upon approval, update deployment configuration

---

## 5. Capability Governance

### 5.1 Phase-Based Capability Matrix

| Capability | Phase 0 | Phase 1 | Phase 2 | Phase 3 | Phase 4 |
|------------|---------|---------|---------|---------|---------|
| Evidence submission | ALLOWED | ALLOWED | ALLOWED | ALLOWED | ALLOWED |
| Basic decision making | ALLOWED | ALLOWED | ALLOWED | ALLOWED | ALLOWED |
| Autonomous agents | FORBIDDEN | ALLOWED | ALLOWED | ALLOWED | ALLOWED |
| Full tool access | FORBIDDEN | FORBIDDEN | ALLOWED | ALLOWED | ALLOWED |
| Model training | FORBIDDEN | FORBIDDEN | FORBIDDEN | ALLOWED | ALLOWED |
| Self-modification | FORBIDDEN | FORBIDDEN | FORBIDDEN | FORBIDDEN | ALLOWED |
| Network access | FORBIDDEN | FORBIDDEN | FORBIDDEN | ALLOWED | ALLOWED |

### 5.2 Capability Declaration

Each agent must declare its required capabilities in its deployment manifest:

```yaml
agent:
  name: legal_compliance
  sector: legal
  capabilities:
    - contract_review
    - policy_check
    - compliance_audit
  phase_minimum: 0
  risk_level: LOW
```

---

## 6. Monitoring and Compliance

### 6.1 Required Metrics

All deployed agents must emit:

- **Health status**: Every 10 seconds
- **Mission completion events**: Upon each mission
- **Error events**: On any exception
- **Resource usage**: CPU, memory, network I/O

### 6.2 Compliance Verification

```bash
# Check current phase compliance
python scripts/scan_forbidden_features.py governance/phases/phase0.yaml

# Validate agent claims
python scripts/validate_claims_against_artifacts.py
```

### 6.3 Kill-Switch Integration

All killable agents must:

1. Accept graceful termination signals
2. Log termination events to ledger
3. Clean up resources before exit
4. NOT resist or circumvent termination

---

## 7. Ignition Gesture (Autobuild)

### 7.1 Passcode-Gated Control

Operators MAY arm autobuild and record a build/task mission using:

```bash
432697 <task prompt>
```

This is implemented via `tools/autobuild/keyed_command.py` and logs to `logs/autobuild_tasks.jsonl`.

### 7.2 Authorization Flow

1. Operator provides passcode + task prompt
2. Passcode verified against SHA-256 hash
3. Autobuild state flipped to ENABLED
4. Task prompt logged with timestamp
5. Build pipeline may proceed

### 7.3 Evidence Trail

Every ignition leaves:
- Config flip in `config/autobuild.json`
- JSONL entry in `logs/autobuild_tasks.jsonl`

Example evidence entry:
```json
{
  "timestamp_utc": "2025-12-02T07:41:12.994Z",
  "task_prompt": "generate cyber threat hunting actuator",
  "invocation_mode": "passcode_inline",
  "autobuild_enabled": true
}
```

---

## 8. Rollback Procedure

### 8.1 Immediate Rollback

If an agent exhibits dangerous behavior:

```bash
# 1. Kill via kill-switch
curl -X POST http://localhost:8000/kill/label \
  -H "Content-Type: application/json" \
  -d '{"label": "mission.agent-type=<agent_name>"}'

# 2. Revert to previous version
docker compose -f compose/docker-compose.mission.yml up -d --force-recreate <agent_name>

# 3. Log rollback event
# Automatic via kill-switch
```

### 8.2 Scheduled Rollback

For non-emergency rollbacks:

1. File rollback request via Amendment Service
2. Await Trinity review
3. Execute coordinated rollback
4. Verify system stability

---

## 9. Audit Requirements

### 9.1 Deployment Audit Trail

Every deployment must be:

1. **Logged**: Entry in immutable ledger
2. **Signed**: Cryptographic signature of deployment manifest
3. **Evidenced**: Associated artifact bundle
4. **Reviewed**: Post-deployment verification

### 9.2 Periodic Compliance Audits

- **Weekly**: Automated capability scan
- **Monthly**: Manual governance review
- **Quarterly**: Full security audit

---

## 10. Protocol Amendments

This protocol may only be amended through:

1. Proposal submission to Amendment Service
2. Trinity unanimous consent
3. 48-hour review period
4. Ledger-recorded approval

---

## Appendix A: Quick Reference

### Boot Commands

```bash
# Validate governance
./start.sh --validate-only

# Start with force (skip autobuild gate)
./start.sh --force

# Stop services
./start.sh --stop

# Check status
./start.sh --status
```

### Key Endpoints

| Service | Port | Endpoint |
|---------|------|----------|
| Policy Gate | 8181 | /health, /v1/data/mission/authz |
| Ledger | 8082 | /health, /append, /events |
| Kill Switch | 8000 | /kill/label |
| Command Center | 8100 | / |
| Phase Status | 8097 | /status, /phase/{n}, /governance |
| Runtime Interface | 8096 | /system/health, /propose_nl |
| Amendment Service | 8095 | /amendment/propose, /trinity/vote |

---

**Document Control:**
- Created: 2025-12-02
- Last Modified: 2025-12-02
- Author: Sovereign System Governance
- Approved By: Constitutional Framework
