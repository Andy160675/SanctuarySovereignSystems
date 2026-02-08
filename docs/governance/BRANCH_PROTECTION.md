# Branch Protection Policy — main

To ensure the integrity of the Sovereign Recursion Engine, the following protections are enforced on the `main` branch.

## Requirements
* **Pull Request Required**: No direct pushes to `main`.
* **Required Approvals**: At least 1 approval from a CODEOWNER (StevenJones).
* **Status Checks Pinned**:
    * `Constitutional Invariants (74/74)`
    * `Performance No-Regression`
    * `Phase-9 Evidence Validation`
* **Signed Commits**: All commits in the PR must be GPG/SSH signed.
* **No Force Push**: Blocked for all users.
* **No Deletion**: Blocked for all users.

## Pinned Check Definitions
* `Constitutional Invariants`: `python -m sovereign_engine.tests.run_all`
* `Performance No-Regression`: `python scripts/validate_performance.py`
