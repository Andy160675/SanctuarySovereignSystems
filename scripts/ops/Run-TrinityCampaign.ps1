<#!
.SYNOPSIS
    Run a bounded Trinity campaign (12,000 agents by default) with safe concurrency and audit-only guardrails.
.DESCRIPTION
    Wrapper for trinity\run_campaign.py. Ensures Python env and sets governance env vars.
.PARAMETER Total
    Total number of cases to run (default 12000)
.PARAMETER Concurrency
    Max concurrent cases (default 2000; capped at 5000)
.PARAMETER Query
    Query phrase for Investigator (default: "system sweep")
.PARAMETER Output
    Output JSONL path (default under evidence\campaigns)
.PARAMETER AuditOnly
    If present, sets TRINITY_AUDIT_ONLY=1 to prevent actuation.
.EXAMPLE
    .\Run-TrinityCampaign.ps1 -AuditOnly
#>
[CmdletBinding()]
param(
    [int]$Total = 12000,
    [int]$Concurrency = 2000,
    [string]$Query = "system sweep",
    [string]$Output,
    [switch]$AuditOnly
)

$ErrorActionPreference = 'Stop'

# Ensure we run from repo root if executed elsewhere
$RepoRoot = Split-Path -Parent -Path (Split-Path -Parent $PSCommandPath)
Set-Location $RepoRoot

# Governance: enforce audit-only if requested
if ($AuditOnly) { $env:TRINITY_AUDIT_ONLY = '1' }

# Python executable
$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) { $python = Get-Command py -ErrorAction SilentlyContinue }
if (-not $python) { throw "Python not found in PATH." }

# Default output
if (-not $Output) {
    $stamp = (Get-Date).ToString('yyyy-MM-ddTHH-mm-ssZ')
    $Output = Join-Path $RepoRoot "evidence/campaigns/trinity_campaign_$stamp.jsonl"
}

Write-Host "[INFO] Running Trinity campaign..." -ForegroundColor Cyan
Write-Host "        Total=$Total Concurrency=$Concurrency AuditOnly=$($AuditOnly.IsPresent)" -ForegroundColor Gray
Write-Host "        Output=$Output" -ForegroundColor Gray

$cmd = @(
    "trinity/run_campaign.py",
    "--total", $Total,
    "--concurrency", $Concurrency,
    "--query", $Query,
    "--out", $Output
)
if ($AuditOnly) { $cmd += "--auditOnly" }

& $python $cmd

Write-Host "[INFO] Campaign finished." -ForegroundColor Green
