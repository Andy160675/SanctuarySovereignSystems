[CmdletBinding()]
param(
    [string]$NodeId = $env:COMPUTERNAME,
    [string]$SharePath = "S:\baselines",
    [string]$RepoRoot = "",
    [string]$FirmwarePath = ""
)

$ErrorActionPreference = 'Stop'

if ([string]::IsNullOrWhiteSpace($RepoRoot)) {
    $RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
}

# Define what constitutes the "Evidence Baseline"
$CriticalFiles = @(
    'CANON/TRINITY_DEPLOYMENT_PROTOCOL.md',
    'CONSTITUTION.md',
    'SECURITY.md',
    'scripts/ops/Capture-EvidenceBaseline.ps1'
)

Write-Host "--- CAPTURING EVIDENCE BASELINE FOR NODE: $NodeId ---" -ForegroundColor Cyan

$BaselineData = [ordered]@{
    NodeId = $NodeId
    Timestamp = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
    Environment = @{
        OS = $PSVersionTable.OS
        PSVersion = $PSVersionTable.PSVersion.ToString()
    }
    Evidence = @()
}

foreach ($file in $CriticalFiles) {
    $absPath = Join-Path $RepoRoot $file
    if (Test-Path $absPath) {
        $hash = (Get-FileHash -Algorithm SHA256 -Path $absPath).Hash.ToLower()
        $BaselineData.Evidence += [ordered]@{
            Path = $file
            SHA256 = $hash
        }
        Write-Host "Captured: $file ($hash)" -ForegroundColor Gray
    } else {
        $BaselineData.Evidence += [ordered]@{
            Path = $file
            SHA256 = $null
            Status = "MISSING"
        }
        Write-Host "Warning: Missing critical file $file" -ForegroundColor Yellow
    }
}

# Capture Firmware if provided
if (-not [string]::IsNullOrWhiteSpace($FirmwarePath)) {
    if (Test-Path $FirmwarePath) {
        $hash = (Get-FileHash -Algorithm SHA256 -Path $FirmwarePath).Hash.ToLower()
        $BaselineData.Evidence += [ordered]@{
            Path = [System.IO.Path]::GetFileName($FirmwarePath)
            SHA256 = $hash
            Type = "Firmware"
        }
        Write-Host "Captured Firmware: $FirmwarePath ($hash)" -ForegroundColor Green
    } else {
        Write-Host "Warning: Firmware path $FirmwarePath not found." -ForegroundColor Yellow
    }
}

$TimestampStr = (Get-Date -Format "yyyyMMdd_HHmmss")
$FileName = "evidence_baseline_summary_$TimestampStr.json"
$LocalDir = Join-Path $RepoRoot "evidence/baselines/$NodeId"
if (-not (Test-Path $LocalDir)) { New-Item -ItemType Directory -Path $LocalDir -Force | Out-Null }

$LocalPath = Join-Path $LocalDir $FileName
$BaselineData | ConvertTo-Json -Depth 10 | Set-Content -Path $LocalPath -Encoding UTF8
Write-Host "Local baseline saved to: $LocalPath" -ForegroundColor Green

# Publish to Share
if (Test-Path $SharePath) {
    $TargetDir = Join-Path $SharePath $NodeId
    if (-not (Test-Path $TargetDir)) { New-Item -ItemType Directory -Path $TargetDir -Force | Out-Null }
    
    $TargetPath = Join-Path $TargetDir $FileName
    Copy-Item -Path $LocalPath -Destination $TargetPath -Force
    Write-Host "Published to Share: $TargetPath" -ForegroundColor Green
} else {
    Write-Host "Warning: Share path $SharePath not found. Ensure NAS is mounted to S:." -ForegroundColor Yellow
}
