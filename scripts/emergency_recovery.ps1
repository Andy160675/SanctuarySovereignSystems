param(
  [string]$BaseRef = "v1.0.0-kernel74",
  [string]$SecurityPath = "sovereign_engine/extensions/security",
  [switch]$MergeToMain,
  [switch]$Push
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Write-Host "=== Emergency Recovery (No Shortcuts) ==="

# Guard: clean tree
$dirty = git status --porcelain
if ($dirty) { throw "Working tree is not clean. Commit/stash first." }

git fetch origin --tags

$branch = "emergency-recovery-" + (Get-Date -Format "yyyyMMdd-HHmmss")
git checkout -b $branch $BaseRef

Write-Host "Running kernel invariant suite..."
$env:PYTHONPATH = "."
python -m sovereign_engine.tests.run_all
if ($LASTEXITCODE -ne 0) { throw "Kernel tests failed." }

Write-Host "Running security validation + fingerprint checkpoint..."
$env:PYTHONPATH = "."
python scripts/security_validate.py --repo-root . --write-fingerprint
if ($LASTEXITCODE -ne 0) { throw "Security validation failed." }

git add $SecurityPath
git add scripts/security_validate.py
git add scripts/emergency_recovery.ps1
git add audit/seals/kernel_fingerprint.sha256

$staged = git diff --cached --name-only
if (-not $staged) {
  Write-Host "No staged changes."
} else {
  git commit -m "security(governance): add zero-trust evidence chain and constitutional enforcer"
}

if ($MergeToMain) {
  $featureBranch = git branch --show-current

  git checkout main
  git pull --ff-only origin main
  git merge --no-ff $featureBranch -m "security(governance): emergency recovery merge"

  $env:PYTHONPATH = "."
  python -m sovereign_engine.tests.run_all
  if ($LASTEXITCODE -ne 0) { throw "Post-merge kernel tests failed." }

  $env:PYTHONPATH = "."
  python scripts/security_validate.py --repo-root .
  if ($LASTEXITCODE -ne 0) { throw "Post-merge security validation failed." }

  if ($Push) {
    git push origin main
  } else {
    Write-Host "Merge complete locally. Push skipped."
  }
} else {
  Write-Host "Recovery branch ready: $branch"
}
