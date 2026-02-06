<#
.SYNOPSIS
  Captures deployment/smoke evidence into an existing closeout pack and refreshes SHA256 manifest.

.USAGE
  pwsh -File tools/make_smoke_evidence.ps1 -TagName "restore-healthy-20251230" -SmokeCommand "python verify_integration.py"
  pwsh -File tools/make_smoke_evidence.ps1 -TagName "restore-healthy-20251230" -SmokeCommand "python path\to\your_smoke.py --quick"
#>

[CmdletBinding()]
param(
  [string]$RepoRoot = (Get-Location).Path,
  [Parameter(Mandatory=$true)][string]$TagName,
  [Parameter(Mandatory=$true)][string]$SmokeCommand
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function New-Dir([string]$Path) {
  if (-not (Test-Path $Path)) { New-Item -ItemType Directory -Path $Path | Out-Null }
}
function Write-Text([string]$Path, [string]$Content) {
  $dir = Split-Path -Parent $Path
  if ($dir) { New-Dir $dir }
  $Content | Out-File -FilePath $Path -Encoding UTF8
}
function Run-Capture([string]$Command, [string]$OutFile) {
  $dir = Split-Path -Parent $OutFile
  if ($dir) { New-Dir $dir }

  $stdout = ""
  $exit = 0
  try { $stdout = (Invoke-Expression $Command 2>&1 | Out-String) }
  catch { $stdout = ($_ | Out-String); $exit = 1 }

  $header = @"
==== COMMAND ====
$Command

==== TIMESTAMP (UTC) ====
$(Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")

==== OUTPUT ====
"@
  ($header + "`r`n" + $stdout) | Out-File -FilePath $OutFile -Encoding UTF8
  return $exit
}

$CloseoutRoot = Join-Path $RepoRoot ("closeout\" + $TagName)
if (-not (Test-Path $CloseoutRoot)) {
  throw "Closeout folder not found: $CloseoutRoot"
}

$DeployDir = Join-Path $CloseoutRoot "evidence\DEPLOY"
New-Dir $DeployDir

# Basic environment snapshot (non-secret)
$envInfo = @()
$envInfo += "UTC: " + (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
$envInfo += "ComputerName: $env:COMPUTERNAME"
$envInfo += "User: $env:USERNAME"
$envInfo += "OS: " + (Get-CimInstance Win32_OperatingSystem | Select-Object -ExpandProperty Caption)
$envInfo += "PSVersion: " + $PSVersionTable.PSVersion.ToString()
Write-Text (Join-Path $DeployDir "deploy_env.txt") ($envInfo -join "`r`n")

# Smoke run
$exit = Run-Capture $SmokeCommand (Join-Path $DeployDir "smoke_output.txt")

# Append a small note into closeout_note.md (idempotent-ish)
$notePath = Join-Path $CloseoutRoot "closeout_note.md"
if (Test-Path $notePath) {
  $existing = Get-Content $notePath -Raw -Encoding UTF8
  if ($existing -notmatch "## Deployment / Smoke Evidence") {
    $append = @"

## Deployment / Smoke Evidence
- evidence/DEPLOY/deploy_env.txt
- evidence/DEPLOY/smoke_output.txt
"@
    Write-Text $notePath ($existing + $append)
  }
}

# Refresh SHA-256 manifest for entire pack
$manifestPath = Join-Path $CloseoutRoot "MANIFEST_SHA256.txt"
$allFiles = Get-ChildItem -Path $CloseoutRoot -Recurse -File | Sort-Object FullName
$lines = foreach ($f in $allFiles) {
  $hash = (Get-FileHash -Algorithm SHA256 -Path $f.FullName).Hash.ToLowerInvariant()
  $rel  = $f.FullName.Substring($CloseoutRoot.Length).TrimStart('\')
  "$hash  $rel"
}
Write-Text $manifestPath ($lines -join "`r`n")

Write-Host ""
Write-Host "SMOKE EVIDENCE CAPTURED:"
Write-Host "  $DeployDir"
Write-Host "Manifest refreshed: MANIFEST_SHA256.txt"
$resultString = if ($exit -eq 0) { "PASS" } else { "FAIL (see smoke_output.txt)" }
Write-Host ("Smoke result: " + $resultString)
exit $exit
