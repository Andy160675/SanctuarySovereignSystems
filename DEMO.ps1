# Sovereign System V3 - One-Click Demo
# Tag: v3.0.0-complete

$Host.UI.RawUI.WindowTitle = "Sovereign System V3 Demo"

Write-Host ""
Write-Host "  ============================================================" -ForegroundColor Cyan
Write-Host "   SOVEREIGN SYSTEM V3 - One-Click Demo" -ForegroundColor Cyan
Write-Host "   Tag: v3.0.0-complete" -ForegroundColor Cyan
Write-Host "  ============================================================" -ForegroundColor Cyan
Write-Host ""

Set-Location $PSScriptRoot

# Check Python
Write-Host "  [1/4] Checking Python..." -ForegroundColor Yellow
try {
    $pyVersion = python --version 2>&1
    Write-Host "        $pyVersion" -ForegroundColor Green
} catch {
    Write-Host "  ERROR: Python not found. Please install Python 3.10+" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Check Streamlit
Write-Host ""
Write-Host "  [2/4] Checking Streamlit..." -ForegroundColor Yellow
$streamlitCheck = python -c "import streamlit; print(streamlit.__version__)" 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "        Installing Streamlit..." -ForegroundColor Yellow
    pip install streamlit | Out-Null
}
Write-Host "        Streamlit OK" -ForegroundColor Green

# Check project modules
Write-Host ""
Write-Host "  [3/4] Checking project modules..." -ForegroundColor Yellow
python -c "from src.boardroom.anchoring import load_chain" 2>&1 | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Host "  ERROR: Project modules not found. Run from repo root." -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}
Write-Host "        Modules OK" -ForegroundColor Green

# Launch
Write-Host ""
Write-Host "  [4/4] Launching Governance Cockpit..." -ForegroundColor Yellow
Write-Host ""
Write-Host "  ============================================================" -ForegroundColor Cyan
Write-Host "   Opening browser at http://localhost:8501" -ForegroundColor White
Write-Host "   Press Ctrl+C to stop" -ForegroundColor White
Write-Host "  ============================================================" -ForegroundColor Cyan
Write-Host ""

Start-Process "http://localhost:8501"
streamlit run streamlit_app/Home.py --server.headless true
