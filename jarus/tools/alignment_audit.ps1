<#
.SYNOPSIS
  Performs an alignment audit of the The Blade of Truth against the expected baseline.

.DESCRIPTION
  - Confirms anchor tags exist.
  - Confirms closeout packs exist and are verified.
  - Confirms custody log is present.
  - Confirms deterministic tooling is present.
  - Confirms governance policy documents are present.

.USAGE
  powershell -File tools\alignment_audit.ps1
#>

[CmdletBinding()]
param(
  [string]$RepoRoot = (Get-Location).Path
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Continue"

$Passed = 0
$Failed = 0

function Report-Result([string]$Task, [bool]$Success, [string]$Detail = "") {
  if ($Success) {
    Write-Host "âœ… PASS: $Task" -ForegroundColor Green
    if ($Detail) { Write-Host "   $Detail" }
    $global:Passed++
  } else {
    Write-Host "âŒ FAIL: $Task" -ForegroundColor Red
    if ($Detail) { Write-Host "   $Detail" }
    $global:Failed++
  }
}

Write-Host "--- SOVEREIGN ALIGNMENT AUDIT ---" -Cyan

# 1. Anchor Tags
$tags = @("restore-healthy-20251230", "crm-v1-anchor")
foreach ($tag in $tags) {
  $tagCheck = git tag --list $tag
  Report-Result "Git tag '$tag' exists" ($tagCheck -eq $tag)
}

# 2. Closeout Packs
foreach ($tag in $tags) {
  $packPath = Join-Path $RepoRoot "closeout\$tag"
  $packExists = Test-Path $packPath
  Report-Result "Closeout pack '$tag' exists" $packExists

  if ($packExists) {
    $verifyCmd = "powershell -File tools\verify_closeout_pack.ps1 -TagName $tag"
    $verifyResult = Invoke-Expression $verifyCmd | Out-String
    $isVerified = $LASTEXITCODE -eq 0
    Report-Result "Closeout pack '$tag' integrity verified" $isVerified ($verifyResult.Trim())
  }
}

# 3. Custody Log
$custodyLog = Join-Path $RepoRoot "custody\custody.jsonl"
$custodyExists = Test-Path $custodyLog
Report-Result "Custody log exists" $custodyExists

if ($custodyExists) {
  $lastLine = Get-Content $custodyLog | Select-Object -Last 1
  Report-Result "Custody log contains recent entry" ($lastLine -match "crm-v1-anchor") ("Last entry: " + $lastLine)
}

# 4. Deterministic Tooling
$tools = @(
  "make_closeout_pack.ps1",
  "make_smoke_evidence.ps1",
  "verify_closeout_pack.ps1",
  "stamp_custody.ps1",
  "bump_policy_rev.ps1",
  "verify_revision_gate.ps1",
  "closeout_pipeline.ps1"
)
foreach ($tool in $tools) {
  $toolPath = Join-Path $RepoRoot "tools\$tool"
  Report-Result "Tool '$tool' exists" (Test-Path $toolPath)
}

# 5. Governance Documents
$docs = @(
  "docs\RESTORE_ANCHORS.md",
  "docs\BASELINE_EXPECTED_STATE.md",
  "policy\capabilities.yaml",
  "policy\revision.json"
)
foreach ($doc in $docs) {
  $docPath = Join-Path $RepoRoot $doc
  Report-Result "Document '$doc' exists" (Test-Path $docPath)
}

Write-Host "`n--- AUDIT SUMMARY ---" -Cyan
Write-Host "PASSED: $Passed" -ForegroundColor Green
$SummaryColor = if ($Failed -gt 0) { "Red" } else { "Gray" }
Write-Host "FAILED: $Failed" -ForegroundColor $SummaryColor

if ($Failed -eq 0) {
  Write-Host "`nMISSION STATUS: ALIGNED" -ForegroundColor Green
  exit 0
} else {
  Write-Host "`nMISSION STATUS: DRIFT DETECTED" -ForegroundColor Red
  exit 1
}

