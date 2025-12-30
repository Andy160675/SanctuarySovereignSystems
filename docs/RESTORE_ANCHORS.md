# Sovereign Restore Anchor Policy

This document defines the rules and procedures for managing **Restore Anchors** in the Sovereign system.

## 1. What is an Anchor?
A **Restore Anchor** is a cryptographically verified snapshot of the system state (code, configuration, and evidence) that has been confirmed to be in a healthy, operational condition.

Each anchor is identified by:
- A Git tag (e.g., `restore-healthy-20251230`)
- A closeout pack directory (e.g., `closeout/restore-healthy-20251230/`)
- A tamper-evident manifest (`MANIFEST_SHA256.txt`)

## 2. Immutability Rule
**Anchors are immutable.**
Once a Restore Anchor is finalized and tagged:
- DO NOT modify any files within the `closeout/<tag>/` directory.
- DO NOT move or delete the anchor tag.
- Any change to the system must result in a **new** anchor or release point.

## 3. Automation (The Law)
The full closeout lifecycle MUST be executed via the automated pipeline. This ensures that Generate -> Prove -> Verify -> Custody steps are performed in the correct order.

```powershell
powershell -File tools\closeout_pipeline.ps1 -TagName "release-v1.0" -SmokeCommand "python verify_integration.py"
```

## 4. Capability + Revision Management (CRM)
The system uses CRM v1 to prevent silent drift in security-critical code.

### 4.1 Revision Gate
Any changes to security-critical files (e.g., `governance.py`, red-team tests) require a policy revision bump. The `closeout_pipeline.ps1` enforces this check at Stage 0.

### 4.2 Bumping Policy
If you intentionally modify security-critical files, you must bump the revision before closing out:

```powershell
powershell -File tools\bump_policy_rev.ps1 -Message "Describe your security changes here"
```

## 5. Verification
Before starting new work or performing a deployment, verify the integrity of the anchor:

```powershell
powershell -File tools\verify_closeout_pack.ps1 -TagName "restore-healthy-20251230"
```

A successful verification proves that the evidence pack has not been tampered with since its creation.

## 6. Custody Tracking
Every time an anchor is verified or handed over, a custody stamp should be generated:

```powershell
powershell -File tools\stamp_custody.ps1 -TagName "restore-healthy-20251230"
```

This logs the event in `custody/custody.jsonl` without modifying the frozen anchor pack.

## 7. Starting New Work
All new development phases, deployment hardening, or feature work MUST:
1. Start from a verified Restore Anchor tag.
2. Create a new branch (e.g., `feature/hardening-based-on-20251230`).
3. Close out under a NEW tag and manifest when the phase is complete.

---
*Stay Sovereign.*
