# Secret Remediation Playbook

## Overview
This document provides steps to remediate leaked secrets in the Sovereign System repositories.

## Immediate Response (Triage)
1. **Identify**: Confirm the leaked secret (type, provider, value).
2. **Invalidate**: Revoke/Rotate the secret at the source (e.g., GitHub, AWS, OpenAI).
3. **Verify**: Ensure the old secret no longer works.

## History Purging (Git)
Removing a secret from the current commit is NOT enough. You must purge it from the history.

### Method 1: BFG Repo-Cleaner (Recommended for Speed)
1. Create a `passwords.txt` containing the secret.
2. Run: `bfg --replace-text passwords.txt`
3. Push changes: `git push --force`

### Method 2: git filter-repo (Modern & Safe)
1. Install: `pip install git-filter-repo`
2. Run: `git filter-repo --replace-text <(echo "secret==>REDACTED")`
3. Push changes: `git push --force`

## Clean-up Checklist
- [ ] Rotate the secret at the provider.
- [ ] Purge the secret from all branches and tags.
- [ ] Add the secret's pattern to `.gitignore` or `exclude` files.
- [ ] Notify the Security Officer.
- [ ] Audit logs for unauthorized usage during the leak window.

## Prevention
- Use `Sovereign-PAT-Encrypt.ps1` for local storage.
- Use GitHub Secrets for CI/CD.
- Install `gitleaks` or `git-secrets` as a pre-commit hook.
