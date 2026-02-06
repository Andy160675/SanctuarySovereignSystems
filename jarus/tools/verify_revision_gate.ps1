<#
.SYNOPSIS
  Detects silent drift in security-critical files by comparing hashes against policy/revision.json.

.DESCRIPTION
  - Computes current hashes of security-critical files.
  - Compares against "security_critical_hashes" in policy/revision.json.
  - Fails if a file changed but policy_rev was not bumped.

.USAGE
  powershell -File tools\verify_revision_gate.ps1
#>

[CmdletBinding()]
param(
  [string]$RepoRoot = (Get-Location).Path
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$RevisionPath = Join-Path $RepoRoot "policy\revision.json"
if (-not (Test-Path $RevisionPath)) {
  Write-Host "FAIL: policy/revision.json not found." -ForegroundColor Red
  exit 1
}

$Revision = Get-Content $RevisionPath | ConvertFrom-Json
$StoredHashes = $Revision.security_critical_hashes

# Define security-critical files
$CriticalFiles = @(
  "governance.py",
  "tests\red_team\test_tool_abuse.py",
  "tests\red_team\test_prompt_injection.py",
  "tests\test_st_michael.py",
  "src\core\config.py"
)

$drift = New-Object System.Collections.Generic.List[string]
$newHashes = @{}

foreach ($file in $CriticalFiles) {
  $fullPath = Join-Path $RepoRoot $file
  if (-not (Test-Path $fullPath)) {
    Write-Host "WARN: Critical file missing: $file" -ForegroundColor Yellow
    continue
  }

  $hash = (Get-FileHash -Algorithm SHA256 -Path $fullPath).Hash.ToLowerInvariant()
  $newHashes[$file] = $hash

  # Check if we have a stored hash for this file
  if ($StoredHashes.PSObject.Properties.Name -contains $file) {
    $expected = $StoredHashes.$file
    if ($hash -ne $expected) {
      $drift.Add("DRIFT: $file has changed!`n  Expected: $expected`n  Actual:   $hash")
    }
  } else {
    # If not in stored hashes, it's new/untracked in the gate
    Write-Host "NOTE: $file is new to the revision gate." -ForegroundColor Cyan
  }
}

if ($drift.Count -gt 0) {
  Write-Host ""
  Write-Host "REVISION GATE FAILED:" -ForegroundColor Red
  foreach ($d in $drift) { Write-Host $d }
  Write-Host ""
  Write-Host "ACTION REQUIRED: If these changes are intentional, run tools\bump_policy_rev.ps1" -ForegroundColor Yellow
  exit 1
}

Write-Host "PASS: Revision gate verified. No silent drift detected." -ForegroundColor Green
exit 0
