[CmdletBinding()]
param(
  # Repo root (defaults to parent of scripts directory)
  [string]$RepoRoot = '',
  # Output directory for manifests
  [string]$OutDir = '',
  # Deterministic timestamp stamp for the manifest filename, e.g. 20260203T022700Z
  [string]$ManifestStamp = '',
  # Hostname to embed in filename; default is current machine name
  [string]$Hostname = $env:COMPUTERNAME,
  # Relative files to include in manifest (SHA256 only; no content)
  [string[]]$Include = @(
    'CANON/TRINITY_DEPLOYMENT_PROTOCOL.md',
    'fleet/inventory.json',
    'fleet/trios.json',
    'scripts/fleet/orchestrate_fleet.ps1',
    'scripts/make_repo_manifest.ps1',
    'evidence/TRINITY_DEPLOYMENT_VERIFICATION.md',
    'evidence/SITREP.md'
  )
)

$ErrorActionPreference = 'Stop'

function Get-Sha256File([string]$path) {
  (Get-FileHash -Algorithm SHA256 -LiteralPath $path).Hash.ToLower()
}

if([string]::IsNullOrWhiteSpace($RepoRoot)){
  $RepoRoot = Resolve-Path (Join-Path $PSScriptRoot '..') | Select-Object -ExpandProperty Path
}

if([string]::IsNullOrWhiteSpace($OutDir)){
  $OutDir = Join-Path $RepoRoot 'evidence/manifests'
}

$stamp = if([string]::IsNullOrWhiteSpace($ManifestStamp)) { (Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssZ') } else { $ManifestStamp }
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null

$manifestPath = Join-Path $OutDir ("repo_manifest_{0}_{1}.json" -f $Hostname,$stamp)

$files = @()
foreach($rel in $Include){
  $abs = Join-Path $RepoRoot $rel
  if(Test-Path -LiteralPath $abs){
    $files += [ordered]@{ path=$rel; sha256=(Get-Sha256File $abs) }
  } else {
    $files += [ordered]@{ path=$rel; sha256=$null; missing=$true }
  }
}

$doc = [ordered]@{
  generated_utc = (Get-Date).ToUniversalTime().ToString('o')
  hostname = $Hostname
  stamp = $stamp
  files = $files
}

($doc | ConvertTo-Json -Depth 6) | Set-Content -LiteralPath $manifestPath -Encoding UTF8
Write-Host "Manifest written: $manifestPath" -ForegroundColor Green
