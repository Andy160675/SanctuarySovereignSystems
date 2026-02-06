# Sovereign System Context Glossary

This document clarifies specific terms and references encountered during the Sovereign System deployment.

## 1. 12,000-case campaign
- **Reference:** Found in `scripts\ops\Run-TrinityCampaign.ps1`.
- **Definition:** A bounded Trinity campaign that defaults to running **12,000 agents**. It is used for large-scale strategic simulation and audit.
- **Guardrails:** Operates with safe concurrency and audit-only protections by default.

## 2. Shards (HSM Shards)
- **Reference:** Found in `src\chaos_factor.rs` and `src\chaos_simulator.rs`.
- **Definition:** Hardware Security Module (HSM) key shards. The system requires at least **5 original HSM shards** to be intact/presented for recovery conditions.
- **Role:** Part of the cryptographic sovereignty and recovery protocol.

## 3. Remaining Shards
- **Context:** Likely refers to the uninstantiated or unpresented HSM shards required to meet the quorum (5 shards) for full system recovery or authority restoration.

## 4. Trinity Cluster (Logical Roles)
- **PC-A:** Legislature (Constitutional Core / Camunda)
- **PC-B:** Executive (Orchestration / StackStorm)
- **PC-C:** Judiciary (Verification / Nextflow)

## 5. Pentad Fleet (Physical Roles)
- **EYES (PC1):** Dashboard/Observation
- **BRAIN (PC2):** NAS Integration/Storage
- **HEART (PC3):** Core Operations
- **MIND (PC4):** Intelligence/LLM
- **SPINE (PC5):** Hub/Cold Store (often associated with NAS)

*Last Updated: 2026-02-05*
