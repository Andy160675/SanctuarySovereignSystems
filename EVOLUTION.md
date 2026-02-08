# EVOLUTION PROTOCOL: Season 3+
**Baseline Protection & Safe Growth**

This protocol defines the mandatory requirements for evolving the `sovereign_engine` kernel and its surrounding governance substrate. It ensures that the resilience properties established in `v1.1.0-stable` are preserved during future expansion.

## 1. The Immutable Core
The 7 Kernel Invariants defined in `README.md` are immutable. No evolution step may weaken, bypass, or override them. Any change that modifies the logic of Phases 0-8 must be treated as a **High-Risk Evolution**.

## 2. Evolution Workflow
Every change to the system must follow the **S.V.E.A.** (Sensing, Verification, Evidence, Alignment) cycle:

### S - Sensing (CI Validation)
*   **Regression Check**: All changes must pass the full 74-test suite (`python -m sovereign_engine.tests.run_all`).
*   **Sanity Assertion**: New features must include a corresponding sanity assertion in the CI workflow (e.g., artifact existence checks).

### V - Verification (Constitutional Alignment)
*   **Invariant Check**: Every new feature or refactor must be mapped against the 7 Invariants. If a change touches a "Forbidden State" or "Halt Doctrine", it requires a Steward-level dual-key override simulation.

### E - Evidence (Cryptographic Chain)
*   **Append-Only Ledger**: Every merge to `main` must generate a new evidence entry via `scripts/generate_build_evidence.py`.
*   **Hash Continuity**: The evidence chain tip must be verified as valid before and after the change.

### A - Alignment (Narrative & TPM)
*   **TPM Report**: Any unexpected behavior during development must be documented using the `DAILY_REPAIR_REPORT_TEMPLATE.md`.
*   **Deterministic Documentation**: Documentation must be updated to reflect *actual* behavior. Use "does/is" instead of "should/will".

## 3. Deployment Gating
*   **v1.1.0-stable as Anchor**: No PR may be merged if it fails the `v1.1.0-stable` regression baseline.
*   **Audit Sealing**: For major releases (e.g., v1.2.0), the audit ledger must be sealed, and a new `vX.X.X-stable` tag must be issued in the evidence chain.

## 4. Extension Boundary
*   Extensions (Phase 9) must not modify the kernel.
*   Extensions must provide a `manifest.json` and pass the `GOVERNANCE_MERGE_CHECKLIST_S3.md`.

---
*Authorized by Sovereign Engine Governance Substrate.*
