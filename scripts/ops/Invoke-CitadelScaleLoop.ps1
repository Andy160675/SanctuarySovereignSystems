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

function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $color = switch ($Level) {
        "INFO"     { "White" }
        "WARN"     { "Yellow" }
        "ERROR"    { "Red" }
        "OK"       { "Green" }
        "CITADEL"  { "Cyan" }
        default    { "White" }
    }
    Write-Host "[$ts] [$Level] $Message" -ForegroundColor $color
}

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
    $MatchLine = $OptResult | Out-String -Stream | Where-Object { $_ -match "Average System Efficiency Gain: ([\d.]+)%" }
    if ($MatchLine -and $MatchLine -match "Average System Efficiency Gain: ([\d.]+)%") {
        $Efficiency = [double]$Matches[1]
    }
    
    # 4. Check Monitor for Skew
    Start-Sleep -Seconds 5 # Increased for real measurement
    $MonitorOutput = Receive-Job -Job $MonitorJob
    $SkewDetected = $MonitorOutput -match "EMERGENCY STOP" -or $MonitorOutput -match "CRITICAL_SKEW" -or $MonitorOutput -match "distribution skew detected"
    
    Stop-Job $MonitorJob
    Remove-Job $MonitorJob
    
    $Status = "SUCCESS"
    if ($SkewDetected) { $Status = "SKEW_DETECTED" }
    
    $LogEntry = @{
        Iteration = $i
        Timestamp = (Get-Date).ToString("yyyy-MM-dd HH:mm:ssZ")
        AgentQty = $CurrentAgentQty
        EfficiencyGain = $Efficiency
        SkewDetected = ($SkewDetected -eq $true)
        Status = $Status
    }
    
    $LogEntry | ConvertTo-Json -Compress | Out-File -FilePath $LogFile -Append -Encoding UTF8
    
    $Color = if ($SkewDetected) { "Red" } else { "Green" }
    Write-Host "[LOOP $i/$Iterations] Complete. Gain: $Efficiency% | Skew: $SkewDetected | Qty: $CurrentAgentQty" -ForegroundColor $Color
    
    if ($SkewDetected) {
        $Reduction = [Math]::Max(100, [int]($CurrentAgentQty * 0.1))
        $CurrentAgentQty -= $Reduction
        Write-Log "Critical Skew Detected. Reducing Agent Qty by $Reduction to $CurrentAgentQty for next cycle." "WARN"
        if ($CurrentAgentQty -lt 100) {
            Write-Log "Agent Qty below minimum threshold. Terminating Sequence." "ERROR"
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
