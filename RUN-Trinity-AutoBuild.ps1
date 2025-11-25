# RUN-Trinity-AutoBuild.ps1
# ===========================
# One-shot automated build / smoke for:
# - mock_services.py (8001-8005, 8502)
# - Trinity backend (8600)
# - Trinity run_case smoke test (with LLM doll)
#
# Usage:
#   .\RUN-Trinity-AutoBuild.ps1
#   .\RUN-Trinity-AutoBuild.ps1 -KeepRunning   # Don't kill services after test

param(
    [switch]$KeepRunning
)

$ErrorActionPreference = "Stop"
$base = $PSScriptRoot
if (-not $base) { $base = "C:\sovereign-system" }

Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host "  SOVEREIGN TRINITY - AUTOMATED BUILD" -ForegroundColor Cyan
Write-Host "  Mock Services + Trinity Backend + Smoke Test" -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host ""

# Track processes for cleanup
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
        Write-Host "`nCleaning up processes..." -ForegroundColor Yellow
        foreach ($p in $script:procs) {
            if ($p -and -not $p.HasExited) {
                Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue
            }
        }
    }
}

try {
    # 1) Check Python dependencies
    Write-Host "[STEP 1] Checking dependencies..." -ForegroundColor Cyan
    $depCheck = python -c "import fastapi, uvicorn, httpx; print('OK')" 2>&1
    if ($depCheck -ne "OK") {
        Write-Host "  Installing dependencies..." -ForegroundColor Yellow
        pip install fastapi uvicorn httpx pydantic --quiet
    } else {
        Write-Host "  Dependencies OK" -ForegroundColor Green
    }

    # 2) Start mock_services.py (8001-8005, 8502)
    Write-Host ""
    Write-Host "[STEP 2] Starting mock services (8001-8005, 8502)..." -ForegroundColor Cyan

    $mockProc = Start-Process python -PassThru -WindowStyle Minimized -ArgumentList @(
        "$base\mock_services.py"
    ) -WorkingDirectory $base
    $script:procs += $mockProc

    Start-Sleep -Seconds 3

    # 3) Start Trinity backend (8600)
    Write-Host "[STEP 3] Starting Trinity backend (8600)..." -ForegroundColor Cyan

    $trinityProc = Start-Process python -PassThru -WindowStyle Minimized -ArgumentList @(
        "$base\trinity\trinity_backend.py"
    ) -WorkingDirectory $base
    $script:procs += $trinityProc

    Start-Sleep -Seconds 3

    # 4) Wait for health endpoints
    Write-Host ""
    Write-Host "[STEP 4] Health checks..." -ForegroundColor Cyan

    $okAggregated = Wait-Healthy "http://localhost:8502/health" "Aggregated Backend (8502)"
    $okTrinity    = Wait-Healthy "http://localhost:8600/health" "Trinity Backend (8600)"

    if (-not ($okAggregated -and $okTrinity)) {
        Write-Host ""
        Write-Host "One or more services failed health check. Aborting." -ForegroundColor Red
        Cleanup
        exit 1
    }

    # 5) Execute Trinity run_case smoke test
    Write-Host ""
    Write-Host "[STEP 5] Running Trinity smoke test (CASE-TEST-001)..." -ForegroundColor Cyan

    $body = @{
        case_id = "CASE-TEST-001"
        query   = "evidence"
    } | ConvertTo-Json

    try {
        $resp = Invoke-RestMethod `
            -Uri "http://localhost:8600/api/trinity/run_case" `
            -Method POST `
            -Body $body `
            -ContentType "application/json"
    } catch {
        Write-Host "Trinity run_case call failed: $_" -ForegroundColor Red
        Cleanup
        exit 1
    }

    # 6) Parse and display results
    Write-Host ""
    Write-Host "=" * 60 -ForegroundColor Cyan
    Write-Host "  TRINITY SMOKE TEST RESULT" -ForegroundColor Cyan
    Write-Host "=" * 60 -ForegroundColor Cyan
    Write-Host ""

    $runId       = $resp.run_id
    $caseId      = $resp.case_id
    $success     = $resp.success
    $evidenceCnt = $resp.summary.evidence_found
    $integrity   = $resp.summary.integrity_status
    $action      = $resp.summary.action_taken
    $riskLens    = $resp.summary.risk_lens

    Write-Host "  Run ID          : $runId"
    Write-Host "  Case ID         : $caseId"
    Write-Host "  Success         : $success"
    Write-Host "  Evidence Found  : $evidenceCnt"
    Write-Host "  Integrity       : $integrity"
    Write-Host "  Action Taken    : $action"
    Write-Host "  Risk Lens       : $riskLens"
    Write-Host ""

    # LLM Analysis (Russian Doll)
    if ($resp.llm_analysis) {
        Write-Host "  --- LLM Russian Doll Analysis ---" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "  Inner Summary:" -ForegroundColor Gray
        Write-Host "    $($resp.llm_analysis.inner_summary)"
        Write-Host ""
        Write-Host "  Outer Commentary:" -ForegroundColor Gray
        Write-Host "    $($resp.llm_analysis.outer_commentary)"
        Write-Host ""
    }

    # SVC (Sovereign Version Control) Commit
    if ($resp.svc) {
        Write-Host "  --- SVC Commit (Sovereign Version Control) ---" -ForegroundColor Magenta
        Write-Host ""
        Write-Host "  Commit Hash   : $($resp.svc.commit_hash)" -ForegroundColor White
        Write-Host "  Parent Commit : $($resp.svc.parent_commit)" -ForegroundColor Gray
        Write-Host "  Commit ID     : $($resp.svc.commit_id)" -ForegroundColor Gray
        Write-Host ""
    }

    # Pipeline duration
    $duration = $resp.pipeline_duration_ms
    Write-Host "  Pipeline Duration: ${duration}ms"
    Write-Host ""

    # Build status
    Write-Host "=" * 60 -ForegroundColor Cyan
    if ($integrity -eq "INTACT" -and $riskLens -eq "low") {
        Write-Host "  BUILD STATUS: PASS" -ForegroundColor Green
        Write-Host "  All evidence verified, no tampering detected." -ForegroundColor Green
    } elseif ($integrity -eq "COMPROMISED") {
        Write-Host "  BUILD STATUS: WARN (Tamper Detected)" -ForegroundColor Yellow
        Write-Host "  Guardian should have enforced. Check enforcement actions." -ForegroundColor Yellow
    } else {
        Write-Host "  BUILD STATUS: UNKNOWN" -ForegroundColor DarkYellow
        Write-Host "  Integrity: $integrity, Risk: $riskLens" -ForegroundColor DarkYellow
    }
    Write-Host "=" * 60 -ForegroundColor Cyan
    Write-Host ""

    # ================================================================
    # SVC CLI: Show commit history
    # ================================================================
    Write-Host ""
    Write-Host "[SVC] Sovereign Version Control history (latest first):" -ForegroundColor Cyan
    Write-Host ""

    $svcScript = "$base\sov_vc\sov.py"
    if (Test-Path $svcScript) {
        try {
            python $svcScript log
        } catch {
            Write-Host "Warning: could not run SVC CLI (python sov.py log): $_" -ForegroundColor DarkYellow
        }
    } else {
        Write-Host "SVC CLI not found at $svcScript (skipping log view)." -ForegroundColor DarkYellow
    }

    Write-Host ""
    Write-Host "=" * 60 -ForegroundColor Cyan
    Write-Host ""

    if ($KeepRunning) {
        Write-Host "Services are still running (use -KeepRunning was specified)." -ForegroundColor Gray
        Write-Host "Mock Services PID: $($mockProc.Id)" -ForegroundColor Gray
        Write-Host "Trinity PID: $($trinityProc.Id)" -ForegroundColor Gray
        Write-Host ""
        Write-Host "To stop: Stop-Process -Id $($mockProc.Id),$($trinityProc.Id)" -ForegroundColor Gray
    } else {
        Cleanup
        Write-Host "Services stopped. Build complete." -ForegroundColor Gray
    }

} catch {
    Write-Host "Error: $_" -ForegroundColor Red
    Cleanup
    exit 1
}
