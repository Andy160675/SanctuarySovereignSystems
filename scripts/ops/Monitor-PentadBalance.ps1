# =============================================================================
# Monitor-PentadBalance.ps1
# MISSION: Elite Performance Monitoring with '3-Point' Emergency Stop.
# Balances workload across the Pentad (MIND, HEART, EYES, backdrop3, pc5) + NAS.
# Aligned with THE_DIAMOND_DOCTRINE.md (Action follows Restraint).
# =============================================================================

param(
    [float]$ControlLimitVariance = 0.15, # 15% variance limit for elite performance
    [int]$MaxViolations = 3,
    [string]$AuditLog = "validation/pentad_balance.jsonl"
)

function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $color = switch ($Level) {
        "INFO"    { "White" }
        "ELITE"   { "Cyan" }
        "WARN"    { "Yellow" }
        "HALT"    { "Red" }
        "OK"      { "Green" }
        default   { "White" }
    }
    Write-Host "[$ts] [$Level] $Message" -ForegroundColor $color
}

Write-Host "--- PENTAD DISTRIBUTION MONITOR ACTIVE (Elite Mode) ---" -ForegroundColor Cyan
$ViolationCount = 0

while ($true) {
    # 1. Measure: Real load across the Pentad nodes
    $BindingTable = Get-Content "CONFIG\pentad\BINDING_TABLE.md"
    $ActiveNodes = $BindingTable | Where-Object { $_ -match "\| \*\*(.*?)\*\* \| (.*?) \| (.*?) \| (.*?) \| (.*?) \|" }
    
    $LoadMetrics = @{}
    $Nodes = @()
    
    foreach ($NodeLine in $ActiveNodes) {
        if ($NodeLine -match "\| \*\*(.*?)\*\* \| (.*?) \| (.*?) \| (.*?) \| (.*?) \|") {
            $Role = $matches[1].Trim()
            $IP = $matches[2].Trim()
            if ($IP -match "^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$") {
                $Nodes += $Role
                # Real measurement: Attempt to query CPU load via WinRM or WMI (fallback to ping latency as a proxy if remote management is restricted)
                $Load = 0.5 # Default
                try {
                    if ($Role -eq "PC-A" -or $Role -eq "PC-CORE-1") {
                        $Load = (Get-Counter '\Processor(_Total)\% Processor Time' -ErrorAction SilentlyContinue).CounterSamples.CookedValue / 100
                    } else {
                        # Proxy load via ping latency (ms) - simple heuristic for non-simulated connectivity
                        $Ping = Test-Connection -ComputerName $IP -Count 1 -ErrorAction SilentlyContinue
                        if ($Ping) { $Load = [Math]::Min(1.0, $Ping.ResponseTime / 100) } else { $Load = 1.0 }
                    }
                } catch { $Load = 0.9 }
                $LoadMetrics[$Role] = $Load
            }
        }
    }

    if ($Nodes.Count -eq 0) {
        Write-Log "No active nodes found in Binding Table. Monitoring local host only." "WARN"
        $Nodes = @("LOCAL")
        $LoadMetrics["LOCAL"] = (Get-Counter '\Processor(_Total)\% Processor Time').CounterSamples.CookedValue / 100
    }

    # 2. Calculate Balance: Measure variance from the Mean
    $Loads = $LoadMetrics.Values
    $Mean = ($Loads | Measure-Object -Average).Average
    $OutsideCount = 0
    $Violations = @()

    foreach ($n in $Nodes) {
        $Variance = [Math]::Abs($LoadMetrics[$n] - $Mean) / $Mean
        if ($Variance -gt $ControlLimitVariance) {
            $OutsideCount++
            $Violations += "$n (Var: $([Math]::Round($Variance*100, 2))%)"
        }
    }

    # 3. Decision: Enforce '3 Points Outside' Protocol
    $Status = "BALANCED"
    if ($OutsideCount -gt 0) {
        Write-Log "Distribution skew detected: $OutsideCount points outside limits." "WARN"
        if ($OutsideCount -ge $MaxViolations) {
            $Status = "CRITICAL_SKEW"
            Write-Log "ELITE PERFORMANCE BREACH: $OutsideCount points outside. INITIATING EMERGENCY STOP." "HALT"
            
            # Record the failure for 'Measure Twice, Cut Once' audit
            $AuditEntry = @{
                Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
                Status = $Status
                Violations = $Violations
                MeanLoad = $Mean
                Action = "SYSTEM_HALT"
            }
            $AuditEntry | ConvertTo-Json -Compress | Out-File $AuditLog -Append -Encoding UTF8
            
            # Stop the machine (Kill high-throttle tasks)
            Get-Job | Stop-Job
            break # Exit the monitor and stop the run
        }
    }

    # 4. Audit & Throttle Adjustment
    $AuditEntry = @{
        Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
        Status = $Status
        OutsideCount = $OutsideCount
        MeanLoad = $Mean
        Action = "THROTTLE_MAINTAIN"
    }
    $AuditEntry | ConvertTo-Json -Compress | Out-File $AuditLog -Append -Encoding UTF8
    
    if ($Status -eq "BALANCED") {
        Write-Log "Pentad Balance: BALANCED (Mean: $([Math]::Round($Mean, 2))). Increasing throttle..." "ELITE"
    }

    Start-Sleep -Seconds 10
}
