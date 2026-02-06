<#
.SYNOPSIS
  Verifies a closeout pack against MANIFEST_SHA256.txt (tamper-evident check).

.USAGE
  powershell -File tools\verify_closeout_pack.ps1 -TagName "restore-healthy-20251230"
#>

[CmdletBinding()]
param(
  [string]$RepoRoot = (Get-Location).Path,
  [Parameter(Mandatory=$true)][string]$TagName
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Fail([string]$Msg) {
  Write-Host "FAIL: $Msg"
  exit 1
}

$CloseoutRoot = Join-Path $RepoRoot ("closeout\" + $TagName)
if (-not (Test-Path $CloseoutRoot)) { Fail "Closeout folder not found: $CloseoutRoot" }

$ManifestPath = Join-Path $CloseoutRoot "MANIFEST_SHA256.txt"
if (-not (Test-Path $ManifestPath)) { Fail "Manifest not found: $ManifestPath" }

$lines = Get-Content $ManifestPath -Encoding UTF8 | Where-Object { $_.Trim() -ne "" }
if ($lines.Count -eq 0) { Fail "Manifest is empty: $ManifestPath" }

$issues  = New-Object System.Collections.Generic.List[string]
$checked = 0
$skipped = 0

foreach ($line in $lines) {
  # Expect: "<sha256>  <relative_path>"
  if ($line -notmatch '^\s*([0-9a-fA-F]{64})\s{2,}(.+?)\s*$') {
    $issues.Add("Malformed manifest line: $line")
    continue
  }

  $expected = $Matches[1].ToLowerInvariant()
  $relPath  = $Matches[2].Trim()

  # Never verify the manifest against itself (self-referential)
  if ($relPath -ieq "MANIFEST_SHA256.txt") {
    $skipped++
    continue
  }

  $fullPath = Join-Path $CloseoutRoot $relPath
  if (-not (Test-Path $fullPath)) {
    $issues.Add("Missing file: $relPath")
    continue
  }

  $actual = (Get-FileHash -Algorithm SHA256 -Path $fullPath).Hash.ToLowerInvariant()
  if ($actual -ne $expected) {
    $issues.Add("Hash mismatch: $relPath`n  expected=$expected`n  actual  =$actual")
  }

  $checked++
}

if ($issues.Count -gt 0) {
  Write-Host ""
  Write-Host "TAMPER CHECK FAILED ($($issues.Count) issues):"
  $issues | ForEach-Object { Write-Host ("- " + $_) }
  exit 1
}

Write-Host ""
Write-Host "PASS: Closeout pack verified against manifest."
Write-Host "  Tag: $TagName"
Write-Host "  Root: $CloseoutRoot"
Write-Host "  Files checked: $checked"
Write-Host "  Files skipped: $skipped (manifest self-entry)"
exit 0
