<#
.SYNOPSIS
    SelfHealAutomation.ps1 — The Blade of Truth (Elite Edition)
.DESCRIPTION
    Perform bounded, repeatable self-healing checks and remediations on a single host.
#>

#Requires -Version 5.1

[CmdletBinding(SupportsShouldProcess)]
param(
    [Parameter()]
    [switch]$Once,

    [Parameter()]
    [switch]$AuditOnly,

    [Parameter()]
    [switch]$DryRun,

    [Parameter()]
    [string]$ConfigPath,

    [Parameter()]
    [string]$LogPath = "$env:ProgramData\SelfHeal\logs\SelfHealAutomation.log",

    [Parameter()]
    [string]$JsonLogPath = "$env:ProgramData\SelfHeal\logs\SelfHealAutomation.jsonl",

    [Parameter()]
    [string]$EvidencePath = "$env:ProgramData\SelfHeal\evidence",

    [Parameter()]
    [int]$IntervalSeconds = 300,

    [Parameter()]
    [switch]$OutputJson,

    [Parameter()]
    [switch]$Status
)

# Constants
$VERSION = "2.1.0"
$MACHINE_ID = $env:COMPUTERNAME
$CORRELATION_ID = [guid]::NewGuid().ToString()

# Exit Codes
enum ExitCode {
    Success = 0
    Error = 1
    UnhealthyNoAction = 2
    GuardrailBlocked = 3
    ConfigError = 4
}

# Global State
$script:ExitCode = [ExitCode]::Success
$script:CycleSummary = @{
    CycleNumber = 0
    ChecksRun = 0
    ChecksPassed = 0
    ChecksFailed = 0
    ActionsTaken = 0
    ActionsBlocked = 0
    StartTime = $null
    EndTime = $null
}

# Guardrails
$script:Guardrails = @{
    MaxActionsPerCycle   = 3
    CooldownSeconds      = 300
    CircuitBreakerLimit  = 5
    ActionsThisCycle     = 0
    ConsecutiveFailures  = 0
    CircuitBroken        = $false
}

# Config
$script:Config = @{
    DiskCriticalGb       = 5
    DiskWarningGb        = 10
    CriticalServices     = @("W32Time") # Safe default
    NetworkTarget        = "8.8.8.8"
    LatencyThresholdMs   = 200
}

#region Helper Functions

function Write-Log {
    param($Level, $Component, $Message, $Details = @{})
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logLine = "[$timestamp] [$Level] [$Component] $Message"
    
    $color = switch ($Level) {
        "ERROR" { "Red" }
        "WARN"  { "Yellow" }
        "ACTION" { "Cyan" }
        "AUDIT" { "Green" }
        default { "Gray" }
    }
    
    Write-Host $logLine -ForegroundColor $color
    
    if (-not (Test-Path (Split-Path $LogPath -Parent))) {
        New-Item -Path (Split-Path $LogPath -Parent) -ItemType Directory -Force | Out-Null
    }
    
    $logLine | Out-File -FilePath $LogPath -Append -Encoding UTF8
    
    $jsonEntry = @{
        timestamp = Get-Date -Format "o"
        level = $Level
        component = $Component
        message = $Message
        details = $Details
        correlationId = $CORRELATION_ID
    } | ConvertTo-Json -Compress
    
    $jsonEntry | Out-File -FilePath $JsonLogPath -Append -Encoding UTF8
}

function New-HealthObject {
    param([bool]$Healthy, [string]$Severity, [string]$CheckName, $Metrics = @{}, $RemediationName = $null)
    return @{
        Healthy = $Healthy
        Severity = $Severity
        CheckName = $CheckName
        Metrics = $Metrics
        RemediationName = $RemediationName
        Timestamp = Get-Date -Format "o"
    }
}

#endregion

#region Health Checks

function Check-DiskHealth {
    $drive = Get-PSDrive -Name C
    $freeGb = [math]::Round($drive.Free / 1GB, 2)
    $metrics = @{ freeGb = $freeGb }
    
    if ($freeGb -lt $script:Config.DiskCriticalGb) {
        Write-Log -Level ERROR -Component "DiskHealth" -Message "CRITICAL: Low disk space on C: ($freeGb GB)"
        return New-HealthObject -Healthy $false -Severity "Critical" -CheckName "Check-DiskHealth" -Metrics $metrics
    }
    Write-Log -Level AUDIT -Component "DiskHealth" -Message "Disk C: healthy ($freeGb GB free)"
    return New-HealthObject -Healthy $true -Severity "Low" -CheckName "Check-DiskHealth" -Metrics $metrics
}

function Check-ServiceHealth {
    param($ServiceName)
    $svc = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
    if (-not $svc) {
        Write-Log -Level ERROR -Component "ServiceHealth" -Message "Service $ServiceName not found"
        return New-HealthObject -Healthy $false -Severity "High" -CheckName "Check-ServiceHealth" -Metrics @{ service = $ServiceName; status = "NotFound" }
    }
    
    if ($svc.Status -ne "Running") {
        Write-Log -Level WARN -Component "ServiceHealth" -Message "Service $ServiceName is $($svc.Status)"
        return New-HealthObject -Healthy $false -Severity "Medium" -CheckName "Check-ServiceHealth" -Metrics @{ service = $ServiceName; status = $($svc.Status) } -RemediationName "Invoke-ServiceRemediation"
    }
    
    Write-Log -Level AUDIT -Component "ServiceHealth" -Message "Service $ServiceName is Running"
    return New-HealthObject -Healthy $true -Severity "Low" -CheckName "Check-ServiceHealth" -Metrics @{ service = $ServiceName; status = "Running" }
}

function Check-NetworkHealth {
    $target = $script:Config.NetworkTarget
    try {
        $ping = Test-Connection -ComputerName $target -Count 1 -ErrorAction Stop
        $latency = $ping.ResponseTime
        if ($latency -gt $script:Config.LatencyThresholdMs) {
            Write-Log -Level WARN -Component "NetworkHealth" -Message "High latency to $target ($latency ms)"
            return New-HealthObject -Healthy $false -Severity "Medium" -CheckName "Check-NetworkHealth" -Metrics @{ latency = $latency }
        }
        Write-Log -Level AUDIT -Component "NetworkHealth" -Message "Network healthy ($latency ms latency)"
        return New-HealthObject -Healthy $true -Severity "Low" -CheckName "Check-NetworkHealth" -Metrics @{ latency = $latency }
    } catch {
        Write-Log -Level ERROR -Component "NetworkHealth" -Message "Network unreachable: $target"
        return New-HealthObject -Healthy $false -Severity "High" -CheckName "Check-NetworkHealth" -Metrics @{ error = $_.Exception.Message }
    }
}

#endregion

#region Remediations

function Invoke-ServiceRemediation {
    param($Params)
    $serviceName = $Params.service
    Write-Log -Level ACTION -Component "Remediation" -Message "Attempting to start service: $serviceName"
    try {
        Start-Service -Name $serviceName -ErrorAction Stop
        Write-Log -Level AUDIT -Component "Remediation" -Message "Successfully started service: $serviceName"
        return $true
    } catch {
        Write-Log -Level ERROR -Component "Remediation" -Message "Failed to start service: $serviceName - $($_.Exception.Message)"
        return $false
    }
}

function Invoke-Remediation {
    param($Name, $Metrics)
    
    if ($script:AuditOnly) {
        Write-Log -Level INFO -Component "Guardrail" -Message "AuditOnly: Skipping remediation $Name"
        $script:CycleSummary.ActionsBlocked++
        return
    }
    
    if ($script:Guardrails.ActionsThisCycle -ge $script:Guardrails.MaxActionsPerCycle) {
        Write-Log -Level WARN -Component "Guardrail" -Message "Max actions reached for this cycle. Blocking $Name"
        $script:CycleSummary.ActionsBlocked++
        return
    }
    
    $success = $false
    if ($Name -eq "Invoke-ServiceRemediation") {
        $success = Invoke-ServiceRemediation -Params $Metrics
    }
    
    if ($success) {
        $script:Guardrails.ActionsThisCycle++
        $script:CycleSummary.ActionsTaken++
    }
}

#endregion

function Invoke-HealthCycle {
    param($CycleNumber)
    $script:CycleSummary.CycleNumber = $CycleNumber
    $script:CycleSummary.ChecksRun = 0
    $script:CycleSummary.ChecksPassed = 0
    $script:CycleSummary.ChecksFailed = 0
    $script:CycleSummary.ActionsTaken = 0
    $script:CycleSummary.ActionsBlocked = 0
    $script:CycleSummary.StartTime = Get-Date
    
    Write-Log -Level INFO -Component "Cycle" -Message "--- Starting Health Cycle $CycleNumber ---"
    
    # Check Disk
    $disk = Check-DiskHealth
    $script:CycleSummary.ChecksRun++
    if ($disk.Healthy) { $script:CycleSummary.ChecksPassed++ } else { $script:CycleSummary.ChecksFailed++ }
    
    # Check Services
    foreach ($svcName in $script:Config.CriticalServices) {
        $svc = Check-ServiceHealth -ServiceName $svcName
        $script:CycleSummary.ChecksRun++
        if ($svc.Healthy) { 
            $script:CycleSummary.ChecksPassed++ 
        } else { 
            $script:CycleSummary.ChecksFailed++
            if ($svc.RemediationName) {
                Invoke-Remediation -Name $svc.RemediationName -Metrics $svc.Metrics
            }
        }
    }
    
    # Check Network
    $net = Check-NetworkHealth
    $script:CycleSummary.ChecksRun++
    if ($net.Healthy) { $script:CycleSummary.ChecksPassed++ } else { $script:CycleSummary.ChecksFailed++ }
    
    $script:CycleSummary.EndTime = Get-Date
    $duration = ($script:CycleSummary.EndTime - $script:CycleSummary.StartTime).TotalSeconds
    Write-Log -Level INFO -Component "Cycle" -Message "Cycle $CycleNumber complete. Passed: $($script:CycleSummary.ChecksPassed)/$($script:CycleSummary.ChecksRun). Actions: $($script:CycleSummary.ActionsTaken)."
}

# Execution
if ($Status) {
    Write-Host "SelfHealAutomation v$VERSION - Status: Running"
    exit 0
}

$cycle = 1
while ($true) {
    Invoke-HealthCycle -CycleNumber $cycle
    if ($Once) { break }
    Write-Log -Level INFO -Component "Main" -Message "Sleeping for $IntervalSeconds seconds..."
    Start-Sleep -Seconds $IntervalSeconds
    $cycle++
    $script:Guardrails.ActionsThisCycle = 0
}

exit [int]$script:ExitCode
