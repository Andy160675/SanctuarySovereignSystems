# =============================================================================
# Sovereign System - Atomic Boot Script (Windows PowerShell)
# =============================================================================
# This script provides deterministic system startup with:
# - PID management for process tracking
# - Autobuild gate checking
# - Health verification
# - Evidence logging
#
# Usage: .\start.ps1 [-Force] [-Dev] [-ValidateOnly] [-Stop] [-Status]
# =============================================================================

[CmdletBinding()]
param(
    [switch]$Force,
    [switch]$Dev,
    [switch]$ValidateOnly,
    [switch]$Stop,
    [switch]$Status
)

$ErrorActionPreference = "Stop"

# Configuration
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

$PidFile = Join-Path $ScriptDir ".sovereign.pid"
$LockFile = Join-Path $ScriptDir ".sovereign.lock"
$LogDir = Join-Path $ScriptDir "logs"
$ComposeFile = "compose/docker-compose.mission.yml"
$AutobuildConfig = "config/autobuild.json"

# =============================================================================
# Utility Functions
# =============================================================================

function Write-LogInfo {
    param([string]$Message)
    $timestamp = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
    Write-Host "[INFO] $timestamp $Message" -ForegroundColor Blue
}

function Write-LogSuccess {
    param([string]$Message)
    $timestamp = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
    Write-Host "[OK] $timestamp $Message" -ForegroundColor Green
}

function Write-LogWarn {
    param([string]$Message)
    $timestamp = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
    Write-Host "[WARN] $timestamp $Message" -ForegroundColor Yellow
}

function Write-LogError {
    param([string]$Message)
    $timestamp = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
    Write-Host "[ERROR] $timestamp $Message" -ForegroundColor Red
}

# =============================================================================
# Lock Management
# =============================================================================

function Test-Lock {
    if (Test-Path $LockFile) {
        $lockContent = Get-Content $LockFile -ErrorAction SilentlyContinue
        if ($lockContent) {
            $lockPid = [int]$lockContent
            try {
                $process = Get-Process -Id $lockPid -ErrorAction Stop
                Write-LogError "Another instance is running (PID: $lockPid)"
                exit 1
            }
            catch {
                Write-LogWarn "Stale lock file found, removing..."
                Remove-Item $LockFile -Force
            }
        }
    }
    $PID | Out-File $LockFile -Force
}

function Remove-Lock {
    if (Test-Path $LockFile) {
        Remove-Item $LockFile -Force
    }
}

# =============================================================================
# PID Management
# =============================================================================

function Write-PidFile {
    $bootTime = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
    $phase = 0
    if (Test-Path "governance/ACTIVE_PHASE") {
        $phase = [int](Get-Content "governance/ACTIVE_PHASE")
    }

    $pidData = @{
        boot_pid = $PID
        boot_time_utc = $bootTime
        compose_file = $ComposeFile
        status = "running"
        phase = $phase
    }

    $pidData | ConvertTo-Json | Out-File $PidFile -Force
    Write-LogInfo "PID file written: $PID"
}

function Clear-PidFile {
    if (Test-Path $PidFile) {
        $stopTime = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
        try {
            $data = Get-Content $PidFile | ConvertFrom-Json
            $data.status = "stopped"
            $data | Add-Member -NotePropertyName "stop_time_utc" -NotePropertyValue $stopTime -Force
            $data | ConvertTo-Json | Out-File $PidFile -Force
        }
        catch {
            Remove-Item $PidFile -Force
        }
    }
}

# =============================================================================
# Autobuild Gate Check
# =============================================================================

function Test-AutobuildGate {
    if (Test-Path $AutobuildConfig) {
        try {
            $config = Get-Content $AutobuildConfig | ConvertFrom-Json
            if ($config.enabled -eq $true) {
                Write-LogSuccess "Autobuild gate: ENABLED"
                return $true
            }
            else {
                Write-LogWarn "Autobuild gate: DISABLED"
                return $false
            }
        }
        catch {
            Write-LogWarn "Failed to read autobuild config"
            return $true
        }
    }
    else {
        Write-LogWarn "Autobuild config not found, proceeding with manual mode"
        return $true
    }
}

# =============================================================================
# Governance Validation
# =============================================================================

function Test-Governance {
    Write-LogInfo "Validating governance configuration..."

    # Check ACTIVE_PHASE exists
    if (-not (Test-Path "governance/ACTIVE_PHASE")) {
        Write-LogError "governance/ACTIVE_PHASE not found"
        return $false
    }

    $phase = [int](Get-Content "governance/ACTIVE_PHASE")
    Write-LogInfo "Active Phase: $phase"

    # Validate phase definition exists
    $phaseFile = "governance/phases/phase$phase.yaml"
    if (-not (Test-Path $phaseFile)) {
        Write-LogError "Phase definition not found: $phaseFile"
        return $false
    }

    # Run governance validation if script exists
    if (Test-Path "scripts/validate_governance_config.py") {
        try {
            $result = python scripts/validate_governance_config.py 2>&1
            if ($LASTEXITCODE -eq 0) {
                Write-LogSuccess "Governance config valid"
            }
            else {
                Write-LogError "Governance validation failed"
                return $false
            }
        }
        catch {
            Write-LogWarn "Could not run governance validation"
        }
    }

    # Run phase validation
    if (Test-Path "scripts/validate_phase.py") {
        try {
            python scripts/validate_phase.py $phaseFile 2>&1 | Out-Null
            if ($LASTEXITCODE -eq 0) {
                Write-LogSuccess "Phase validation passed"
            }
            else {
                Write-LogWarn "Phase validation had warnings"
            }
        }
        catch {
            Write-LogWarn "Could not run phase validation"
        }
    }

    return $true
}

# =============================================================================
# Docker Compose Operations
# =============================================================================

function Start-Services {
    Write-LogInfo "Starting Sovereign System services..."

    if (-not (Test-Path $ComposeFile)) {
        Write-LogError "Compose file not found: $ComposeFile"
        return $false
    }

    try {
        docker compose -f $ComposeFile up -d --build
        if ($LASTEXITCODE -eq 0) {
            Write-LogSuccess "Services started successfully"
            return $true
        }
        else {
            Write-LogError "Failed to start services"
            return $false
        }
    }
    catch {
        Write-LogError "Docker compose failed: $_"
        return $false
    }
}

function Test-Health {
    Write-LogInfo "Checking service health..."

    $maxAttempts = 30
    $requiredServices = @("policy_gate", "ledger_service", "command-center")

    for ($attempt = 1; $attempt -le $maxAttempts; $attempt++) {
        $healthyCount = 0

        foreach ($service in $requiredServices) {
            $status = docker compose -f $ComposeFile ps --format json 2>$null | ConvertFrom-Json
            $svc = $status | Where-Object { $_.Name -like "*$service*" }
            if ($svc -and $svc.Health -eq "healthy") {
                $healthyCount++
            }
        }

        if ($healthyCount -eq $requiredServices.Count) {
            Write-LogSuccess "All core services healthy"
            return $true
        }

        Write-LogInfo "Waiting for services... ($attempt/$maxAttempts)"
        Start-Sleep -Seconds 2
    }

    Write-LogWarn "Not all services reached healthy state"
    docker compose -f $ComposeFile ps
    return $false
}

function Stop-Services {
    Write-LogInfo "Stopping Sovereign System services..."
    docker compose -f $ComposeFile down
    Clear-PidFile
    Write-LogSuccess "Services stopped"
}

function Get-ServiceStatus {
    docker compose -f $ComposeFile ps
}

# =============================================================================
# Evidence Logging
# =============================================================================

function Write-BootEvidence {
    param([string]$Mode = "manual")

    if (-not (Test-Path $LogDir)) {
        New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
    }

    $bootLog = Join-Path $LogDir "boot_evidence.jsonl"
    $phase = 0
    if (Test-Path "governance/ACTIVE_PHASE") {
        $phase = [int](Get-Content "governance/ACTIVE_PHASE")
    }

    $entry = @{
        timestamp_utc = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
        event = "boot"
        pid = $PID
        phase = $phase
        mode = $Mode
    }

    $entry | ConvertTo-Json -Compress | Add-Content $bootLog
    Write-LogInfo "Boot evidence logged"
}

# =============================================================================
# Main Entry Point
# =============================================================================

try {
    Write-Host ""
    Write-Host "+=================================================================+"
    Write-Host "|           SOVEREIGN SYSTEM - ATOMIC BOOT                        |"
    Write-Host "+=================================================================+"
    Write-Host ""

    # Handle --status
    if ($Status) {
        Get-ServiceStatus
        exit 0
    }

    # Handle --stop
    if ($Stop) {
        Stop-Services
        exit 0
    }

    # Acquire lock
    Test-Lock

    # Validate governance
    if (-not (Test-Governance)) {
        Write-LogError "Governance validation failed. Boot aborted."
        exit 1
    }

    if ($ValidateOnly) {
        Write-LogSuccess "Validation complete. Exiting (-ValidateOnly mode)."
        exit 0
    }

    # Check autobuild gate (skip if -Force)
    if (-not $Force) {
        if (-not (Test-AutobuildGate)) {
            Write-LogWarn "Autobuild disabled. Use -Force to override or enable via passcode."
            exit 0
        }
    }
    else {
        Write-LogWarn "Force mode: skipping autobuild gate"
    }

    # Write PID
    Write-PidFile

    # Log evidence
    $mode = if ($Dev) { "dev" } else { "manual" }
    Write-BootEvidence -Mode $mode

    # Start services
    if (-not (Start-Services)) {
        Clear-PidFile
        exit 1
    }

    # Health check
    Test-Health | Out-Null

    Write-Host ""
    Write-LogSuccess "Sovereign System boot complete"
    Write-Host ""
    Write-Host "  Dashboard: http://localhost:8100"
    Write-Host "  Phase Status API: http://localhost:8097"
    Write-Host "  Runtime Interface: http://localhost:8096"
    Write-Host ""
}
finally {
    Remove-Lock
}
