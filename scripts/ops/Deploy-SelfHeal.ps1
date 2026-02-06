<#
.SYNOPSIS
    Deploy-SelfHeal.ps1 — Deployment Helper for SelfHealAutomation.ps1
.DESCRIPTION
    Deploys SelfHealAutomation.ps1 to target location with proper configuration.
#>

#Requires -Version 5.1

[CmdletBinding(SupportsShouldProcess)]
param(
    [Parameter()]
    [string]$TargetPath = "C:\SelfHeal",

    [Parameter()]
    [switch]$CreateScheduledTask,

    [Parameter()]
    [int]$TaskInterval = 5
)

$ErrorActionPreference = "Stop"

function Write-DeployLog {
    param($Message, $Level = "INFO")
    $color = switch ($Level) {
        "SUCCESS" { "Green" }
        "ERROR"   { "Red" }
        default   { "White" }
    }
    Write-Host "[DEPLOY] $Message" -ForegroundColor $color
}

# 1. Create target directory
if (-not (Test-Path $TargetPath)) {
    Write-DeployLog "Creating target directory: $TargetPath"
    New-Item -Path $TargetPath -ItemType Directory -Force | Out-Null
}

# 2. Copy SelfHealAutomation.ps1
$sourcePath = Join-Path $PSScriptRoot "SelfHealAutomation.ps1"
$destPath = Join-Path $TargetPath "SelfHealAutomation.ps1"

if (Test-Path $sourcePath) {
    Write-DeployLog "Copying SelfHealAutomation.ps1 to $TargetPath"
    Copy-Item -Path $sourcePath -Destination $destPath -Force
} else {
    Write-DeployLog "Source script not found at $sourcePath" -Level "ERROR"
    exit 1
}

# 3. Create data directories
$dataDirs = @(
    "$env:ProgramData\SelfHeal\logs",
    "$env:ProgramData\SelfHeal\evidence"
)
foreach ($dir in $dataDirs) {
    if (-not (Test-Path $dir)) {
        Write-DeployLog "Creating data directory: $dir"
        New-Item -Path $dir -ItemType Directory -Force | Out-Null
    }
}

# 4. Create scheduled task if requested
if ($CreateScheduledTask) {
    Write-DeployLog "Setting up Scheduled Task..."
    $taskName = "SelfHealAutomation"
    $scriptPath = $destPath
    
    $arguments = "-NoProfile -ExecutionPolicy Bypass -File `"$scriptPath`" -Once"
    
    # Remove existing task
    if (Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue) {
        Write-DeployLog "Removing existing task: $taskName"
        Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
    }
    
    $trigger = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Minutes $TaskInterval)
    $action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument $arguments
    $principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount -RunLevel Highest
    $settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable
    
    Register-ScheduledTask -TaskName $taskName -Trigger $trigger -Action $action -Principal $principal -Settings $settings -Description "Sovereign Self-Heal Automation"
    Write-DeployLog "Scheduled task '$taskName' created successfully (Interval: $TaskInterval mins)" -Level "SUCCESS"
}

Write-DeployLog "Deployment complete." -Level "SUCCESS"
