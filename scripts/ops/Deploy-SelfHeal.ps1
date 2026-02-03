<#
.SYNOPSIS
    Deploy-SelfHeal.ps1 — Deployment Helper for SelfHealAutomation.ps1

.DESCRIPTION
    Deploys SelfHealAutomation.ps1 to target location with proper configuration.

.PARAMETER TargetPath
    Deployment target directory (default: C:\SelfHeal)

.PARAMETER ConfigPath
    Path to configuration file to deploy

.PARAMETER CreateScheduledTask
    Create a Windows Scheduled Task for continuous operation

.PARAMETER TaskInterval
    Interval in minutes for scheduled task (default: 5)

.PARAMETER Uninstall
    Remove SelfHealAutomation from target

.EXAMPLE
    .\Deploy-SelfHeal.ps1 -CreateScheduledTask

.EXAMPLE
    .\Deploy-SelfHeal.ps1 -Uninstall
#>

#Requires -Version 5.1
#Requires -RunAsAdministrator

[CmdletBinding(SupportsShouldProcess)]
param(
    [Parameter()]
    [string]$TargetPath = "C:\SelfHeal",

    [Parameter()]
    [string]$ConfigPath,

    [Parameter()]
    [switch]$CreateScheduledTask,

    [Parameter()]
    [ValidateRange(1, 60)]
    [int]$TaskInterval = 5,

    [Parameter()]
    [switch]$Uninstall
)

$ErrorActionPreference = "Stop"

#region ============================================================================
#region FUNCTIONS
#region ============================================================================

function Write-DeployLog {
    param(
        [string]$Message,
        [string]$Level = "INFO"
    )
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $color = switch ($Level) {
        "INFO"    { "White" }
        "SUCCESS" { "Green" }
        "WARN"    { "Yellow" }
        "ERROR"   { "Red" }
    }
    Write-Host "[$timestamp] [$Level] $Message" -ForegroundColor $color
}

function Install-SelfHeal {
    Write-Host ""
    Write-Host "╔══════════════════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "║  DEPLOYING SELFHEALAUTOMATION                                                ║" -ForegroundColor Cyan
    Write-Host "╚══════════════════════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
    Write-Host ""

    # Create target directory
    if (-not (Test-Path $TargetPath)) {
        Write-DeployLog "Creating target directory: $TargetPath"
        New-Item -Path $TargetPath -ItemType Directory -Force | Out-Null
    }

    # Copy files
    $sourceDir = $PSScriptRoot
    $filesToCopy = @(
        "SelfHealAutomation.ps1",
        "SelfHealConfig.schema.json",
        "SelfHealConfig.example.json",
        "Test-SelfHeal.ps1"
    )

    foreach ($file in $filesToCopy) {
        $sourcePath = Join-Path $sourceDir $file
        $destPath = Join-Path $TargetPath $file
        
        if (Test-Path $sourcePath) {
            Write-DeployLog "Copying: $file"
            Copy-Item -Path $sourcePath -Destination $destPath -Force
        } else {
            Write-DeployLog "Source file not found: $file" -Level "WARN"
        }
    }

    # Copy config if specified
    if ($ConfigPath -and (Test-Path $ConfigPath)) {
        $configDest = Join-Path $TargetPath "SelfHealConfig.json"
        Write-DeployLog "Copying configuration: $ConfigPath"
        Copy-Item -Path $ConfigPath -Destination $configDest -Force
    }

    # Create data directories
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

    Write-DeployLog "Deployment complete" -Level "SUCCESS"

    # Create scheduled task if requested
    if ($CreateScheduledTask) {
        Install-ScheduledTask
    }
}

function Install-ScheduledTask {
    Write-Host ""
    Write-DeployLog "Creating scheduled task..."

    $taskName = "SelfHealAutomation"
    $scriptPath = Join-Path $TargetPath "SelfHealAutomation.ps1"
    $configPath = Join-Path $TargetPath "SelfHealConfig.json"

    # Build arguments
    $arguments = "-NoProfile -ExecutionPolicy Bypass -File `"$scriptPath`" -Once"
    if (Test-Path $configPath) {
        $arguments += " -ConfigPath `"$configPath`""
    }

    # Remove existing task
    $existingTask = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
    if ($existingTask) {
        Write-DeployLog "Removing existing scheduled task"
        Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
    }

    # Create trigger
    $trigger = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Minutes $TaskInterval)

    # Create action
    $action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument $arguments

    # Create principal (run as SYSTEM)
    $principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount -RunLevel Highest

    # Create settings
    $settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1)

    # Register task
    Register-ScheduledTask -TaskName $taskName -Trigger $trigger -Action $action -Principal $principal -Settings $settings -Description "SelfHealAutomation — The Blade of Truth"

    Write-DeployLog "Scheduled task created: $taskName (every $TaskInterval minutes)" -Level "SUCCESS"
}

function Uninstall-SelfHeal {
    Write-Host ""
    Write-Host "╔══════════════════════════════════════════════════════════════════════════════╗" -ForegroundColor Yellow
    Write-Host "║  UNINSTALLING SELFHEALAUTOMATION                                             ║" -ForegroundColor Yellow
    Write-Host "╚══════════════════════════════════════════════════════════════════════════════╝" -ForegroundColor Yellow
    Write-Host ""

    # Remove scheduled task
    $taskName = "SelfHealAutomation"
    $existingTask = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
    if ($existingTask) {
        Write-DeployLog "Removing scheduled task: $taskName"
        Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
    }

    # Remove installation directory
    if (Test-Path $TargetPath) {
        Write-DeployLog "Removing installation directory: $TargetPath"
        Remove-Item -Path $TargetPath -Recurse -Force
    }

    # Optionally remove data (prompt user)
    $dataPath = "$env:ProgramData\SelfHeal"
    if (Test-Path $dataPath) {
        $confirm = Read-Host "Remove data directory ($dataPath)? [y/N]"
        if ($confirm -eq "y" -or $confirm -eq "Y") {
            Write-DeployLog "Removing data directory: $dataPath"
            Remove-Item -Path $dataPath -Recurse -Force
        } else {
            Write-DeployLog "Data directory preserved: $dataPath" -Level "WARN"
        }
    }

    Write-DeployLog "Uninstall complete" -Level "SUCCESS"
}

#endregion

#region ============================================================================
#region MAIN
#region ============================================================================

if ($Uninstall) {
    Uninstall-SelfHeal
} else {
    Install-SelfHeal
}

#endregion
