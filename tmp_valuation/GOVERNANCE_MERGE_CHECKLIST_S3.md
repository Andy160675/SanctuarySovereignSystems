# GOVERNANCE MERGE CHECKLIST: Season 3 Extensions

## Document ID: CSS-GOV-CHK-001
## Referenced by: SEASON_TRANSITION_1-2_to_3.md (Section 3.2, Gate 1)

---

Every Season 3 extension PR must satisfy ALL items below before merge is permitted. A single unchecked item blocks the merge. No exceptions. No overrides below steward tier.

---

## Extension Identity

- **Extension ID:** S3-EXT-___
- **Extension Name:** ___
- **PR Number:** #___
- **Proposer:** ___
- **Reviewer (Steward):** ___
- **Date:** ___

---

## Checklist

### Specification

- [ ] `EXT_SPEC.md` is present in `sovereign_engine/extensions/S3-EXT-XXX/`
- [ ] `EXT_SPEC.md` includes Subtractive Invariance justification (`VIABLE = TOTAL - FORBIDDEN`)
- [ ] `EXT_SPEC.md` includes dependency declaration (kernel phases interfaced)
- [ ] `EXT_SPEC.md` includes authority tier requirement
- [ ] `EXT_SPEC.md` includes evidence generation requirements
- [ ] `EXT_SPEC.md` includes rollback procedure

### Registration

- [ ] `ROADMAP.md` amendment PR approved by steward
- [ ] Extension registered with ID, name, purpose, pricing model, and owner

### Kernel Integrity

- [ ] `python -m sovereign_engine.tests.run_all` returns **74/74 PASS**
- [ ] No files in `CODEOWNERS` protected paths are modified by this PR
- [ ] Phase 9 compliance gate passes (extension does not modify Season 2 invariants)
- [ ] No forbidden state is introduced or enabled: `unaudited_action`, `silent_escalation`, `cross_authority_call`, `tampered_signal`, `post_halt_execution`, `steward_override_without_dual_key`

### Extension Quality

- [ ] Extension has its own test suite
- [ ] 100% of declared functionality is covered by tests
- [ ] Extension tests pass independently of other extensions
- [ ] Extension can be activated and deactivated without kernel side effects
- [ ] Rollback procedure has been tested

### Evidence

- [ ] Phase 9 compliance gate output archived to Evidence Vault (with timestamp + hash)
- [ ] Full test suite results archived to Evidence Vault
- [ ] `EXT_SPEC.md` hash at time of merge recorded
- [ ] Steward approval record archived

### Authority

- [ ] Steward has reviewed and approved this checklist
- [ ] Dual-key approval obtained (if extension touches steward-tier authority)

---

## Steward Sign-Off

**Steward Name:** ___
**Date:** ___
**Decision:** APPROVED / REJECTED
**Reason (if rejected):** ___

---

```
Gate status: OPEN / CLOSED
If any item unchecked: Gate = CLOSED. Merge blocked.
```
