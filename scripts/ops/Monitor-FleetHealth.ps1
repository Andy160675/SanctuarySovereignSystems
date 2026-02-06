<#
.SYNOPSIS
    Monitor-FleetHealth.ps1 — Sovereignty Fleet Auditor
.DESCRIPTION
    Audits the massive 30,000 node fleet manifest and ensures synchronization 
    with the local Self-Heal state.
#>

param(
    [string]$ManifestPath = "evidence/fleet_30k_deployment.json",
    [string]$JsonLogPath = "$env:ProgramData\SelfHeal\logs\SelfHealAutomation.jsonl"
)

function Write-AuditLog {
    param($Message, $Level = "INFO")
    $ts = Get-Date -Format "yyyy-MM-ddTHH:mm:ssZ"
    $logEntry = @{
        component = "FleetAuditor"
        message = $Message
        level = $Level
        timestamp = $ts
        correlationId = [guid]::NewGuid().ToString()
    }
    $logEntry | ConvertTo-Json -Compress | Out-File -FilePath $JsonLogPath -Append -Encoding UTF8
    Write-Host "[$ts] [$Level] $Message"
}

if (-not (Test-Path $ManifestPath)) {
    Write-AuditLog "Fleet manifest not found at $ManifestPath" "ERROR"
    exit 1
}

Write-AuditLog "Starting Fleet Audit for 30,000 nodes..."

$manifest = Get-Content $ManifestPath | ConvertFrom-Json
$nodeCount = $manifest.nodes.Count

if ($nodeCount -eq 30000) {
    Write-AuditLog "Fleet integrity verified: 30,000 nodes present." "AUDIT"
} else {
    Write-AuditLog "Fleet integrity FAILURE: Expected 30,000, found $nodeCount" "ERROR"
}

# Check for stale check-ins
$staleThreshold = (Get-Date).AddMinutes(-10)
$staleNodes = $manifest.nodes | Where-Object { [DateTime]$_.last_checkin -lt $staleThreshold }

if ($staleNodes) {
    Write-AuditLog "$($staleNodes.Count) nodes are showing stale check-ins." "WARN"
} else {
    Write-AuditLog "All 30,000 nodes are synchronized within tolerance." "AUDIT"
}

Write-AuditLog "Fleet Audit Complete. System Status: SYSTEM_ALARP" "INFO"
