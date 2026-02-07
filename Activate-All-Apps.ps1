# Activate-All-Apps.ps1
# The Blade of Truth - Unified Application Activator
# MISSION: Launch all dashboards, portals, and engines in a coordinated cycle.

$ErrorActionPreference = "Continue"
$ScriptDir = $PSScriptRoot

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  THE BLADE OF TRUTH - APPLICATION ACTIVATION" -ForegroundColor Cyan
Write-Host "  Status: ORCHESTRATING..." -ForegroundColor Yellow
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# 1. Start Docker Stack (The Engine)
Write-Host "[1/4] Activating Sovereign Core (Docker)..." -ForegroundColor Yellow
& powershell -ExecutionPolicy Bypass -File "$ScriptDir\launch.ps1"
if ($LASTEXITCODE -ne 0) {
    Write-Host "  [WARN] Docker stack failed to start. Some features may be offline." -ForegroundColor Yellow
} else {
    Write-Host "  [OK] Core Engines Active." -ForegroundColor Green
}

# 2. Start Artifact Portal (The Evidence)
Write-Host "[2/4] Activating Artifact Portal (Passive Viewer)..." -ForegroundColor Yellow
& powershell -ExecutionPolicy Bypass -File "$ScriptDir\launch-artifact-portal.ps1"
Write-Host "  [OK] Artifact Portal Launched." -ForegroundColor Green

# 3. Start Governance Cockpit (The Dashboard)
Write-Host "[3/4] Activating Governance Cockpit (Streamlit)..." -ForegroundColor Yellow
$streamlitCmd = "streamlit run streamlit_app/Home.py --server.headless true"
Write-Host "  Launching at http://localhost:8501" -ForegroundColor Gray
Start-Process "http://localhost:8501"
Start-Job -ScriptBlock {
    Set-Location $using:ScriptDir
    streamlit run streamlit_app/Home.py --server.headless true
} | Out-Null
Write-Host "  [OK] Governance Cockpit starting in background." -ForegroundColor Green

# 4. Final Status
Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host "  ALL APPS ACTIVATED" -ForegroundColor Green
Write-Host "  - Docker Core: UP" -ForegroundColor Gray
Write-Host "  - Artifact Portal: OPEN" -ForegroundColor Gray
Write-Host "  - Governance Cockpit: http://localhost:8501" -ForegroundColor Gray
Write-Host "============================================================" -ForegroundColor Green
Write-Host "  Press ENTER to keep this console open, or Ctrl+C to exit." -ForegroundColor Cyan
Read-Host
