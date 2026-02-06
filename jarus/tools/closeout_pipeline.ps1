<#
.SYNOPSIS
  Orchestrates the full end-to-end closeout lifecycle (The Law).

.DESCRIPTION
  This script unifies the Generate -> Prove -> Verify -> Custody lifecycle into a single command.
  It ensures every release is audit-grade, deterministic, and anchored.

.USAGE
  powershell -File tools\closeout_pipeline.ps1 -TagName "release-v1.0" -SmokeCommand "python verify_integration.py"

.PARAMETERS
  -TagName: The name of the tag/folder for this closeout.
  -SmokeCommand: The command to run for smoke verification.
  -GitPush: (Optional) If set, will commit closeout artifacts and push the tag.
#>

[CmdletBinding()]
param(
  [Parameter(Mandatory=$true)][string]$TagName,
  [Parameter(Mandatory=$true)][string]$SmokeCommand,
  [switch]$GitPush
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$RepoRoot = (Get-Location).Path

function Log([string]$Msg) {
  Write-Host ""
  Write-Host ">>> $Msg" -ForegroundColor Cyan
}

try {
  # 0. CRM GATE
  Log "STAGE 0: Verifying Revision Gate (No Silent Drift)"
  powershell -File tools\verify_revision_gate.ps1 -RepoRoot $RepoRoot

  # 1. GENERATE
  Log "STAGE 1: Generating Closeout Pack"
  powershell -File tools\make_closeout_pack.ps1 -TagName $TagName -RepoRoot $RepoRoot

  # 2. PROVE (Smoke)
  Log "STAGE 2: Capturing Smoke Evidence"
  powershell -File tools\make_smoke_evidence.ps1 -TagName $TagName -SmokeCommand $SmokeCommand -RepoRoot $RepoRoot

  # 3. VERIFY
  Log "STAGE 3: Verifying Pack Integrity"
  powershell -File tools\verify_closeout_pack.ps1 -TagName $TagName -RepoRoot $RepoRoot

  # 4. CUSTODY
  Log "STAGE 4: Recording Chain of Custody"
  powershell -File tools\stamp_custody.ps1 -TagName $TagName -RepoRoot $RepoRoot

  # 5. ANCHOR (Git)
  if ($GitPush) {
    Log "STAGE 5: Anchoring Remotely"
    
    # Check if anything to commit
    $status = git status --short
    if ($status) {
      git add .
      git commit -m "closeout: $TagName (automated pipeline run)"
      git push
    }
    
    # Tagging
    git tag $TagName
    git push origin $TagName
  }

  Log "LIFECYCLE COMPLETE: $TagName"
  Write-Host "System is anchored and verified." -ForegroundColor Green
} catch {
  Write-Host "LIFECYCLE FAILED: $_" -ForegroundColor Red
  exit 1
}
