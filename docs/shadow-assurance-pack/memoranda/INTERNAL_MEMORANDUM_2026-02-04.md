# Internal Memorandum

**To:** Risk Committee, Audit Committee  
**From:** Chief Operating Officer  
**Date:** 4 February 2026  
**Subject:** Phase A Shadow Assurance Mode — Technical Justification and Implementation Proposal  
**Classification:** INTERNAL — BOARD LEVEL  
**Reference:** SAM-2026-001

---

## 1. Executive Summary

This memorandum provides the technical justification and implementation detail supporting the Risk Committee One-Pager requesting approval for Phase A: Shadow Assurance Mode. The proposed capability addresses three persistent regulatory exposure areas through a verification-only, non-production assurance layer that generates audit-grade evidence on demand.

**Investment:** £150,000 (one-time)  
**Duration:** 12 working days  
**Operational Impact:** Zero  
**Production Integration:** None  

---

## 2. Problem Statement

### 2.1 Current State

Admiral currently relies on narrative-based reconstruction when responding to regulatory inquiries, incident investigations, or audit requests. This approach presents three material weaknesses:

| Weakness | Current State | Regulatory Exposure |
|----------|--------------|---------------------|
| **Post-incident reconstruction** | Testimony and log analysis | PRA SS1/21: "Firms must be able to demonstrate..." |
| **Operational resilience evidence** | Plans and procedures documented | FCA PS21/3: "...evidence of testing and response" |
| **Model/pricing governance** | Test results and approvals | SR 11-7: "...full decision lineage" |

### 2.2 Gap Analysis

The gap is not capability but **evidence quality**. Current approaches produce:

- **Narrative accounts** rather than deterministic reconstruction
- **Compliance assertions** rather than verifiable proofs
- **Point-in-time snapshots** rather than continuous audit trails

Regulators increasingly expect **evidence over opinion** and **reconstruction over testimony**.

---

## 3. Proposed Solution

### 3.1 Shadow Assurance Mode (Phase A)

A non-production, verification-only capability that:

1. **Reconstructs** decision paths deterministically from historical data
2. **Generates** cryptographic, tamper-evident evidence chains
3. **Demonstrates** system behaviour under induced failure conditions
4. **Produces** regulator-ready artifacts on demand

### 3.2 Explicit Boundaries

| Capability | Phase A Status |
|------------|---------------|
| Decision reconstruction | ✓ Included |
| Evidence generation | ✓ Included |
| Failure-mode demonstration | ✓ Included |
| Artifact production | ✓ Included |
| Production integration | ✗ Excluded |
| Real-time mirroring | ✗ Excluded |
| Live customer data | ✗ Excluded |
| Decision enforcement | ✗ Excluded |
| Policy control | ✗ Excluded |

### 3.3 Core Principle

> **Evidence over opinion; reconstruction over testimony.**

Every output is cryptographically sealed, hash-chained, and independently verifiable.

---

## 4. Technical Architecture

### 4.1 Component Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    SHADOW ASSURANCE LAYER                    │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐ │
│  │  Reconstruction │  │    Evidence     │  │   Failure    │ │
│  │     Engine      │  │    Ledger       │  │  Simulator   │ │
│  └────────┬────────┘  └────────┬────────┘  └──────┬───────┘ │
│           │                    │                   │         │
│           └────────────────────┼───────────────────┘         │
│                                │                             │
│                    ┌───────────▼───────────┐                 │
│                    │   Artifact Generator  │                 │
│                    └───────────┬───────────┘                 │
│                                │                             │
└────────────────────────────────┼─────────────────────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │  Regulator-Ready Output │
                    │  (PDF, JSON, Evidence)  │
                    └─────────────────────────┘
```

### 4.2 Data Flow

1. **Input:** Historical decision data (anonymised, non-production copy)
2. **Process:** Deterministic reconstruction with cryptographic attestation
3. **Output:** Sealed evidence packages with verification receipts

### 4.3 Isolation Guarantees

- **Network:** Air-gapped from production systems
- **Data:** Anonymised historical snapshots only
- **Access:** Operator console with role-based controls
- **Audit:** Complete action logging with hash chains

---

## 5. Regulatory Alignment

### 5.1 PRA Operational Resilience (SS1/21)

| Requirement | Phase A Capability |
|-------------|-------------------|
| "Demonstrate ability to remain within impact tolerances" | Failure-mode simulation with evidence |
| "Evidence of testing" | Cryptographic test receipts |
| "Recovery capability" | Reconstruction of recovery paths |

### 5.2 FCA Consumer Duty (PS21/3)

| Requirement | Phase A Capability |
|-------------|-------------------|
| "Fair treatment evidence" | Decision lineage reconstruction |
| "Customer journey transparency" | Path reconstruction with attestation |
| "Outcome monitoring" | Evidence-backed outcome analysis |

### 5.3 Model Risk (SR 11-7)

| Requirement | Phase A Capability |
|-------------|-------------------|
| "Full decision lineage" | Deterministic reconstruction |
| "Quantification enforcement" | Evidence of calculation paths |
| "Independent validation" | Cryptographic verification |

### 5.4 Language Discipline

All outputs use regulator-safe language:

| Permitted | Avoided |
|-----------|---------|
| Demonstrates | Guarantees |
| Reconstructs | Proves |
| Verifies | Certifies |
| Records | Assures |
| Evidences | Warrants |

---

## 6. Cost-Benefit Analysis

### 6.1 Investment

| Component | Cost |
|-----------|------|
| Development (12 days, specialist pool) | £120,000 |
| Infrastructure (sandbox environment) | £15,000 |
| Documentation and training | £10,000 |
| Contingency (5%) | £5,000 |
| **Total** | **£150,000** |

### 6.2 Comparator

Traditional development approach:
- Duration: ~20 weeks
- Cost: ~£300,000+
- Risk: Higher (sequential dependencies)

### 6.3 Risk Avoidance Value (5-Year, Conservative)

| Risk Category | Annual Exposure | Mitigation | 5-Year Value |
|---------------|-----------------|------------|--------------|
| Regulatory fine avoidance | £100,000 | 80% | £400,000 |
| Audit remediation savings | £50,000 | 70% | £175,000 |
| Incident response efficiency | £40,000 | 75% | £150,000 |
| **Total** | | | **£725,000** |

### 6.4 Return on Investment

- **Investment:** £150,000
- **5-Year Value:** £725,000
- **ROI:** 4.8x
- **Payback:** <12 months

---

## 7. Delivery Model

### 7.1 Approach

Parallel specialist agent pools under single orchestration:

- **Pool 1:** Reconstruction Engine (3 agents)
- **Pool 2:** Evidence Ledger (2 agents)
- **Pool 3:** Failure Simulator (2 agents)
- **Pool 4:** Artifact Generator (2 agents)
- **Orchestrator:** Integration and quality assurance

### 7.2 Timeline

| Day | Milestone |
|-----|-----------|
| 1-2 | Infrastructure setup, data preparation |
| 3-5 | Reconstruction Engine complete |
| 6-7 | Evidence Ledger complete |
| 8-9 | Failure Simulator complete |
| 10-11 | Artifact Generator complete |
| 12 | Integration testing, documentation, handover |

### 7.3 Quality Gates

Each component requires:
- Unit test coverage >90%
- Integration test pass
- Security review sign-off
- Documentation complete

---

## 8. Risk Assessment

### 8.1 Project Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Data quality issues | Medium | Medium | Pre-validation in Days 1-2 |
| Integration complexity | Low | Medium | Modular architecture |
| Scope creep | Medium | High | Explicit Phase A boundaries |
| Resource availability | Low | Medium | Parallel pool redundancy |

### 8.2 Operational Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Production interference | None | N/A | Air-gapped by design |
| Data leakage | Low | High | Anonymisation, access controls |
| Misuse of outputs | Low | Medium | Role-based access, audit logging |

---

## 9. Governance

### 9.1 Ownership

- **Owner:** Chief Operating Officer
- **Delivery Lead:** [To be assigned]
- **Technical Lead:** [To be assigned]

### 9.2 Oversight

- **Risk Committee:** Informed (this memorandum)
- **Audit Committee:** On request
- **Board:** Not required for Phase A

### 9.3 Expansion Controls

Any expansion beyond Phase A requires:
- Explicit Risk Committee approval
- Updated business case
- Production integration assessment
- Data protection impact assessment

---

## 10. Decision Requested

Approve £150,000 to proceed with Phase A (Shadow Assurance Mode) only.

- Start: Immediately upon approval
- Complete: 12 working days from start
- Deliverable: Operational shadow assurance capability with documentation

---

## 11. Appendices

The following supporting documents are available upon request:

- **Appendix A:** Technical Architecture Specification
- **Appendix B:** Regulatory Alignment Matrix
- **Appendix C:** Detailed Cost-Benefit Analysis
- **Appendix D:** Risk Register
- **Appendix E:** 12-Day Delivery Schedule
- **Appendix F:** Regulator-Ready Artifact Templates

---

**Prepared by:** Sovereign Operations  
**Reviewed by:** [Pending]  
**Approved by:** [Pending Risk Committee Decision]

---

*This memorandum is classified INTERNAL — BOARD LEVEL and should not be distributed outside the intended recipients without explicit authorisation.*
