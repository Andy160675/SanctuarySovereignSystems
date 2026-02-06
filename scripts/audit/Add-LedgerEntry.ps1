[CmdletBinding()]
param(
    [string]$RepoRoot = "",
    [string]$Event = "Audit pipeline execution",
    [string]$ArtefactHash = "",
    [string]$Actor = "Junie (Autonomous Programmer)",
    [string]$Notes = ""
)

$ErrorActionPreference = 'Stop'

if ([string]::IsNullOrWhiteSpace($RepoRoot)) {
    $RepoRoot = (Resolve-Path $PSScriptRoot\..\..).Path
}

$LedgerPath = Join-Path $RepoRoot "evidence/ledger/DECISION_LEDGER.jsonl"

$Entry = [ordered]@{
    timestamp = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
    event = $Event
    artefact_hash = $ArtefactHash
    actor = $Actor
    notes = $Notes
}

$Line = $Entry | ConvertTo-Json -Compress
$Line | Out-File -FilePath $LedgerPath -Append -Encoding UTF8

Write-Host "Ledger entry added: $Event" -ForegroundColor Gray
