# CSS-GOV-CHK-001: GOVERNANCE_MERGE_CHECKLIST_S3
## Season 3 Extension Compliance Gate

This checklist is the mandatory gate for all Pull Requests (PRs) targeting the Season 3 Extension Surface. No PR shall be merged if any item remains unchecked or fails verification.

### 1. Architectural Integrity
- [ ] **No Kernel Mutation:** PR does not modify files in `sovereign_engine/core/`, `sovereign_engine/configs/`, or `sovereign_engine/tests/`.
- [ ] **Invariant Preservation:** PR does not bypass or weaken any of the 7 Non-Negotiable Invariants.
- [ ] **Halt Compliance:** All new code paths include deterministic failure handling (Halt on Ambiguity).

### 2. Security & Sovereignty
- [ ] **Authority Mapping:** All new signals and handlers are correctly mapped to the Trinity authority levels (Operator/Innovator/Steward).
- [ ] **Audit Trail:** Every state transition introduced by the extension is recorded in the append-only audit ledger.
- [ ] **Zero-Trust Compliance:** Code follows the "Default Deny" doctrine.

### 3. Verification & Evidence
- [ ] **Kernel Regression:** Full kernel test suite (`python -m sovereign_engine.tests.run_all`) passes (74/74).
- [ ] **Extension Tests:** PR includes new invariant tests specific to the extension's logic.
- [ ] **Evidence Log:** PR description contains a link to the `integration_closeout` artifact for the proposed change.

### 4. Mandatory Prerequisites
- [ ] **S3-EXT-000a (Constitutional Enforcer) is ACTIVE.**
- [ ] **S3-EXT-000b (Zero-Trust Evidence Chain) is ACTIVE.**

### 5. Steward Review
- [ ] **Formal Approval:** Steward-tier code owner has reviewed and signed off on the cryptographic impact.

---
**Failure to comply with any of the above results in an immediate REJECT and HALT of the merge pipeline.**
