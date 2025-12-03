# Risk Governance Addendum – Confessor and High-Risk Blocking

**Effective Date:** 2 December 2025
**Scope:** Mission Planning, Risk Assessment, and High-Risk Mission Blocking
**Audience:** Investors, Regulators, Executive Stakeholders, Legal Counsel

---

## 1. Purpose and Scope

This Addendum specifies how mission-level risk is identified, assessed, and enforced for AI-driven plans under the Mission Execution Charter.

It creates a binding rule that **no mission may proceed to execution if classified as HIGH risk** by the independent Confessor agent.

---

## 2. Confessor – Independent Risk Assessment Function

Confessor is a dedicated AI agent whose sole mandate is to assess the risk of mission objectives before execution.

- For every new mission plan, Confessor receives at minimum:
  - A unique mission identifier
  - The mission objective or equivalent high-level description

- Confessor analyzes the objective and returns a structured assessment including:
  - `risk_level`: one of `LOW`, `MEDIUM`, `HIGH`, or `UNKNOWN`
  - `rationale`: a concise explanation of the assigned level

Each assessment is written as a structured event into the **immutable ledger** and linked to the corresponding mission identifier.

---

## 3. Mandatory Risk Gating of Missions

The Planner agent is **prohibited** from executing a mission plan until a Confessor assessment has been obtained or a defined timeout has elapsed.

### 3.1 Planner Obligations

The Planner must:
1. Request a Confessor assessment for every new mission plan
2. Wait for Confessor's response for up to a defined maximum period (default: 60 seconds)

### 3.2 HIGH Risk Handling

If Confessor returns `risk_level = HIGH`:
- The mission plan **must be rejected** and not executed
- A `plan_rejected` event, including Confessor's assessment, must be recorded in the ledger
- The API must return a clear rejection status to the caller

### 3.3 Approved Missions

Only plans with `risk_level` other than `HIGH` (or where no assessment is returned within the timeout under documented fallback conditions) may proceed to task execution.

This converts risk assessment from advisory intelligence into a **binding control point** on execution.

---

## 4. Human Oversight and Intervention

Human operators retain full authority to:

- **Review** Confessor assessments and associated rationale
- **Override or halt** any mission, even if not classified as HIGH, using the existing kill-switch and pause mechanisms defined in the Charter
- **Tighten or relax** risk thresholds over time through governed policy changes, subject to recorded approval and version control

These measures support the requirement that high-risk AI systems must remain subject to effective human oversight and stoppability during use.

### Regulatory Alignment

- EU AI Act Article 14: Human oversight requirements
- ISO/IEC 42001: AI Management System standards
- AIMS compliance framework

---

## 5. Evidence, Audit, and Traceability

For each mission, the following items must be recoverable from the evidence and ledger systems:

| Event Type | Description |
|------------|-------------|
| `plan_created` | The original mission objective and generated plan |
| `risk_assessment` | Confessor's assessment (risk_level and rationale) |
| `plan_approved` / `plan_rejected` | The Planner's decision and reasoning |
| `task_*` | Task delegation, execution, and completion events |
| `kill_switch` | Any human override, kill, or pause actions |

This ensures that decisions to proceed with or block missions are **traceable, auditable, and reproducible** for regulators, auditors, and investors.

### Hash Chain Integrity

All ledger entries are cryptographically hash-chained, providing:
- Tamper detection
- Immutable audit trail
- Verifiable history via `/verify` endpoint

---

## 6. Governance and Change Control

The existence of Confessor, the obligation to obtain risk assessments, and the HIGH-risk blocking rule are part of the **binding governance framework** of the organization.

### 6.1 Protected Elements

Any change to:
- Confessor's mandate
- The definition or handling of HIGH risk
- The requirement to block HIGH-risk missions

**Must be approved** through formal governance (e.g., Board or designated committee), recorded in meeting minutes, and reflected in an updated version of this Addendum.

### 6.2 Version Control

| Version | Date | Change Summary | Approved By |
|---------|------|----------------|-------------|
| 1.0 | 2025-12-02 | Initial addendum | [Pending] |

---

## 7. Technical Implementation Reference

### 7.1 Confessor Endpoint

```
POST /assess_plan
Content-Type: application/json

{
  "mission_id": "M-20251202XXXXXX",
  "objective": "Mission objective text"
}

Response:
{
  "mission_id": "M-20251202XXXXXX",
  "assessment": {
    "risk_level": "MEDIUM",
    "rationale": "Explanation of risk assessment"
  }
}
```

### 7.2 Ledger Events

Risk assessment events follow the standard ledger schema:

```json
{
  "event_type": "risk_assessment",
  "agent": "confessor",
  "target": "M-20251202XXXXXX",
  "outcome": "MEDIUM",
  "metadata": {
    "mission_id": "M-20251202XXXXXX",
    "objective": "...",
    "assessment": { "risk_level": "MEDIUM", "rationale": "..." }
  }
}
```

---

## 8. Enforcement

This Addendum forms an integral part of the Mission Execution Charter and is enforceable on the same basis.

Non-compliance with risk gating requirements constitutes a governance violation subject to:
- Immediate mission suspension
- Mandatory incident review
- Corrective action as determined by governance committee

---

**Document Control**

- **Classification:** Internal / Regulatory
- **Owner:** Governance Committee
- **Review Cycle:** Quarterly or upon material change
- **Related Documents:** Mission Execution Charter, Kill-Switch Protocol, Evidence Retention Policy
