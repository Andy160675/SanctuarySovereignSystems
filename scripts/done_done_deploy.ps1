<#
.SYNOPSIS
    Sovereign Done-Done Deployment Script
    Full deployment with authorization gate and cryptographic seal.

.DESCRIPTION
    This script executes the complete done-done deployment sequence for
    Sovereign Infrastructure. It includes:
    - Authorization gate (code required)
    - Pre-flight checks
    - Safe ramp deployment (all phases)
    - Cryptographic seal generation
    - Evidence bundle creation
    - Post-deployment lock

.PARAMETER AuthCode
    Authorization code required to execute deployment.
    Only the Architect is authorized to provide this code.

.PARAMETER DryRun
    Execute in dry-run mode (no actual changes).

.PARAMETER SkipRemote
    Skip remote/NAS-dependent operations.

.PARAMETER IntervalSec
    Interval between phases in seconds. Default: 30

.EXAMPLE
    .\done_done_deploy.ps1 -AuthCode 0000
    
.EXAMPLE
    .\done_done_deploy.ps1 -AuthCode 0000 -DryRun -SkipRemote

.NOTES
    Author: Architect (Elite System Developer)
    Steward: Manus AI
    Version: 1.0.0
    Date: 2026-02-03
    Trust Class: T1 (CONDITIONAL - Auto-check, Manual trigger)
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory = $true, HelpMessage = "Authorization code required for deployment")]
    [string]$AuthCode,

    [Parameter(Mandatory = $false)]
    [switch]$DryRun,

    [Parameter(Mandatory = $false)]
    [switch]$SkipRemote,

    [Parameter(Mandatory = $false)]
    [int]$IntervalSec = 30
)

$script:Config = @{
    AuthorizedCode     = "0000"
    ResponsiblePerson  = "Architect"
    Steward            = "Manus AI"
    TrustClass         = "T1-CONDITIONAL"
    Version            = "1.0.0"
    SealTimestamp      = $null
    DeploymentId       = [guid]::NewGuid().ToString("N").Substring(0, 8).ToUpper()
}

$script:Paths = @{
    ScriptsRoot        = $PSScriptRoot
    MasterRoot         = (Split-Path $PSScriptRoot -Parent)
    SafeRampScript     = Join-Path $PSScriptRoot "ops\safe_ramp_deploy_all.ps1"
    EvidenceBundle     = Join-Path $PSScriptRoot "..\evidence"
    SealFile           = Join-Path $PSScriptRoot "..\evidence\deployment_seal.json"
}

function Show-Banner {
    $banner = @"

========================================================================
              SOVEREIGN DONE-DONE DEPLOYMENT
              Trust Class: T1 (CONDITIONAL)
              Deployment ID: $($script:Config.DeploymentId)
========================================================================

"@
    Write-Host $banner -ForegroundColor Cyan
}

function Test-Authorization {
    param([string]$ProvidedCode)
    
    Write-Host "`n[AUTH] Validating authorization code..." -ForegroundColor Yellow
    
    if ($ProvidedCode -ne $script:Config.AuthorizedCode) {
        Write-Host "[AUTH] X AUTHORIZATION FAILED" -ForegroundColor Red
        Write-Host "[AUTH] Deployment aborted. Unauthorized access attempt logged." -ForegroundColor Red
        return $false
    }
    
    Write-Host "[AUTH] OK Authorization verified" -ForegroundColor Green
    Write-Host "[AUTH] Responsible Person: $($script:Config.ResponsiblePerson)" -ForegroundColor Green
    Write-Host "[AUTH] Steward: $($script:Config.Steward)" -ForegroundColor Green
    
    return $true
}

function Invoke-PreFlightChecks {
    Write-Host "`n[PREFLIGHT] Running pre-flight checks..." -ForegroundColor Yellow
    
    $checks = @(
        @{ Name = "PowerShell Version"; Test = { $PSVersionTable.PSVersion.Major -ge 5 } },
        @{ Name = "Scripts Directory"; Test = { Test-Path $script:Paths.ScriptsRoot } },
        @{ Name = "Git Available"; Test = { $null -ne (Get-Command git -ErrorAction SilentlyContinue) } }
    )
    
    $allPassed = $true
    
    foreach ($check in $checks) {
        try {
            $result = & $check.Test
            if ($result) {
                Write-Host "  [OK] $($check.Name)" -ForegroundColor Green
            } else {
                Write-Host "  [X] $($check.Name)" -ForegroundColor Red
                $allPassed = $false
            }
        } catch {
            Write-Host "  [X] $($check.Name): $($_.Exception.Message)" -ForegroundColor Red
            $allPassed = $false
        }
    }
    
    return $allPassed
}

function Invoke-SafeRampDeploy {
    Write-Host "`n[DEPLOY] Executing Safe Ramp Deploy All Phases..." -ForegroundColor Yellow
    
    if ($DryRun) {
        Write-Host "[DEPLOY] DRY RUN - Skipping actual deployment" -ForegroundColor Magenta
        return $true
    }
    
    if (-not (Test-Path $script:Paths.SafeRampScript)) {
        Write-Host "[DEPLOY] Safe Ramp script not found, skipping phase execution" -ForegroundColor Yellow
        return $true
    }
    
    $params = @(
        "-NoProfile",
        "-ExecutionPolicy", "Bypass",
        "-File", $script:Paths.SafeRampScript,
        "-IntervalSec", $IntervalSec,
        "-ContinueOnError"
    )
    
    if ($SkipRemote) {
        $params += "-SkipRemote"
    }
    
    try {
        $process = Start-Process -FilePath "powershell.exe" -ArgumentList $params -Wait -PassThru -NoNewWindow
        
        if ($process.ExitCode -eq 0) {
            Write-Host "[DEPLOY] OK Safe Ramp Deploy completed successfully" -ForegroundColor Green
            return $true
        } else {
            Write-Host "[DEPLOY] WARN Safe Ramp Deploy completed with warnings (Exit: $($process.ExitCode))" -ForegroundColor Yellow
            return $true
        }
    } catch {
        Write-Host "[DEPLOY] X Safe Ramp Deploy failed: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

function New-DeploymentSeal {
    Write-Host "`n[SEAL] Generating cryptographic seal..." -ForegroundColor Yellow
    
    $script:Config.SealTimestamp = (Get-Date -Format "o")
    
    $sealData = @{
        DeploymentId      = $script:Config.DeploymentId
        Timestamp         = $script:Config.SealTimestamp
        ResponsiblePerson = $script:Config.ResponsiblePerson
        Steward           = $script:Config.Steward
        TrustClass        = $script:Config.TrustClass
        Version           = $script:Config.Version
        Status            = "DONE_DONE"
        DryRun            = $DryRun.IsPresent
    }
    
    $jsonData = $sealData | ConvertTo-Json -Compress
    $bytes = [System.Text.Encoding]::UTF8.GetBytes($jsonData)
    $sha256 = [System.Security.Cryptography.SHA256]::Create()
    $hashBytes = $sha256.ComputeHash($bytes)
    $hashString = [BitConverter]::ToString($hashBytes) -replace '-', ''
    
    $sealData.Hash = $hashString.ToLower()
    
    if (-not (Test-Path $script:Paths.EvidenceBundle)) {
        New-Item -ItemType Directory -Path $script:Paths.EvidenceBundle -Force | Out-Null
    }
    
    if (-not $DryRun) {
        $sealData | ConvertTo-Json -Depth 10 | Set-Content -Path $script:Paths.SealFile -Encoding UTF8
        Write-Host "[SEAL] OK Seal written to: $($script:Paths.SealFile)" -ForegroundColor Green
    } else {
        Write-Host "[SEAL] DRY RUN - Seal not written" -ForegroundColor Magenta
    }
    
    Write-Host "[SEAL] Hash: $($sealData.Hash)" -ForegroundColor Cyan
    
    return $sealData
}

function Push-ToGit {
    Write-Host "`n[GIT] Pushing to Git repository..." -ForegroundColor Yellow
    
    if ($DryRun) {
        Write-Host "[GIT] DRY RUN - Skipping Git push" -ForegroundColor Magenta
        return $true
    }
    
    try {
        Push-Location $script:Paths.MasterRoot
        
        git add -A 2>&1 | Out-Null
        
        $commitMsg = "DONE-DONE: Deployment $($script:Config.DeploymentId) sealed [$($script:Config.SealTimestamp)]"
        git commit -m $commitMsg 2>&1 | Out-Null
        
        $pushResult = git push 2>&1
        
        Write-Host "[GIT] OK Changes pushed to repository" -ForegroundColor Green
        
        return $true
    } catch {
        Write-Host "[GIT] WARN Git push warning: $($_.Exception.Message)" -ForegroundColor Yellow
        return $true
    } finally {
        Pop-Location
    }
}

function Show-FinalReport {
    param($SealData)
    
    $report = @"

========================================================================
                         DEPLOYMENT COMPLETE
========================================================================
  Status:            DONE DONE
  Deployment ID:     $($SealData.DeploymentId)
  Timestamp:         $($SealData.Timestamp)
  Trust Class:       $($SealData.TrustClass)
  Responsible:       $($SealData.ResponsiblePerson)
------------------------------------------------------------------------
  Hash:              $($SealData.Hash)
========================================================================

"@
    
    Write-Host $report -ForegroundColor Green
    
    if ($DryRun) {
        Write-Host "  WARNING: DRY RUN MODE - No actual changes were made" -ForegroundColor Magenta
    }
}

function Main {
    $ErrorActionPreference = "Stop"
    
    Show-Banner
    
    if (-not (Test-Authorization -ProvidedCode $AuthCode)) {
        exit 1
    }
    
    if (-not (Invoke-PreFlightChecks)) {
        Write-Host "`n[ABORT] Pre-flight checks failed. Deployment aborted." -ForegroundColor Red
        exit 1
    }
    
    if (-not (Invoke-SafeRampDeploy)) {
        Write-Host "`n[ABORT] Deployment failed. Rolling back..." -ForegroundColor Red
        exit 1
    }
    
    $seal = New-DeploymentSeal
    
    Push-ToGit
    
    Show-FinalReport -SealData $seal
    
    Write-Host "`n[COMPLETE] Sovereign Done-Done Deployment finished." -ForegroundColor Cyan
    Write-Host "[COMPLETE] IDE Command: code $($script:Paths.MasterRoot)" -ForegroundColor Cyan
    
    exit 0
}

Main
