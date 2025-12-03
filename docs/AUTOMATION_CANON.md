# Automation Baseline Canon (v0.1.0)

**Status:** LOCKED
**Date of Enforcement:** December 3, 2025

---

## Baseline Commit

```
Full Hash: 1cb2f04661ab7de247fab18ffd779638f156aaa8
Git Tag:   v0.1.0-automation-baseline
```

This is not "a good commit." It is the **lowest legal floor** for anything public-facing.

---

## Enforced Workflows

All workflows passing on the baseline commit:

| Workflow | File | Status |
|----------|------|--------|
| Security Scan | `security-scan.yml` | ✅ PASSING |
| Container Security | `container-security.yml` | ✅ PASSING |
| E2E Tests | `e2e-tests.yml` | ✅ PASSING |
| Scheduled Ops | `scheduled-ops.yml` | ✅ PASSING |

---

## Branch Protection

The `main` branch is protected with all above workflows as **required status checks**.

Humans cannot silently walk around the nervous system.

---

## Canonical Rule

> **No governance, demo, or investor artifact may reference a commit below this baseline.**

This prevents:
- Screenshots from universes the machine wouldn't accept
- Claims about states that predate constitutional enforcement
- Future-you (or a rushed CEO) waving around outdated evidence

---

## What This Means

As of `v0.1.0-automation-baseline`:

1. Every change to `main` must pass multi-language security scans
2. Every change must pass container security checks
3. Every change must pass governance-grade E2E tests
4. Scheduled operations verify ongoing health

The machine will contradict us if we lie.

---

## Verification

Anyone can verify the baseline:

```bash
# Check the tag exists
git tag -l "v0.1.0-automation-baseline"

# Verify commit hash matches
git rev-parse v0.1.0-automation-baseline

# Check workflow status (requires gh CLI)
gh run list --commit 1cb2f04661ab7de247fab18ffd779638f156aaa8
```

---

## Evidence Location

Screenshots and artifacts proving the baseline:

```
docs/evidence/AUTOMATION_BASELINE_v0.1.0/
├── github_actions_all_green.png
├── branch_protection_settings.png
└── manifest.json
```

---

## Amendment Process

To establish a new baseline:

1. All required workflows must be GREEN on the candidate commit
2. Tag the commit: `v0.X.0-automation-baseline`
3. Update this document with new hash and date
4. Previous baselines remain in git history as audit trail

---

## Constitutional Status

This document is part of the **Sovereign System Constitution**.

It is versioned, hashed, and enforced by CI.

*"The machine refuses to trust anything below this floor."*

---

*Last updated: December 3, 2025*
*Automation Baseline v0.1.0*
