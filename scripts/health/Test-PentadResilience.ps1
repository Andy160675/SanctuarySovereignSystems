# Test-PentadResilience.ps1
# Codifies the Pentad Resilience Matrix and forcing functions.
# Enforces state transitions based on node availability and constitutional rules.

param(
    [string]$ConfigPath = "core/governance/pentad_resilience.json",
    [int]$IntervalSec = 60
)

# Resilience Matrix Definitions (Constitutional Forcing Functions)
$ForcingFunctions = @{
    "PCA_TIMEOUT"    = 15  # Minutes
    "PCE_TIMEOUT"    = 5   # Minutes
    "NAS_TIMEOUT"    = 10  # Minutes
    "DEGRADED_LIMIT" = 2   # Heads unresponsive
    "HALT_LIMIT"     = 3   # Heads unresponsive
}

$CurrentState = @{
    "Status" = "HEALTHY"
    "UnresponsiveNodes" = @()
    "LastChecked" = Get-Date
    "PCA_DownSince" = $null
    "PCE_DownSince" = $null
    "NAS_DownSince" = $null
}

function Get-NodeStatus {
    param([string]$NodeName)
    # Simulation: In production, use Test-Connection or service health endpoints
    # PC-CORE-1 is currently the only one we can "see" locally
    if ($NodeName -eq "PC-CORE-1") { return $true }
    return $false # Assume others down for this simulation
}

function Apply-ForcingFunctions {
    $now = Get-Date
    
    # 1. PC A down > 15 minutes -> Read-Only
    if ($CurrentState.PCA_DownSince -and ($now - $CurrentState.PCA_DownSince).TotalMinutes -gt $ForcingFunctions.PCA_TIMEOUT) {
        Write-Warning "FORCING FUNCTION: PC A down > 15m. Entering READ-ONLY mode."
        $CurrentState.Status = "READ-ONLY"
    }

    # 2. PC E down > 5 minutes -> External network severed
    if ($CurrentState.PCE_DownSince -and ($now - $CurrentState.PCE_DownSince).TotalMinutes -gt $ForcingFunctions.PCE_TIMEOUT) {
        Write-Error "FORCING FUNCTION: PC E down > 5m. SEVERING EXTERNAL NETWORK."
        # Invoke-SeverNetwork
    }

    # 3. NAS unreachable > 10 minutes -> Halt new workflows
    if ($CurrentState.NAS_DownSince -and ($now - $CurrentState.NAS_DownSince).TotalMinutes -gt $ForcingFunctions.NAS_TIMEOUT) {
        Write-Error "FORCING FUNCTION: NAS unreachable > 10m. HALTING NEW WORKFLOWS."
        $CurrentState.Status = "HALTED"
    }

    # 4. Any 2 heads unresponsive -> DEGRADED
    if ($CurrentState.UnresponsiveNodes.Count -ge $ForcingFunctions.DEGRADED_LIMIT) {
        $CurrentState.Status = "DEGRADED"
    }

    # 5. Any 3 heads unresponsive -> HALT Autonomous
    if ($CurrentState.UnresponsiveNodes.Count -ge $ForcingFunctions.HALT_LIMIT) {
        $CurrentState.Status = "MANUAL_ONLY"
    }
}

function Monitor-Loop {
    Write-Host "Starting Pentad Resilience Monitor..." -ForegroundColor Cyan
    $nodes = @("PC-A", "PC-B", "PC-C", "PC-D", "PC-E", "NAS")
    
    while ($true) {
        $unresponsive = @()
        foreach ($node in $nodes) {
            if (-not (Get-NodeStatus $node)) {
                $unresponsive += $node
                
                # Track specific down times
                if ($node -eq "PC-A" -and -not $CurrentState.PCA_DownSince) { $CurrentState.PCA_DownSince = Get-Date }
                if ($node -eq "PC-E" -and -not $CurrentState.PCE_DownSince) { $CurrentState.PCE_DownSince = Get-Date }
                if ($node -eq "NAS" -and -not $CurrentState.NAS_DownSince) { $CurrentState.NAS_DownSince = Get-Date }
            } else {
                # Reset down times if back up
                if ($node -eq "PC-A") { $CurrentState.PCA_DownSince = $null }
                if ($node -eq "PC-E") { $CurrentState.PCE_DownSince = $null }
                if ($node -eq "NAS") { $CurrentState.NAS_DownSince = $null }
            }
        }
        
        $CurrentState.UnresponsiveNodes = $unresponsive
        $CurrentState.LastChecked = Get-Date
        
        Apply-ForcingFunctions
        
        Write-Host "[$($CurrentState.LastChecked)] Status: $($CurrentState.Status) | Unresponsive: $($unresponsive -join ', ')"
        
        Start-Sleep -Seconds $IntervalSec
    }
}

Monitor-Loop
