# SEASONS.md
## Canonical Season Boundaries for SanctuarySovereignSystems

This file defines the authoritative Season split for this repository.
If any code/docs conflict with this file, this file governs until amended.

## 1) Season Definitions (Normative)

| Season | Name | Scope | Mutability | Status |
|---|---|---|---|---|
| **Season 1** | Constitutional Design Canon | Philosophy, principles, threat framing, invariance doctrine, formal claims, pre-code architecture intent ("what/why") | Amendable via governance process | **Backfilled by this doc** |
| **Season 2** | Executable Kernel | `constitution.json`, Phases 0–9, constitutional enforcement, halt doctrine, authority ladder, audit/ledger invariants ("how") | **Immutable by default** | Built/tested |
| **Season 3** | Extension Surface | Plug-ins, integrations, orchestration, product modules, external connectors ("what else") | Flexible, but constrained by Season 2 gates | Interface defined |

## 2) Hard Boundary Rules

1. **Season 3 must not modify Season 2 invariants.**
2. **Season 2 must implement Season 1 intent, not reinterpret it ad hoc.**
3. **No direct edits to kernel invariants from extension code paths.**
4. **Any proposed Season 2 invariant change requires formal amendment + approval gate.**
5. **Halt doctrine applies across all Seasons when ambiguity or invariant risk is detected.**

## 3) Repository Mapping (Expected)

- **Season 1 (Design Canon)**
  - `docs/` (constitutional rationale, threat model, reference architecture)
- **Season 2 (Kernel)**
  - `core/`, `configs/constitution.json`, kernel tests, compliance gates
- **Season 3 (Extensions)**
  - `extensions/` or equivalent module folders, integration adapters, product add-ons

> If current folders differ, this mapping is target-state normative, not a blocker.

## 4) Gate Model

### Season 1 → Season 2 Gate
Required artifacts:
- constitutional mapping
- falsifiable claims / failure criteria
- threat model linkage to enforcement

### Season 2 → Season 3 Gate
Required checks:
- extension cannot alter halt doctrine
- extension cannot alter authority ladder
- extension cannot alter audit/ledger invariants
- explicit compliance evidence recorded

## 5) Versioning Policy

- **Season 1**: `S1-doc-vX.Y`
- **Season 2**: `S2-kernel-vX.Y` (major only for constitutional/invariant change)
- **Season 3**: `S3-ext-<module>-vX.Y`

## 6) Manus "9 Articles" Alignment

Where Manus references "9 Articles," treat them as the constitutional structure that maps primarily to:
- Season 1 (intent and doctrine), and
- Season 2 (enforced kernel realization).

This avoids terminology drift between repositories.

## 7) Amendment Procedure

To change this file:
1. Open governance proposal with rationale + impact analysis.
2. Identify affected Season boundaries and tests.
3. Provide migration and rollback plan.
4. Obtain approval per repository governance policy.
5. Record evidence in ledger/audit artifacts.

---

**Current authoritative interpretation:**
- **Season 1** = constitutional design canon (pre-code intent)
- **Season 2** = executable kernel (Phases 0–9 + invariants + constitution)
- **Season 3** = constrained extension ecosystem (must pass compliance gate)
