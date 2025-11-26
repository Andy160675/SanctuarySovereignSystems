@echo off
title Sovereign System V3 Demo
color 0A

echo.
echo  ============================================================
echo   SOVEREIGN SYSTEM V3 - One-Click Demo
echo   Tag: v3.0.0-complete
echo  ============================================================
echo.

cd /d "%~dp0"

echo  [1/4] Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo  ERROR: Python not found. Please install Python 3.10+
    pause
    exit /b 1
)
echo        Python OK

echo.
echo  [2/4] Checking Streamlit...
python -c "import streamlit" >nul 2>&1
if errorlevel 1 (
    echo        Installing Streamlit...
    pip install streamlit >nul 2>&1
)
echo        Streamlit OK

echo.
echo  [3/4] Checking project modules...
python -c "from src.boardroom.anchoring import load_chain" >nul 2>&1
if errorlevel 1 (
    echo  ERROR: Project modules not found. Run from repo root.
    pause
    exit /b 1
)
echo        Modules OK

echo.
echo  [4/4] Launching Governance Cockpit...
echo.
echo  ============================================================
echo   Opening browser at http://localhost:8501
echo   Press Ctrl+C to stop
echo  ============================================================
echo.

start "" http://localhost:8501
streamlit run streamlit_app/Home.py --server.headless true

pause
