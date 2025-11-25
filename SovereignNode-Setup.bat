@echo off
setlocal EnableDelayedExpansion

:: =============================================================================
:: SovereignNode-Setup.bat
:: Sovereign System Offline Installer for Air-Gapped Nodes
:: =============================================================================

title Sovereign Node Setup - Away Kit v1

echo.
echo ============================================================
echo   SOVEREIGN NODE SETUP - AWAY KIT v1
echo   Air-Gapped Installation Wizard
echo ============================================================
echo.

:: Detect script location (should be on boot USB)
set "SCRIPT_DIR=%~dp0"
set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"

:: Target installation directory
set "TARGET=C:\sovereign-system"

echo [INFO] Installer location: %SCRIPT_DIR%
echo [INFO] Target directory:   %TARGET%
echo.

:: =============================================================================
:: Step 1: Check Python
:: =============================================================================
echo [STEP 1/6] Checking Python installation...

python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [WARN] Python not found in PATH.
    echo.
    if exist "%SCRIPT_DIR%\installers\python-3.11.9-amd64.exe" (
        echo [INFO] Found Python installer in kit.
        echo [INFO] Please run: %SCRIPT_DIR%\installers\python-3.11.9-amd64.exe
        echo [INFO] Select "Add Python to PATH" during installation.
        echo.
        set /p INSTALL_PY="Install Python now? (Y/N): "
        if /i "!INSTALL_PY!"=="Y" (
            start /wait "" "%SCRIPT_DIR%\installers\python-3.11.9-amd64.exe" /passive InstallAllUsers=1 PrependPath=1
            echo [OK] Python installer completed. Please restart this script.
            pause
            exit /b 0
        )
    ) else (
        echo [ERROR] Python not found and no installer in kit.
        echo [ERROR] Please install Python 3.10+ manually.
        pause
        exit /b 1
    )
) else (
    for /f "tokens=2" %%v in ('python --version 2^>^&1') do set PY_VER=%%v
    echo [OK] Python !PY_VER! found.
)

:: =============================================================================
:: Step 2: Create Target Directory
:: =============================================================================
echo.
echo [STEP 2/6] Creating target directory...

if not exist "%TARGET%" (
    mkdir "%TARGET%"
    echo [OK] Created %TARGET%
) else (
    echo [INFO] Directory already exists: %TARGET%
)

:: Create subdirectories
mkdir "%TARGET%\evidence_store" 2>nul
mkdir "%TARGET%\evidence_store\CASE-TEST-001" 2>nul
mkdir "%TARGET%\sov_vc" 2>nul
mkdir "%TARGET%\sov_vc\commits" 2>nul
mkdir "%TARGET%\trinity" 2>nul
mkdir "%TARGET%\boardroom" 2>nul
mkdir "%TARGET%\logs" 2>nul

echo [OK] Directory structure ready.

:: =============================================================================
:: Step 3: Install Python Dependencies (Offline)
:: =============================================================================
echo.
echo [STEP 3/6] Installing Python dependencies (offline)...

if exist "%SCRIPT_DIR%\pip-cache" (
    echo [INFO] Installing from offline cache...
    pip install --no-index --find-links="%SCRIPT_DIR%\pip-cache" fastapi uvicorn httpx pydantic streamlit requests python-multipart
    if %ERRORLEVEL% EQU 0 (
        echo [OK] Dependencies installed from cache.
    ) else (
        echo [WARN] Some packages may have failed. Continuing...
    )
) else (
    echo [WARN] No pip-cache found. Attempting online install...
    pip install fastapi uvicorn httpx pydantic streamlit requests python-multipart
)

:: =============================================================================
:: Step 4: Copy Core Files
:: =============================================================================
echo.
echo [STEP 4/6] Copying core system files...

:: Check for core-minimal first (boot USB), then full system
if exist "%SCRIPT_DIR%\core-minimal" (
    echo [INFO] Copying from core-minimal...
    xcopy "%SCRIPT_DIR%\core-minimal\*" "%TARGET%\" /E /Y /Q
) else if exist "%SCRIPT_DIR%\sovereign-system" (
    echo [INFO] Copying from sovereign-system...
    xcopy "%SCRIPT_DIR%\sovereign-system\*" "%TARGET%\" /E /Y /Q
) else (
    echo [WARN] No source files found in kit. Manual copy required.
)

:: Copy README
if exist "%SCRIPT_DIR%\AWAY_KIT_README.md" (
    copy "%SCRIPT_DIR%\AWAY_KIT_README.md" "%TARGET%\" /Y >nul
)

echo [OK] Core files copied.

:: =============================================================================
:: Step 5: Verify Installation
:: =============================================================================
echo.
echo [STEP 5/6] Verifying installation...

set VERIFY_PASS=1

if exist "%TARGET%\mock_services.py" (
    echo [OK] mock_services.py present
) else (
    echo [FAIL] mock_services.py missing
    set VERIFY_PASS=0
)

if exist "%TARGET%\sov_vc\sov.py" (
    echo [OK] sov_vc/sov.py present
) else (
    echo [WARN] sov_vc/sov.py missing (SVC features unavailable)
)

if exist "%TARGET%\trinity" (
    echo [OK] trinity/ directory present
) else (
    echo [WARN] trinity/ missing (Trinity features unavailable)
)

:: Quick Python import test
python -c "import fastapi, uvicorn, httpx" 2>nul
if %ERRORLEVEL% EQU 0 (
    echo [OK] Python dependencies verified
) else (
    echo [WARN] Some Python dependencies may be missing
)

:: =============================================================================
:: Step 6: Create Desktop Shortcut
:: =============================================================================
echo.
echo [STEP 6/6] Creating shortcuts...

:: Create a simple launcher batch file
echo @echo off > "%TARGET%\START-SOVEREIGN.bat"
echo cd /d "%TARGET%" >> "%TARGET%\START-SOVEREIGN.bat"
echo echo Starting Sovereign System... >> "%TARGET%\START-SOVEREIGN.bat"
echo python mock_services.py >> "%TARGET%\START-SOVEREIGN.bat"

echo [OK] Created START-SOVEREIGN.bat in %TARGET%

:: =============================================================================
:: Complete
:: =============================================================================
echo.
echo ============================================================
echo   INSTALLATION COMPLETE
echo ============================================================
echo.
echo   Location:    %TARGET%
echo   Start:       %TARGET%\START-SOVEREIGN.bat
echo   Health:      http://localhost:8502/health
echo   SVC Log:     python sov_vc/sov.py log
echo.
echo   Next Steps:
echo   1. cd %TARGET%
echo   2. python mock_services.py
echo   3. Open http://localhost:8502/health in browser
echo.
echo ============================================================
echo.

pause
