# =============================================================================
# RUN-FieldSandbox.ps1
# Sovereign Away Kit - Field SSD Quick Launcher
# =============================================================================
#
# PURPOSE: One-command launch for field deployments from portable SSD
# LOCATION: G:\RUN-FieldSandbox.ps1 (SOV_FIELD drive)
#
# Usage:
#   .\RUN-FieldSandbox.ps1                  # Standard run
#   .\RUN-FieldSandbox.ps1 -KeepRunning     # Don't cleanup after smoke test
#   .\RUN-FieldSandbox.ps1 -SkipSmoke       # Just start services, no test
#
# =============================================================================

param(
    [switch]$KeepRunning,
    [switch]$SkipSmoke,
    [string]$SourcePath = ""
)

$ErrorActionPreference = "Stop"

# Auto-detect source path
if (-not $SourcePath) {
    $scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

    # Check common locations
    $candidates = @(
        "$scriptDir\sovereign-system",
        "$scriptDir",
        "C:\sovereign-system",
        "G:\sovereign-system",
        "E:\SOVEREIGN-SANDBOX"
    )

    foreach ($c in $candidates) {
        if (Test-Path "$c\mock_services.py") {
            $SourcePath = $c
            break
        }
    }

    if (-not $SourcePath) {
        Write-Host "[ERROR] Could not find sovereign-system. Specify -SourcePath" -ForegroundColor Red
        exit 1
    }
}

Write-Host ""
Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host "  SOVEREIGN FIELD SANDBOX - AWAY KIT v1" -ForegroundColor Cyan
Write-Host "  Portable Deployment Quick Start" -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host ""

Write-Host "[CONFIG] Source path: $SourcePath" -ForegroundColor Gray
Write-Host "[CONFIG] Keep running: $KeepRunning" -ForegroundColor Gray
Write-Host "[CONFIG] Skip smoke: $SkipSmoke" -ForegroundColor Gray
Write-Host ""

$procs = @()

function Wait-Healthy {
    param(
        [string]$Url,
        [string]$Name,
        [int]$TimeoutSec = 30
    )

    Write-Host "  Waiting for $Name ... " -NoNewline
    $sw = [Diagnostics.Stopwatch]::StartNew()
    while ($sw.Elapsed.TotalSeconds -lt $TimeoutSec) {
        try {
            $r = Invoke-WebRequest -Uri $Url -Method Get -UseBasicParsing -TimeoutSec 2 -ErrorAction SilentlyContinue
            if ($r.StatusCode -eq 200) {
                Write-Host "OK" -ForegroundColor Green
                return $true
            }
        } catch {
            Start-Sleep -Milliseconds 500
        }
    }
    Write-Host "TIMEOUT" -ForegroundColor Red
    return $false
}

function Cleanup {
    if (-not $KeepRunning) {
        Write-Host "`n[CLEANUP] Stopping services..." -ForegroundColor Yellow
        foreach ($p in $script:procs) {
            if ($p -and -not $p.HasExited) {
                Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue
            }
        }
    }
}

try {
    # ==========================================================================
    # Step 1: Verify prerequisites
    # ==========================================================================
    Write-Host "[STEP 1] Verifying prerequisites..." -ForegroundColor Cyan

    $mockScript = "$SourcePath\mock_services.py"
    if (-not (Test-Path $mockScript)) {
        Write-Host "[ERROR] mock_services.py not found at: $mockScript" -ForegroundColor Red
        exit 1
    }
    Write-Host "  [OK] mock_services.py found" -ForegroundColor Green

    # Check Python
    $pyCheck = python -c "import fastapi, uvicorn, httpx; print('OK')" 2>&1
    if ($pyCheck -ne "OK") {
        Write-Host "[WARN] Python dependencies may be missing. Attempting install..." -ForegroundColor Yellow
        pip install fastapi uvicorn httpx pydantic --quiet
    } else {
        Write-Host "  [OK] Python dependencies verified" -ForegroundColor Green
    }

    # ==========================================================================
    # Step 2: Start Mock Services
    # ==========================================================================
    Write-Host ""
    Write-Host "[STEP 2] Starting mock services (ports 8001-8005, 8502)..." -ForegroundColor Cyan

    $mockProc = Start-Process python -PassThru -WindowStyle Minimized -ArgumentList @(
        $mockScript
    ) -WorkingDirectory $SourcePath
    $script:procs += $mockProc
    Write-Host "  [OK] Mock services started (PID: $($mockProc.Id))" -ForegroundColor Green

    Start-Sleep -Seconds 3

    # ==========================================================================
    # Step 3: Start Trinity Backend (if available)
    # ==========================================================================
    $trinityScript = "$SourcePath\trinity\trinity_backend.py"
    $trinityProc = $null

    if (Test-Path $trinityScript) {
        Write-Host ""
        Write-Host "[STEP 3] Starting Trinity backend (port 8600)..." -ForegroundColor Cyan

        $trinityProc = Start-Process python -PassThru -WindowStyle Minimized -ArgumentList @(
            $trinityScript
        ) -WorkingDirectory $SourcePath
        $script:procs += $trinityProc
        Write-Host "  [OK] Trinity backend started (PID: $($trinityProc.Id))" -ForegroundColor Green

        Start-Sleep -Seconds 3
    } else {
        Write-Host ""
        Write-Host "[STEP 3] Trinity backend not found (skipping)" -ForegroundColor DarkYellow
    }

    # ==========================================================================
    # Step 4: Health Checks
    # ==========================================================================
    Write-Host ""
    Write-Host "[STEP 4] Health checks..." -ForegroundColor Cyan

    $okAggregated = Wait-Healthy "http://localhost:8502/health" "Aggregated Backend (8502)"

    $okTrinity = $true
    if ($trinityProc) {
        $okTrinity = Wait-Healthy "http://localhost:8600/health" "Trinity Backend (8600)"
    }

    if (-not $okAggregated) {
        Write-Host "[ERROR] Core services failed to start" -ForegroundColor Red
        Cleanup
        exit 1
    }

    # ==========================================================================
    # Step 5: Smoke Test (unless skipped)
    # ==========================================================================
    if (-not $SkipSmoke) {
        Write-Host ""
        Write-Host "[STEP 5] Running smoke test..." -ForegroundColor Cyan

        if ($trinityProc -and $okTrinity) {
            # Full Trinity smoke test
            $body = @{
                case_id = "CASE-FIELD-001"
                query   = "evidence"
            } | ConvertTo-Json

            try {
                $resp = Invoke-RestMethod `
                    -Uri "http://localhost:8600/api/trinity/run_case" `
                    -Method POST `
                    -Body $body `
                    -ContentType "application/json"

                Write-Host "  [OK] Trinity run_case completed" -ForegroundColor Green
                Write-Host "       Run ID: $($resp.run_id)" -ForegroundColor Gray
                Write-Host "       Evidence: $($resp.summary.evidence_found)" -ForegroundColor Gray
                Write-Host "       Integrity: $($resp.summary.integrity_status)" -ForegroundColor Gray
            } catch {
                Write-Host "  [WARN] Trinity smoke test failed: $_" -ForegroundColor Yellow
            }
        } else {
            # Basic health smoke
            try {
                $health = Invoke-RestMethod -Uri "http://localhost:8502/health"
                Write-Host "  [OK] Health check passed" -ForegroundColor Green
                Write-Host "       Status: $($health.overall_status)" -ForegroundColor Gray
                Write-Host "       Services: $($health.services.Count)" -ForegroundColor Gray
            } catch {
                Write-Host "  [WARN] Health smoke test failed" -ForegroundColor Yellow
            }
        }

        # Evidence verification
        Write-Host ""
        Write-Host "[STEP 5b] Verifying evidence store..." -ForegroundColor Cyan
        try {
            $evidenceInfo = Invoke-RestMethod -Uri "http://localhost:8502/api/evidence/info"
            Write-Host "  [OK] Evidence store accessible" -ForegroundColor Green
            Write-Host "       Case: $($evidenceInfo.case_id)" -ForegroundColor Gray
            Write-Host "       Tampered: $($evidenceInfo.tampered)" -ForegroundColor Gray
        } catch {
            Write-Host "  [WARN] Evidence info unavailable" -ForegroundColor Yellow
        }
    }

    # ==========================================================================
    # Step 6: SVC Log (if available)
    # ==========================================================================
    $svcScript = "$SourcePath\sov_vc\sov.py"
    if (Test-Path $svcScript) {
        Write-Host ""
        Write-Host "[SVC] Sovereign Version Control history:" -ForegroundColor Magenta
        try {
            python $svcScript log
        } catch {
            Write-Host "  [WARN] SVC log unavailable" -ForegroundColor Yellow
        }
    }

    # ==========================================================================
    # Summary
    # ==========================================================================
    Write-Host ""
    Write-Host "=" * 60 -ForegroundColor Green
    Write-Host "  FIELD SANDBOX READY" -ForegroundColor Green
    Write-Host "=" * 60 -ForegroundColor Green
    Write-Host ""
    Write-Host "  Endpoints:" -ForegroundColor Cyan
    Write-Host "    Health:        http://localhost:8502/health"
    Write-Host "    Evidence:      http://localhost:8502/api/evidence/info"
    Write-Host "    Verify Hash:   http://localhost:8502/api/core/verify_hash"
    if ($trinityProc) {
        Write-Host "    Trinity:       http://localhost:8600/api/trinity/run_case"
    }
    Write-Host ""
    Write-Host "  Processes:" -ForegroundColor Cyan
    Write-Host "    Mock Services: PID $($mockProc.Id)"
    if ($trinityProc) {
        Write-Host "    Trinity:       PID $($trinityProc.Id)"
    }
    Write-Host ""

    if ($KeepRunning) {
        Write-Host "  Services will keep running (-KeepRunning specified)" -ForegroundColor Gray
        Write-Host "  To stop: Stop-Process -Id $($mockProc.Id)" -ForegroundColor Gray
        if ($trinityProc) {
            Write-Host "           Stop-Process -Id $($trinityProc.Id)" -ForegroundColor Gray
        }
        Write-Host ""
        Write-Host "  Press any key to exit (services will continue)..."
        $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    } else {
        Write-Host "  Press any key to stop services and exit..."
        $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
        Cleanup
        Write-Host "[OK] Services stopped." -ForegroundColor Green
    }

} catch {
    Write-Host "[ERROR] $($_.Exception.Message)" -ForegroundColor Red
    Cleanup
    exit 1
}
