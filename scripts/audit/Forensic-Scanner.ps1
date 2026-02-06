[CmdletBinding()]
param(
    [string]$RepoRoot = "",
    [string]$OutFile = "evidence/manifests/ARTEFACT_MAP.json"
)

$ErrorActionPreference = 'Stop'

if ([string]::IsNullOrWhiteSpace($RepoRoot)) {
    $RepoRoot = (Resolve-Path $PSScriptRoot\..\..).Path
}

Write-Host "--- AGENT 1: FORENSIC SCANNER ---" -ForegroundColor Cyan
Write-Host "Scanning repository for artefacts..." -ForegroundColor Gray

$ScanPaths = @(
    "CANON",
    "governance",
    "CONSTITUTION.md",
    "SOP_DAILY.md",
    "evidence",
    "README.md",
    "CHANGELOG.md",
    "scripts/audit",
    "docs/audit"
)

$ArtefactMap = @()

foreach ($path in $ScanPaths) {
    $absPath = Join-Path $RepoRoot $path
    if (Test-Path $absPath) {
        $files = if (Test-Path $absPath -PathType Container) {
            Get-ChildItem -Path $absPath -File -Recurse
        } else {
            Get-Item -Path $absPath
        }

        foreach ($file in $files) {
            $relPath = (Resolve-Path $file.FullName -Relative).TrimStart(".\")
            # Skip some obvious non-artefacts if they slipped in
            if ($relPath -match "node_modules|\.git|\.next") { continue }

            Write-Host "Hashing: $relPath" -ForegroundColor Gray
            $hash = (Get-FileHash -Algorithm SHA256 -Path $file.FullName).Hash.ToLower()
            
            $ArtefactMap += [ordered]@{
                path = $relPath
                hash_sha256 = $hash
                size_bytes = $file.Length
                timestamp = $file.LastWriteTime.ToUniversalTime().ToString("o")
            }
        }
    } else {
        Write-Host "Warning: Path not found: $path" -ForegroundColor Yellow
    }
}

$ArtefactMap | ConvertTo-Json -Depth 10 | Set-Content -Path (Join-Path $RepoRoot $OutFile) -Encoding UTF8
Write-Host "Artefact Map written to: $OutFile" -ForegroundColor Green
