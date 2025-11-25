# start-sovereign-demo.ps1
# One double-click -> Phase-5E sovereign demo (mocks + UI)
# ============================================================

$ErrorActionPreference = "Stop"
$base = "C:\sovereign-system"

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  SOVEREIGN SYSTEM - PHASE 5E DEMO LAUNCHER" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

function Wait-Healthy {
    param(
        [string]$url,
        [string]$name,
        [int]$timeout = 30
    )

    Write-Host "Waiting for $name ($url) ..." -NoNewline
    $sw = [Diagnostics.Stopwatch]::StartNew()
    while ($sw.Elapsed.TotalSeconds -lt $timeout) {
        try {
            $r = Invoke-WebRequest -Uri $url -Method Get -UseBasicParsing -TimeoutSec 2
            if ($r.StatusCode -eq 200) {
                Write-Host " OK" -ForegroundColor Green
                return $true
            }
        } catch {
            Start-Sleep -Milliseconds 500
        }
        Write-Host "." -NoNewline
    }
    Write-Host " TIMEOUT" -ForegroundColor Red
    return $false
}

# Check if venv exists, create if not
$venvPath = "$base\.venv"
if (-not (Test-Path "$venvPath\Scripts\Activate.ps1")) {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    Push-Location $base
    python -m venv .venv
    Pop-Location
}

# 1. Launch mock services window
Write-Host ""
Write-Host "Starting mock services (ports 8001-8005, 8502)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit -Command `"cd '$base'; .\.venv\Scripts\Activate.ps1; pip install fastapi uvicorn pydantic -q --disable-pip-version-check; python .\mock_services.py`""
Start-Sleep 3

# 2. Launch Boardroom UI (if exists)
$boardroomPath = "$base\boardroom"
if (Test-Path "$boardroomPath\boardroom_app.py") {
    Write-Host "Starting Boardroom UI (port 8501)..." -ForegroundColor Yellow
    Start-Process powershell -ArgumentList "-NoExit -Command `"cd '$boardroomPath'; & '$venvPath\Scripts\Activate.ps1'; pip install streamlit requests -q --disable-pip-version-check; streamlit run boardroom_app.py --server.port 8501 --server.headless true`""
    Start-Sleep 2
} else {
    Write-Host "Boardroom UI not found at $boardroomPath - skipping" -ForegroundColor Gray
}

# 3. Wait for services to be healthy
Write-Host ""
Start-Sleep 5
$coreOk = Wait-Healthy "http://localhost:8502/health" "Aggregated Backend"

if ($coreOk) {
    # 4. Show evidence info
    Write-Host ""
    Write-Host "Fetching evidence info..." -ForegroundColor Cyan
    try {
        $evidenceInfo = Invoke-RestMethod -Uri "http://localhost:8502/api/evidence/info" -Method Get
        Write-Host "  Evidence file: $($evidenceInfo.mock_file)" -ForegroundColor White
        Write-Host "  Original hash: $($evidenceInfo.original_hash)" -ForegroundColor White
        Write-Host "  Current hash:  $($evidenceInfo.current_hash)" -ForegroundColor White
        if ($evidenceInfo.tampered) {
            Write-Host "  Status: TAMPERED!" -ForegroundColor Red
        } else {
            Write-Host "  Status: INTACT" -ForegroundColor Green
        }
    } catch {
        Write-Host "  Could not fetch evidence info" -ForegroundColor Gray
    }

    # 5. Auto-open browser
    Write-Host ""
    Write-Host "Opening browser..." -ForegroundColor Cyan
    if (Test-Path "$boardroomPath\boardroom_app.py") {
        Start-Process "http://localhost:8501"
    } else {
        Start-Process "http://localhost:8502"
    }
}

Write-Host ""
Write-Host "============================================" -ForegroundColor Green
Write-Host "  DEMO IS LIVE" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green
Write-Host ""
Write-Host "TAMPER TEST:" -ForegroundColor Yellow
Write-Host "  1. Open: C:\sovereign-system\evidence_store\CASE-TEST-001\mock-event-1.jsonl"
Write-Host "  2. Add a space or change text, save"
Write-Host "  3. Call /api/core/verify_hash - match will be false"
Write-Host ""
Write-Host "QUICK TEST (PowerShell):" -ForegroundColor Yellow
Write-Host '  $body = @{ query="CASE-TEST-001"; limit=1 } | ConvertTo-Json'
Write-Host '  Invoke-RestMethod -Uri http://localhost:8502/truth/search -Method POST -Body $body -ContentType "application/json"'
Write-Host ""
Write-Host "Press any key to exit this launcher (services keep running)..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
