# Regulatory Alignment Matrix

**Project:** Phase A: Shadow Assurance Mode  
**Version:** 1.0  
**Date:** 4 February 2026  
**Classification:** INTERNAL — BOARD LEVEL  
**Reference:** SAM-2026-003

---

## 1. Introduction

This document maps the Phase A: Shadow Assurance Mode capabilities to specific regulatory requirements across three key frameworks: PRA Operational Resilience (SS1/21), FCA Consumer Duty (PS21/3), and Model Risk Management (SR 11-7). It demonstrates how the proposed capability addresses regulatory expectations through evidence-based assurance.

---

## 2. PRA Operational Resilience (SS1/21)

### 2.1 Overview

The PRA's Supervisory Statement SS1/21 requires firms to identify important business services, set impact tolerances, and demonstrate the ability to remain within those tolerances during severe but plausible disruption scenarios.

### 2.2 Requirement Mapping

| SS1/21 Reference | Requirement Summary | Phase A Capability | Evidence Type |
|------------------|---------------------|-------------------|---------------|
| **3.1** | Identify important business services | Reconstruction Engine traces decision paths for identified services | Decision Reconstruction Evidence |
| **3.4** | Set impact tolerances | Failure Simulator models behaviour against defined tolerances | Failure Mode Demonstration |
| **4.1** | Map resources supporting important business services | Technical Architecture documents all system components | Architecture Specification |
| **5.1** | Scenario testing | Failure Simulator executes induced failure scenarios | Failure Mode Demonstration |
| **5.3** | Demonstrate ability to remain within impact tolerances | Metrics captured during simulation (detect, respond, recover times) | Failure Mode Demonstration |
| **5.5** | Evidence of testing | Cryptographic receipts for all simulations | Evidence Pack Receipt |
| **6.1** | Self-assessment | Artifact Generator produces regulator-ready reports | Evidence Pack |
| **7.1** | Governance and oversight | Operator Console with RBAC and audit logging | Audit Trail |

### 2.3 Gap Analysis

| Requirement | Current State | Phase A State | Gap Closed |
|-------------|--------------|---------------|------------|
| Scenario testing evidence | Narrative-based | Cryptographic, deterministic | ✓ Yes |
| Impact tolerance demonstration | Assertion-based | Metrics-based with evidence | ✓ Yes |
| Audit trail | Manual logs | Immutable hash chain | ✓ Yes |

---

## 3. FCA Consumer Duty (PS21/3)

### 3.1 Overview

The FCA's Consumer Duty (PS21/3) requires firms to act to deliver good outcomes for retail customers, with specific focus on products and services, price and value, consumer understanding, and consumer support.

### 3.2 Requirement Mapping

| PS21/3 Reference | Requirement Summary | Phase A Capability | Evidence Type |
|------------------|---------------------|-------------------|---------------|
| **4.3** | Products and services designed to meet needs | Reconstruction Engine traces product/pricing decisions | Decision Reconstruction Evidence |
| **4.10** | Price and value assessment | Reconstruction of pricing decision paths with full lineage | Decision Reconstruction Evidence |
| **4.15** | Consumer understanding | Reconstruction of customer journey decision points | Decision Reconstruction Evidence |
| **4.20** | Consumer support | Evidence of support-related decisions and outcomes | Decision Reconstruction Evidence |
| **5.1** | Monitoring outcomes | Artifact Generator produces outcome analysis reports | Evidence Pack |
| **5.5** | Fair treatment evidence | Deterministic reconstruction of treatment decisions | Decision Reconstruction Evidence |
| **6.1** | Board oversight | Operator Console provides governance controls | Audit Trail |

### 3.3 Gap Analysis

| Requirement | Current State | Phase A State | Gap Closed |
|-------------|--------------|---------------|------------|
| Decision lineage | Partial, manual | Complete, deterministic | ✓ Yes |
| Fair treatment evidence | Assertion-based | Reconstruction-based | ✓ Yes |
| Outcome monitoring | Periodic reports | On-demand evidence generation | ✓ Yes |

---

## 4. Model Risk Management (SR 11-7)

### 4.1 Overview

SR 11-7 (Guidance on Model Risk Management) establishes supervisory expectations for effective model risk management, including model development, implementation, and use, as well as validation and governance.

### 4.2 Requirement Mapping

| SR 11-7 Reference | Requirement Summary | Phase A Capability | Evidence Type |
|-------------------|---------------------|-------------------|---------------|
| **II.A** | Model development documentation | Reconstruction Engine documents decision logic | Decision Reconstruction Evidence |
| **II.B** | Implementation testing | Failure Simulator tests model behaviour under stress | Failure Mode Demonstration |
| **III.A** | Effective challenge | Independent reconstruction verifies model outputs | Decision Reconstruction Evidence |
| **III.B** | Ongoing monitoring | Evidence Ledger maintains continuous audit trail | Audit Trail |
| **IV.A** | Governance and controls | Operator Console with RBAC and approval workflows | Audit Trail |
| **IV.B** | Model inventory | Reconstruction Engine catalogues decision components | Architecture Specification |
| **V.A** | Validation independence | Shadow layer operates independently of production | Architecture Specification |
| **V.B** | Full decision lineage | Complete path reconstruction from input to output | Decision Reconstruction Evidence |

### 4.3 Gap Analysis

| Requirement | Current State | Phase A State | Gap Closed |
|-------------|--------------|---------------|------------|
| Full decision lineage | Test results only | Complete path reconstruction | ✓ Yes |
| Independent validation | Manual review | Automated, deterministic verification | ✓ Yes |
| Quantification enforcement | Assertion-based | Evidence-based with hash verification | ✓ Yes |

---

## 5. Cross-Regulatory Summary

### 5.1 Capability Coverage Matrix

| Phase A Capability | PRA SS1/21 | FCA PS21/3 | SR 11-7 |
|--------------------|------------|------------|---------|
| **Reconstruction Engine** | ✓ | ✓ | ✓ |
| **Evidence Ledger** | ✓ | ✓ | ✓ |
| **Failure Simulator** | ✓ | — | ✓ |
| **Artifact Generator** | ✓ | ✓ | ✓ |
| **Operator Console** | ✓ | ✓ | ✓ |

### 5.2 Evidence Type Coverage

| Evidence Type | PRA SS1/21 | FCA PS21/3 | SR 11-7 |
|---------------|------------|------------|---------|
| **Decision Reconstruction Evidence** | ✓ | ✓ | ✓ |
| **Failure Mode Demonstration** | ✓ | — | ✓ |
| **Evidence Pack Receipt** | ✓ | ✓ | ✓ |
| **Audit Trail** | ✓ | ✓ | ✓ |

---

## 6. Language Discipline

All Phase A outputs use regulator-safe language to avoid overclaim:

| Permitted Verbs | Avoided Verbs |
|-----------------|---------------|
| Demonstrates | Guarantees |
| Reconstructs | Proves |
| Verifies | Certifies |
| Records | Assures |
| Evidences | Warrants |
| Shows | Confirms |
| Indicates | Establishes |

---

## 7. Conclusion

Phase A: Shadow Assurance Mode provides comprehensive coverage across the three primary regulatory frameworks relevant to Admiral's operations. The capability addresses persistent gaps in evidence quality by replacing narrative-based assertions with deterministic, cryptographically-sealed evidence.

---

**Prepared by:** Sovereign Operations  
**Reviewed by:** [Pending]
