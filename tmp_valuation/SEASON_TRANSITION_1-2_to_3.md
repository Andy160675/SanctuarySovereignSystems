# SEASON TRANSITION: 1-2 → 3

## Constitutional Handoff of Authority

**Document ID:** CSS-GOV-DOC-003
**Effective Date:** 2026-02-08
**Status:** ACTIVE — IRREVERSIBLE
**Author:** Andy Jones, Founder — Codex Sovereign Systems
**Witness:** Sovereign Recursion Engine v1.0.0-kernel74 (74/74 invariant passes, 600 PDCA signals, zero halts)

---

## 1. EPOCH DECLARATION

### 1.1 Closing: Season 2 — Kernel Locked

```
EPOCH:    Season 2
CODENAME: Kernel Locked
TAG:      v1.0.0-kernel74
STATUS:   SEALED
```

Season 1 established doctrine. Season 2 compiled that doctrine into executable code. Both epochs are now closed.

**Season 1-2 objective — COMPLETE:**
A stable, invariant-locked core capable of hosting governed extensions.

**Evidence of completion:**
- 74/74 invariant tests passing without regression
- 600 PDCA signals processed across 100 cycles with zero halts
- 601 ledger entries with unbroken SHA-256 hash chain
- 7 constitutional invariants encoded and enforced
- 6 forbidden states defined and gated
- Phase 0–9 pipeline operational end-to-end
- Extension compliance gate (Phase 9) proven functional

No further commits to Season 1-2 scoped paths are permitted. The kernel is frozen. This is not a pause. It is a permanent seal.

### 1.2 Opening: Season 3 — Governance Active / Kernel Frozen

```
EPOCH:    Season 3
CODENAME: Governance Surface
STATUS:   ACTIVE
SCOPE:    Extension, integration, and operation upon the frozen kernel
```

**Season 3 objective — OPENED:**
A constitutional surface for adding, verifying, and operating bolt-ons without kernel modification.

Season 3 inherits the kernel. It does not own it. It does not modify it. It builds upon it through governed extension points defined by Phase 9 and constrained by the 7 invariants.

---

## 2. IMMUTABLE ARTIFACTS (THE SEAL)

The following artifacts constitute the sealed output of Season 1-2. Together they form the genesis block of the Sovereign System. Their integrity is the foundation of all Season 3 work.

### 2.1 Canonical Artifacts

| Artifact | Type | Purpose |
|----------|------|---------|
| `v1.0.0-kernel74` | Git tag | The final kernel release. 74/74 tests. Immutable reference point. |
| `sovereign_engine/core/` | Directory | Phases 0–9. The locked kernel. No Season 3 commit may modify any file in this path. |
| `sovereign_engine/configs/constitution.json` | File | Machine-readable constitutional ground truth. Append-only from this point. |
| `sovereign_engine/tests/run_all.py` | File | The invariant test suite. 74 tests. The regression gate for all future work. |
| `docs/INTEGRATION_CLOSEOUT_S2_to_S3.md` | File | Build/test close-out record for the Season 2 → 3 transition. |
| `docs/INTEGRATION_REPORT_v1.0.0-kernel74.md` | File | Validation proof: full test results, coverage, and invariant verification. |
| `CODEOWNERS` | File | Access control freezing `sovereign_engine/core/` to designated stewards only. |
| `SEASONS.md` | File | Normative boundary definitions for Season 1, 2, and 3. |
| `CLAUDE.md` | File | Constitutional anchor for any AI agent operating on this codebase. |

### 2.2 Integrity Mandate

These artifacts are **append-only**. Their content hashes at the time of the `v1.0.0-kernel74` tag define the system's genesis block.

Any modification to a sealed artifact that is not an append operation constitutes a **constitutional violation** and triggers the halt doctrine: prefer stopping to lying.

The SHA-256 hashes of these files at tag `v1.0.0-kernel74` are the root of trust for all Season 3 evidence chains.

---

## 3. HANDOFF PROTOCOL

### 3.1 Proposing a Season 3 Extension

Any new capability entering the system must be proposed as a Season 3 extension with identifier format `S3-EXT-XXX`.

**Requirement 1: ROADMAP Amendment**

A pull request amending `ROADMAP.md` to register the proposed extension. This PR is governed by the `CODEOWNERS` rule requiring steward-tier approval. The amendment must include:

- Extension identifier (`S3-EXT-XXX`)
- Extension name
- One-sentence purpose
- Proposed pricing model (if customer-facing)
- Named owner

**Requirement 2: Extension Specification**

A file `EXT_SPEC.md` placed in the extension's directory (`sovereign_engine/extensions/S3-EXT-XXX/EXT_SPEC.md`) containing:

- Justification under Subtractive Invariance: the extension must demonstrate that it operates within `VIABLE = TOTAL - FORBIDDEN` and does not expand the FORBIDDEN set or contract the invariant set
- Dependency declaration: which kernel phases it interfaces with
- Authority tier required for activation (operator / innovator / steward)
- Evidence requirements: what audit trail entries it generates
- Rollback procedure: how it is safely deactivated without kernel impact

### 3.2 Merging a Season 3 Extension

An extension PR may only be merged when ALL of the following are satisfied:

**Gate 1: Governance Merge Checklist**

The extension must pass every item in `GOVERNANCE_MERGE_CHECKLIST_S3.md`:

- [ ] `EXT_SPEC.md` present and complete
- [ ] `ROADMAP.md` amendment approved by steward
- [ ] Phase 9 compliance gate passes (extension does not modify Season 2 invariants)
- [ ] Kernel invariant suite (`python -m sovereign_engine.tests.run_all`) returns 74/74
- [ ] No files in `CODEOWNERS` protected paths are modified
- [ ] Extension has its own test suite with 100% of declared functionality covered
- [ ] Authority tier requirements documented and enforced
- [ ] Rollback procedure tested

**Gate 2: Evidence Archival**

The extension must generate and archive the following to the Evidence Vault:

- Compliance gate output (Phase 9 result with timestamp and hash)
- Full test suite results
- `EXT_SPEC.md` hash at time of merge
- Steward approval record

**Gate 3: Path Protection**

The PR must not modify any file in a `CODEOWNERS` protected path. This is enforced by GitHub branch protection rules. Any PR that touches a protected path without steward dual-key approval is automatically rejected.

---

## 4. INVARIANT PRESERVATION

### 4.1 The Regression Rule

**No commit in Season 3 may cause the kernel invariant suite (`python -m sovereign_engine.tests.run_all`) to regress from 74/74 passes.**

This is not a guideline. It is a constitutional constraint with the same authority as the halt doctrine.

A regression is defined as:
- Any test changing from PASS to FAIL
- Any test being removed, skipped, or commented out
- Any test having its assertion weakened
- The total test count dropping below 74

**A regression is a constitutional crisis.** It triggers:

1. Immediate rollback of the offending commit
2. System-wide audit of all changes since last known-good state
3. Incident report filed to the Evidence Vault
4. Steward-tier review before any further merges are permitted

### 4.2 Bootstrap Extensions (S3-EXT-000)

The following two capabilities are designated as `S3-EXT-000` — the zeroth extensions. They are prerequisites for the security and integrity of all subsequent Season 3 work:

**S3-EXT-000a: Constitutional Enforcer**

An automated CI/CD gate that runs on every pull request and:
- Executes the full 74-test invariant suite
- Verifies no `CODEOWNERS` protected files are modified
- Validates `EXT_SPEC.md` presence and completeness for any new extension
- Blocks merge on any failure

**S3-EXT-000b: Zero-Trust Evidence Chain**

An automated evidence generation system that on every merge:
- Captures SHA-256 hashes of all modified files
- Generates RFC-3161 compliant timestamps
- Archives compliance gate outputs
- Maintains an append-only evidence ledger
- Provides chain-of-custody verification for any artifact

These two extensions must be the first Season 3 code merged. No other extension may be proposed, reviewed, or merged until S3-EXT-000a and S3-EXT-000b are operational.

---

## 5. AUTHORITY TRANSFER

### 5.1 Transfer of Custodianship

Custodianship of the codebase now transfers from the **Build/Test Authority** (which achieved a locked kernel) to the **Governance Authority** (which manages the extension surface).

| Authority | Season | Mandate | Status |
|-----------|--------|---------|--------|
| Build/Test Authority | Season 1-2 | Compile doctrine into a proven, invariant-locked kernel | **MANDATE COMPLETE** |
| Governance Authority | Season 3 | Manage the extension surface, enforce compliance gates, preserve kernel integrity | **MANDATE ACTIVE** |

The Build/Test Authority retains veto power over any action that would violate kernel integrity. This veto is exercised automatically by the Constitutional Enforcer (S3-EXT-000a) and may be exercised manually by any designated steward.

### 5.2 Steward Responsibilities Under Season 3

Stewards are the custodians of the frozen kernel. Their duties:

- Approve or reject `ROADMAP.md` amendments for new extensions
- Review `EXT_SPEC.md` submissions for constitutional compliance
- Verify Evidence Vault integrity on a regular cadence
- Invoke the halt doctrine if kernel integrity is threatened
- Maintain the `CODEOWNERS` file

### 5.3 Operational Continuity

The authority transfer does not change:
- The 7 invariants (they are immutable, full stop)
- The 6 forbidden states (they remain enforced)
- The failure policy (router_failure→HALT, audit_failure→HALT, legality_failure→ESCALATE, unknown→HALT)
- The halt doctrine (prefer stopping to lying)
- The authority ladder (operator → innovator → steward)

These persist across all seasons. They are not Season 2 rules that Season 3 inherits. They are constitutional law that transcends seasons.

---

## 6. ACTIVATION

This document takes effect upon commit to the repository root.

Upon activation:
- Season 2 is sealed
- Season 3 is open
- The Governance Authority holds custodianship
- The extension surface is available for governed proposals
- No kernel modification is permitted
- The 74-test invariant suite is the regression gate for all future work

The kernel is proven. The doctrine is compiled. The gate is built. What comes next must pass through it.

---

```
// Season 1-2: SEALED. Season 3: ACTIVE. Governance is now protocol.
```
