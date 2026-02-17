# CSS-DOC-REGISTER-001 — Master Document Register

**CONTROLLED DOCUMENT — DO NOT PRINT**

Last Updated: 17 February 2026
Maintained By: Andy Jones, Steward

---

## Controlled Document Inventory

| Ref | Title | Version | Status | Date | Location | Classification |
|---|---|---|---|---|---|---|
| CSS-OPS-DOC-003 | Post-SIP Autonomous Execution Engine | 1.0 DRAFT | FOR LT REVIEW | 16 Feb 2026 | `operations/css-ops/` | INTERNAL — LT |
| CSS-OPS-DOC-004 | PIOPL Agent Deployment Engine | 1.0 DRAFT | FOR LT REVIEW | 16 Feb 2026 | `operations/css-ops/` | INTERNAL — LT |
| CSS-OPS-DOC-005 | PIOPL Enterprise Operating Plan | 1.0 DRAFT | FOR LT REVIEW | 17 Feb 2026 | `operations/css-ops/` | INTERNAL — LT |
| CSS-OPS-DOC-006 | Meeting Structures, Escalation Paths & Andon | 1.0 DRAFT | FOR LT REVIEW | 17 Feb 2026 | `operations/css-ops/` | INTERNAL — ALL |

## Document Dependency Chain

```
CSS-OPS-DOC-003 (SIP Engine)
    ├── CSS-OPS-DOC-004 (Agent Deployment) — extends DOC-003
    │       └── CSS-OPS-DOC-005 (Enterprise Plan) — extends DOC-003 + DOC-004
    │               └── CSS-OPS-DOC-006 (Meetings/Escalation/Andon) — operationalises DOC-003 + DOC-005
    └── CSS-STRAT-DOC-001 (Creator777 Strategy) — referenced by DOC-004, DOC-005
```

## Format Standards

- **Canonical format:** Markdown (.md) in repository for version control
- **Distribution format:** Word (.docx) for LT review, sign-off, and formal distribution
- **Header/Footer:** All controlled documents carry "CONTROLLED DOCUMENT — DO NOT PRINT" in red, bold
- **Naming:** CSS-[DOMAIN]-[TYPE]-[SEQ] (e.g., CSS-OPS-DOC-003)
- **Amendments:** Require new SIP, LT vote, version increment. No mid-cycle amendments.

## Distribution Matrix

| Person | Role | DOC-003 | DOC-004 | DOC-005 | DOC-006 |
|---|---|---|---|---|---|
| Andy Jones | Steward | FULL | FULL | FULL | FULL |
| Steven Jones | CEO / LT | FULL | FULL | FULL | FULL |
| Chris Bevan | COO / LT | GOV/OPS | GOV/OPS | GOV/OPS | FULL |
| Tom Maher | Programme Director | ROLLOUT | ROLLOUT | ROLLOUT | FULL |

| CSS-OPS-TRACK-001 | Immediate Actions Tracker | 1.0 | LIVE | 17 Feb 2026 | `operations/css-ops/` | INTERNAL — ALL |

## Approval Status

| Document | Andy | Steven | Chris | Frozen? |
|---|---|---|---|---|
| CSS-OPS-DOC-003 | PENDING | PENDING | PENDING | NO |
| CSS-OPS-DOC-004 | PENDING | PENDING | PENDING | NO |
| CSS-OPS-DOC-005 | PENDING | PENDING | PENDING | NO |
| CSS-OPS-DOC-006 | PENDING | PENDING | PENDING | NO |

All documents require 3/3 LT vote to become constitutional. Until voted, they are DRAFT — FOR LT REVIEW.

---

*This register is the single source of truth for all CSS controlled documents.*
