<#
.SYNOPSIS
    Sovereign Citadel: Scale-Verification Loop (25 Cycles).
    Executes autonomous optimization cycles to verify system stability at scale.

.DESCRIPTION
    1. Runs Invoke-AgentOptimization-2700.ps1 for 25 iterations.
    2. Monitors elite-balance and captures delta reports.
    3. Aligns with Phase 2 Safe Citadel requirements.
#>

param(
    [string]$AuthCode = "0000",
    [string]$OptimizationCode = "1234",
    [int]$Iterations = 25,
    [int]$InitialAgentQty = 2700
)

$PSScriptRoot = Get-Location
$LogFile = "validation/citadel_loop_metrics.jsonl"
$CurrentAgentQty = $InitialAgentQty

Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "   CITADEL SCALE VERIFICATION: DYNAMIC AGENT MANAGEMENT" -ForegroundColor Cyan
Write-Host "   Protocol: Autonomous Optimization | Target: $Iterations Cycles" -ForegroundColor Cyan
Write-Host "============================================================`n" -ForegroundColor Cyan

$StartTime = Get-Date

for ($i = 1; $i -le $Iterations; $i++) {
    Write-Host "[LOOP $i/$Iterations] Starting Cycle with $CurrentAgentQty Agents..." -ForegroundColor Yellow
    
    # 1. Start Balance Monitor in background
    $MonitorJob = Start-Job -ScriptBlock {
        Set-Location $using:PSScriptRoot
        PowerShell.exe -ExecutionPolicy Bypass -File .\scripts\ops\Monitor-PentadBalance.ps1 -IntervalSeconds 5
    } -Name "CitadelLoopMonitor-$i"
    
    # 2. Run Optimization with specified agent quantity
    $OptResult = & .\scripts\ops\Invoke-AgentOptimization-2700.ps1 -AuthCode $AuthCode -OptimizationCode $OptimizationCode -AgentCount $CurrentAgentQty
    
    # 3. Capture Metric
    $Efficiency = 0
    # Search in array output
    $Match = $OptResult | Where-Object { $_ -match "Average System Efficiency Gain: ([\d.]+)%" }
    if ($Match -and $Match -match "Average System Efficiency Gain: ([\d.]+)%") {
        $Efficiency = [double]$matches[1]
    }
    
    # 4. Check Monitor for Skew
    Start-Sleep -Seconds 2
    $MonitorOutput = Receive-Job -Job $MonitorJob
    $SkewDetected = $MonitorOutput -match "EMERGENCY STOP"
    
    Stop-Job $MonitorJob
    Remove-Job $MonitorJob
    
    $Status = if ($SkewDetected) { "SKEW_DETECTED" } else { "SUCCESS" }
    
    $LogEntry = @{
        Iteration = $i
        Timestamp = (Get-Date).ToString("yyyy-MM-dd HH:mm:ssZ")
        AgentQty = $CurrentAgentQty
        EfficiencyGain = $Efficiency
        SkewDetected = $SkewDetected
        Status = $Status
    }
    
    $LogEntry | ConvertTo-Json -Compress | Out-File -FilePath $LogFile -Append -Encoding UTF8
    
    $Color = if ($SkewDetected) { "Red" } else { "Green" }
    Write-Host "[LOOP $i/$Iterations] Complete. Gain: $Efficiency% | Skew: $SkewDetected | Qty: $CurrentAgentQty" -ForegroundColor $Color
    
    if ($SkewDetected) {
        $Reduction = [Math]::Max(100, [int]($CurrentAgentQty * 0.1))
        $CurrentAgentQty -= $Reduction
        Write-Host "[!!!] Critical Skew Detected. Reducing Agent Qty by $Reduction to $CurrentAgentQty for next cycle." -ForegroundColor Yellow
        if ($CurrentAgentQty -lt 100) {
            Write-Host "[!!!] Agent Qty below minimum threshold. Terminating Sequence." -ForegroundColor Red
            break
        }
    }
}

$Duration = (Get-Date) - $StartTime
Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "   CITADEL SCALE VERIFICATION COMPLETE" -ForegroundColor Cyan
Write-Host "   Total Duration: $($Duration.TotalMinutes) minutes" -ForegroundColor Cyan
Write-Host "   Metrics: $LogFile" -ForegroundColor Cyan
Write-Host "============================================================`n" -ForegroundColor Cyan
