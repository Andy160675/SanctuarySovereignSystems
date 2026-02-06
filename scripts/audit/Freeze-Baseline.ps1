[CmdletBinding()]
param(
    [string]$RepoRoot = ".",
    [string]$OutDir = "evidence/manifests",
    [string]$Stamp = ""
)

$ErrorActionPreference = 'Stop'

if ([string]::IsNullOrWhiteSpace($Stamp)) {
    $Stamp = (Get-Date).ToUniversalTime().ToString("yyyyMMdd_HHmmss")
}

$ManifestPath = Join-Path $OutDir "STATE0_manifest_$Stamp.json"
$ManifestHashPath = Join-Path $OutDir "STATE0_manifest_$Stamp.sha256"

Write-Host "--- FREEZING BASELINE (STATE 0) ---" -ForegroundColor Cyan

$Files = Get-ChildItem -Path $RepoRoot -Recurse -File | Where-Object { 
    $_.FullName -notlike "*\.git\*" -and 
    $_.FullName -notlike "*\node_modules\*" -and
    $_.FullName -notlike "*\evidence\manifests\*" -and
    $_.FullName -notlike "*\evidence\verification\*"
}

$Manifest = [ordered]@{
    Type = "STATE0_BASELINE"
    Timestamp = (Get-Date).ToUniversalTime().ToString("o")
    Stamp = $Stamp
    Artefacts = @()
}

foreach ($file in $Files) {
    $relPath = Resolve-Path -Path $file.FullName -Relative
    # Clean up relative path formatting
    $relPath = $relPath -replace '^\.\\', ''
    
    $hash = (Get-FileHash -Algorithm SHA256 -Path $file.FullName).Hash.ToLower()
    
    $Manifest.Artefacts += [ordered]@{
        path = $relPath
        hash_sha256 = $hash
        size_bytes = $file.Length
        timestamp = $file.LastWriteTime.ToUniversalTime().ToString("o")
    }
}

$ManifestJson = $Manifest | ConvertTo-Json -Depth 10
$ManifestJson | Set-Content -Path $ManifestPath -Encoding UTF8

$ManifestHash = (Get-FileHash -Algorithm SHA256 -Path $ManifestPath).Hash.ToLower()
"$ManifestHash  $(Split-Path $ManifestPath -Leaf)" | Set-Content -Path $ManifestHashPath

Write-Host "Baseline frozen: $ManifestPath" -ForegroundColor Green
Write-Host "Manifest hash: $ManifestHash" -ForegroundColor Green
