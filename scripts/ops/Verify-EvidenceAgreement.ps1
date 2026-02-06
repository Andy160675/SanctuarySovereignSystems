[CmdletBinding()]
param(
    [string]$SharePath = "S:\baselines",
    [switch]$Gate,
    [string]$RepoRoot = ""
)

$ErrorActionPreference = 'Stop'

if ([string]::IsNullOrWhiteSpace($RepoRoot)) {
    $RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
}

Write-Host "--- VERIFYING EVIDENCE AGREEMENT ---" -ForegroundColor Cyan

if (-not (Test-Path $SharePath)) {
    Write-Host "Error: Share path $SharePath not found. Verify mount 'net use S: ...'" -ForegroundColor Red
    if ($Gate) { exit 1 } else { return }
}

# Get latest baseline for each node
$NodeDirs = Get-ChildItem -Path $SharePath -Directory
$LatestBaselines = @{}

foreach ($dir in $NodeDirs) {
    $latest = Get-ChildItem -Path $dir.FullName -Filter "evidence_baseline_summary_*.json" | Sort-Object Name -Descending | Select-Object -First 1
    if ($latest) {
        $LatestBaselines[$dir.Name] = Get-Content -Path $latest.FullName -Raw | ConvertFrom-Json
        Write-Host "Found latest baseline for $($dir.Name): $($latest.Name)" -ForegroundColor Gray
    }
}

if ($LatestBaselines.Count -lt 2) {
    Write-Host "Insufficient baselines for comparison (found $($LatestBaselines.Count))." -ForegroundColor Yellow
    return
}

$DivergedCount = 0
$TotalComparisons = 0
$Report = [ordered]@{
    VerificationTimestamp = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
    NodesChecked = $LatestBaselines.Keys
    Results = @()
    EscalationState = "GREEN"
}

# Use the first node as the reference
$NodeNames = $LatestBaselines.Keys | Sort-Object
$RefNode = $NodeNames[0]
$RefData = $LatestBaselines[$RefNode]

Write-Host "Using $RefNode as reference." -ForegroundColor Cyan

foreach ($node in $NodeNames) {
    if ($node -eq $RefNode) { continue }
    
    $CurrentData = $LatestBaselines[$node]
    $Agreement = $true
    $Mismatches = @()

    # Compare Evidence (hashes)
    foreach ($refFile in $RefData.Evidence) {
        $match = $CurrentData.Evidence | Where-Object { $_.Path -eq $refFile.Path }
        if (-not $match) {
            $Agreement = $false
            $Mismatches += "Missing file: $($refFile.Path)"
        } elseif ($match.SHA256 -ne $refFile.SHA256) {
            $Agreement = $false
            $Mismatches += "Hash mismatch for $($refFile.Path): $($match.SHA256) vs $($refFile.SHA256)"
        }
    }

    $TotalComparisons++
    if (-not $Agreement) {
        $DivergedCount++
        Write-Host "DIVERGENCE DETECTED on node: $node" -ForegroundColor Red
        foreach($m in $Mismatches) { Write-Host "  - $m" -ForegroundColor Red }
    } else {
        Write-Host "Node $node agrees with $RefNode." -ForegroundColor Green
    }

    $Report.Results += [ordered]@{
        Node = $node
        Agreement = $Agreement
        Mismatches = $Mismatches
    }
}

# Determine Escalation State
# Green: agreement -> execute
# Yellow: partial disagreement -> hold + review (e.g. 1 node disagrees out of many)
# Red: no agreement -> halt (e.g. majority disagrees or all nodes disagree)

if ($DivergedCount -eq 0) {
    $Report.EscalationState = "GREEN"
} elseif ($DivergedCount -lt ($TotalComparisons / 2)) {
    $Report.EscalationState = "YELLOW"
} else {
    $Report.EscalationState = "RED"
}

# Final telemetry
$ReportDir = Join-Path $RepoRoot "evidence/verification"
if (-not (Test-Path $ReportDir)) { New-Item -ItemType Directory -Path $ReportDir -Force | Out-Null }
$ReportPath = Join-Path $ReportDir "evidence_agreement_report_$(Get-Date -Format 'yyyyMMdd_HHmmss').json"
$Report | ConvertTo-Json -Depth 10 | Set-Content -Path $ReportPath -Encoding UTF8

$Hash = (Get-FileHash -Algorithm SHA256 -Path $ReportPath).Hash.ToLower()
$ReceiptPath = $ReportPath + ".sha256"
"$Hash  $($ReportPath | Split-Path -Leaf)" | Set-Content -Path $ReceiptPath

Write-Host "Report written: $ReportPath" -ForegroundColor Green
Write-Host "Receipt written: $ReceiptPath" -ForegroundColor Green

switch ($Report.EscalationState) {
    "GREEN" {
        Write-Host "STATUS: GREEN - All nodes in agreement. Execute." -ForegroundColor Green
    }
    "YELLOW" {
        Write-Host "STATUS: YELLOW - Partial disagreement ($DivergedCount/$TotalComparisons nodes). HOLD + REVIEW." -ForegroundColor Yellow
        if ($Gate) { exit 1 }
    }
    "RED" {
        Write-Host "STATUS: RED - Significant disagreement ($DivergedCount/$TotalComparisons nodes). HALT + INVESTIGATE." -ForegroundColor Red
        if ($Gate) { exit 1 }
    }
}
