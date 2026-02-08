# ROADMAP: Season 3 Extensions

## Document ID: CSS-GOV-DOC-004
## Governed by: CODEOWNERS (steward approval required for amendments)

---

## Registration Protocol

To propose a new extension, submit a PR amending this file with a new entry in the registry below. The PR must be approved by a designated steward per `CODEOWNERS`. Upon approval, create the extension directory at `sovereign_engine/extensions/S3-EXT-XXX/` with a compliant `EXT_SPEC.md`.

---

## Extension Registry

### S3-EXT-000a: Constitutional Enforcer
- **Purpose:** Automated CI gate enforcing kernel regression and CODEOWNERS compliance on every PR
- **Pricing:** Infrastructure (not customer-facing)
- **Owner:** Andy Jones
- **Status:** PREREQUISITE — must be operational before any other extension
- **Priority:** IMMEDIATE

### S3-EXT-000b: Zero-Trust Evidence Chain
- **Purpose:** Automated evidence generation with SHA-256 hashing, RFC-3161 timestamps, and append-only ledger
- **Pricing:** Infrastructure (not customer-facing)
- **Owner:** Andy Jones
- **Status:** PREREQUISITE — must be operational before any other extension
- **Priority:** IMMEDIATE

### S3-EXT-001: AGI Rental
- **Purpose:** Dedicated AI agent compute rental by the hour within sovereign workspace
- **Pricing:** Pay-per-hour (metered)
- **Owner:** TBD
- **Status:** PROPOSED
- **Priority:** HIGH

### S3-EXT-002: PIOPL Tools
- **Purpose:** Personal Intelligence Operating Partner Links — persistent context and knowledge base integration
- **Pricing:** Monthly subscription
- **Owner:** TBD
- **Status:** PROPOSED
- **Priority:** HIGH

### S3-EXT-003: Truth Tools
- **Purpose:** Automated claim verification, contradiction detection, court-admissible evidence packaging
- **Pricing:** Monthly subscription
- **Owner:** TBD
- **Status:** PROPOSED
- **Priority:** HIGH

### S3-EXT-004: Pathology Detector
- **Purpose:** System health monitoring and anomaly detection (promoted from Season 2 candidate)
- **Pricing:** Monthly subscription
- **Owner:** TBD
- **Status:** PROPOSED — candidate code exists in `sovereign_engine/candidates/pathology_detector.py`
- **Priority:** MEDIUM

### S3-EXT-005: Sovereign Sync
- **Purpose:** Multi-node mesh synchronisation with conflict resolution and offline-first operation
- **Pricing:** Monthly subscription
- **Owner:** TBD
- **Status:** PROPOSED — candidate code exists in `sovereign_engine/candidates/sovereign_sync.py`
- **Priority:** MEDIUM

### S3-EXT-006: Property Intelligence
- **Purpose:** Automated property sourcing with Sovereign Value Score and Truth Tools integration
- **Pricing:** Pay-per-lead
- **Owner:** TBD
- **Status:** PROPOSED
- **Priority:** MEDIUM

### S3-EXT-007: Governance Reporter
- **Purpose:** Automated SIOP packets, constitutional health reports, KPI aggregation
- **Pricing:** Monthly subscription
- **Owner:** TBD
- **Status:** PROPOSED
- **Priority:** LOW

### S3-EXT-008: Deliberation Templates
- **Purpose:** Pre-built proposal templates for common governance scenarios
- **Pricing:** One-time purchase
- **Owner:** TBD
- **Status:** PROPOSED
- **Priority:** LOW

### S3-EXT-009: Voice Interface
- **Purpose:** Speech-to-text proposals and text-to-speech deliberation readback
- **Pricing:** Monthly subscription
- **Owner:** TBD
- **Status:** PROPOSED
- **Priority:** LOW

### S3-EXT-010: Evidence Vault
- **Purpose:** Enhanced long-term archival with chain-of-custody and legal system integration
- **Pricing:** Monthly subscription + storage
- **Owner:** TBD
- **Status:** PROPOSED
- **Priority:** MEDIUM

---

## Status Definitions

| Status | Meaning |
|--------|---------|
| PREREQUISITE | Must be operational before other extensions can proceed |
| PROPOSED | Registered in roadmap, awaiting `EXT_SPEC.md` and development |
| IN REVIEW | `EXT_SPEC.md` submitted, undergoing governance merge checklist |
| APPROVED | Passed all gates, merged and available for activation |
| ACTIVE | Live in production, available to customers |
| DEPRECATED | Scheduled for removal, no new activations |
| WITHDRAWN | Removed from roadmap |

---

*Amendments to this file require steward approval via CODEOWNERS.*
