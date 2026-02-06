<#
.SYNOPSIS
  Writes a custody stamp OUTSIDE the closeout pack (does not mutate frozen evidence).

.USAGE
  powershell -File tools\stamp_custody.ps1 -TagName "restore-healthy-20251230"
#>

[CmdletBinding()]
param(
  [string]$RepoRoot = (Get-Location).Path,
  [Parameter(Mandatory=$true)][string]$TagName
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$closeoutRoot = Join-Path $RepoRoot ("closeout\" + $TagName)
$manifest     = Join-Path $closeoutRoot "MANIFEST_SHA256.txt"
if (-not (Test-Path $manifest)) { throw "Manifest not found: $manifest" }

$custodyDir  = Join-Path $RepoRoot "custody"
if (-not (Test-Path $custodyDir)) { New-Item -ItemType Directory -Path $custodyDir | Out-Null }
$custodyFile = Join-Path $custodyDir "custody.jsonl"

$stamp = [pscustomobject]@{
  utc            = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
  tag            = $TagName
  computer       = $env:COMPUTERNAME
  user           = $env:USERNAME
  manifest_sha256= (Get-FileHash -Algorithm SHA256 -Path $manifest).Hash.ToLowerInvariant()
} | ConvertTo-Json -Compress

Add-Content -Path $custodyFile -Value $stamp -Encoding UTF8

Write-Host "CUSTODY STAMP WRITTEN:"
Write-Host "  $custodyFile"
