# CHANGELOG

All notable changes to the CSS controlled document set.

Format: [Semantic Versioning](https://semver.org/). Each document version increments independently via SIP + LT vote.

---

## [Unreleased]

### Pending LT Vote
- CSS-OPS-DOC-003 v1.0 — Post-SIP Autonomous Execution Engine
- CSS-OPS-DOC-004 v1.0 — PIOPL Agent Deployment Engine
- CSS-OPS-DOC-005 v1.0 — PIOPL Enterprise Operating Plan
- CSS-OPS-DOC-006 v1.0 — Meeting Structures, Escalation Paths & Andon System

All four documents are DRAFT — FOR LT REVIEW. They become constitutionally binding upon 3/3 LT vote.

---

## 2026-02-17 — Initial Commit

### Added
- CSS-OPS-DOC-003: SIP lifecycle, 4 human touchpoints, 9-field atomic task schema, escalation ladder, evidence requirements, weekly gate protocol, failure modes, anti-pattern kills
- CSS-OPS-DOC-004: 4-block agent profile schema, 3-tier runtime, capability tokens, unit economics (break-even 305–877 agents), behaviour scoring, three-ledger revenue assurance, 4-phase scaling pathway
- CSS-OPS-DOC-005: 7-division enterprise (D1–D7), 25 agent roles, SIP-001 specification (5-day sprint), pre-conditions, 10 atomic tasks, enterprise hierarchy, ChatGPT concept replacement map
- CSS-OPS-DOC-006: 3 meeting types (daily/weekly/monthly), 4-level escalation ladder, standard message format, 5 blocker types, 3-level Andon system, 12 triggers, 6-step response protocol, integration map
- CSS-DOC-REGISTER-001: Master document register with dependency chain and distribution matrix
- ARTIFACT_REGISTER.json: Machine-readable file inventory with SHA-256 hashes
- CSS-OPS-SITREP-20260217: Session report and critical path assessment

### Format
- Each document in dual format: .md (canonical, version-controlled) + .docx (LT distribution)
- All .docx carry CONTROLLED DOCUMENT — DO NOT PRINT headers/footers
- All .md carry CONTROLLED DOCUMENT warning in document body

---

## Amendment Rules

Per CSS-OPS-DOC-003 Section 12:
- Amendments require a new SIP
- LT vote (3/3) for approval
- Version increment on the amended document
- Entry in this CHANGELOG
- No mid-cycle amendments
