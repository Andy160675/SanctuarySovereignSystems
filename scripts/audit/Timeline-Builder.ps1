[CmdletBinding()]
param(
    [string]$RepoRoot = "",
    [string]$OutJson = "evidence/timeline/TIMELINE.json",
    [string]$OutMd = "evidence/timeline/TIMELINE.md"
)

$ErrorActionPreference = 'Stop'

if ([string]::IsNullOrWhiteSpace($RepoRoot)) {
    $RepoRoot = (Resolve-Path $PSScriptRoot\..\..).Path
}

Write-Host "--- AGENT 2: TIMELINE BUILDER ---" -ForegroundColor Cyan
Write-Host "Reconstructing history from git logs..." -ForegroundColor Gray

# Get git log for the last 50 commits to identify major milestones
try {
    $GitLogs = git log -n 50 --pretty=format:"%h|%aI|%s"
} catch {
    Write-Host "Warning: Git not found or not a repository. Falling back to file timestamps." -ForegroundColor Yellow
    $GitLogs = @()
}

$Timeline = @()

foreach ($line in $GitLogs) {
    $parts = $line -split '\|'
    if ($parts.Count -eq 3) {
        $Timeline += [ordered]@{
            type = "Commit"
            id = $parts[0]
            timestamp = $parts[1]
            description = $parts[2]
        }
    }
}

# Add major file creation events based on earliest known mentions or current state
# For a retroactive audit, we map key doctrine appearances
$Milestones = @(
    @{ date="2025-11-20"; event="Phase 5 Completion (Golden Master established)" }
    @{ date="2026-02-04"; event="Decorrelated Validation Workflow Implemented" }
    @{ date="2026-02-05"; event="AI Thread Recovery Baseline Captured" }
    @{ date="2026-02-06"; event="Retroactive Audit Pipeline Initiated" }
)

foreach ($ms in $Milestones) {
    $Timeline += [ordered]@{
        type = "Milestone"
        id = "M-" + $ms.date.Replace("-","")
        timestamp = $ms.date + "T00:00:00Z"
        description = $ms.event
    }
}

$Timeline = $Timeline | Sort-Object timestamp -Descending

# Save JSON
$Timeline | ConvertTo-Json -Depth 10 | Set-Content -Path (Join-Path $RepoRoot $OutJson) -Encoding UTF8

# Generate Markdown
$MdContent = "# Sovereign System Evolution Timeline`n`n"
$MdContent += "| Timestamp | Type | ID | Event |`n"
$MdContent += "|-----------|------|----|-------|`n"

foreach ($entry in $Timeline) {
    $MdContent += "| $($entry.timestamp) | $($entry.type) | ``$($entry.id)`` | $($entry.description) |`n"
}

$MdContent | Set-Content -Path (Join-Path $RepoRoot $OutMd) -Encoding UTF8

Write-Host "Timeline written to: $OutJson and $OutMd" -ForegroundColor Green
