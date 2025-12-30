# Sovereign Baseline Expected State (as-of 2025-12-30)

This document defines the "Gold Standard" baseline for a healthy Sovereign system restoration.

## 1. Anchor State
- **Primary Anchor**: `crm-v1-anchor` (Git tag)
- **Restoration Anchor**: `restore-healthy-20251230` (Git tag)
- **Policy**: All new work MUST branch from `crm-v1-anchor`.

## 2. Closeout Pack Structure
A valid closeout pack (e.g., `closeout/crm-v1-anchor/`) must contain:
- `closeout_note.md`: Summary of the release.
- `MANIFEST_SHA256.txt`: Tamper-evident hash list of all files in the pack.
- `evidence/`: Subdirectory containing raw verification outputs.
  - `TESTS/pytest_160_pass.txt`
  - `BOOT/sovereign_up_output.txt`
  - `INTEGRATION/verify_integration_output.txt`
  - `DEPLOY/smoke_output.txt`
  - `FINGERPRINT/revision_snapshot.json`
  - `FINGERPRINT/capabilities_snapshot.yaml`

## 3. Deterministic Tooling
The following scripts must exist in `tools/`:
- `make_closeout_pack.ps1`: Generates the pack.
- `make_smoke_evidence.ps1`: Adds smoke test results.
- `verify_closeout_pack.ps1`: Verifies pack integrity.
- `stamp_custody.ps1`: Records chain of custody.
- `bump_policy_rev.ps1`: Updates policy revision and file hashes.
- `verify_revision_gate.ps1`: Prevents silent security drift.
- `closeout_pipeline.ps1`: Orchestrates the full lifecycle.

## 4. Governance & Policy
- `policy/capabilities.yaml`: Canonical list of enabled features.
- `policy/revision.json`: Pinned system version and security hashes.
- `docs/RESTORE_ANCHORS.md`: Formal anchor management policy.
- `custody/custody.jsonl`: Chain of custody log (located outside closeout packs).

## 5. Functional Baseline
- **Tests**: 160/160 PASS.
- **Boot**: `sovereign_up.py` returns success.
- **Integration**: `verify_integration.py` confirms ledger integrity.
- **Security**: Red Team ASR = 0%, Block Rate = 100%.
