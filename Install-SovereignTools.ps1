# =============================================================================
# Install-SovereignTools.ps1
# Sovereign Away Kit - Offline Tool Installer
# =============================================================================
#
# PURPOSE: Install Git, Python, VS Code from local USB installers
# LOCATION: F:\Install-SovereignTools.ps1 (SOV_BOOT USB)
#
# Expected folder structure on USB:
#   F:\Tools\
#       Git-2.43.0-64-bit.exe
#       python-3.11.9-amd64.exe
#       VSCodeSetup-x64-1.85.0.exe (optional)
#
# =============================================================================

$ErrorActionPreference = "SilentlyContinue"

function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $color = switch ($Level) {
        "INFO"  { "White" }
        "WARN"  { "Yellow" }
        "ERROR" { "Red" }
        "OK"    { "Green" }
        default { "White" }
    }
    Write-Host "[$ts] [$Level] $Message" -ForegroundColor $color
}

Write-Host ""
Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host "  SOVEREIGN TOOLS INSTALLER" -ForegroundColor Cyan
Write-Host "  Offline Installation from USB" -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host ""

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$toolsDir = Join-Path $scriptDir "Tools"

Write-Log "Script directory: $scriptDir"
Write-Log "Tools directory: $toolsDir"
Write-Host ""

# =============================================================================
# Check what's already installed
# =============================================================================

Write-Log "Checking existing installations..."

$gitInstalled = $null -ne (Get-Command git -ErrorAction SilentlyContinue)
$pythonInstalled = $null -ne (Get-Command python -ErrorAction SilentlyContinue)
$codeInstalled = $null -ne (Get-Command code -ErrorAction SilentlyContinue)

if ($gitInstalled) {
    $gitVer = git --version 2>&1
    Write-Log "Git already installed: $gitVer" "OK"
} else {
    Write-Log "Git not found" "WARN"
}

if ($pythonInstalled) {
    $pyVer = python --version 2>&1
    Write-Log "Python already installed: $pyVer" "OK"
} else {
    Write-Log "Python not found" "WARN"
}

if ($codeInstalled) {
    Write-Log "VS Code already installed" "OK"
} else {
    Write-Log "VS Code not found (optional)" "WARN"
}

Write-Host ""

# =============================================================================
# Install Git (if needed and installer exists)
# =============================================================================

if (-not $gitInstalled) {
    $gitInstaller = Get-ChildItem "$toolsDir\Git*.exe" -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($gitInstaller) {
        Write-Log "Installing Git from: $($gitInstaller.Name)..."
        Start-Process -FilePath $gitInstaller.FullName -ArgumentList "/VERYSILENT", "/NORESTART", "/NOCANCEL" -Wait

        # Refresh PATH
        $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")

        if (Get-Command git -ErrorAction SilentlyContinue) {
            Write-Log "Git installed successfully" "OK"
        } else {
            Write-Log "Git installation may require restart" "WARN"
        }
    } else {
        Write-Log "No Git installer found in $toolsDir" "WARN"
    }
}

# =============================================================================
# Install Python (if needed and installer exists)
# =============================================================================

if (-not $pythonInstalled) {
    $pyInstaller = Get-ChildItem "$toolsDir\python*.exe" -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($pyInstaller) {
        Write-Log "Installing Python from: $($pyInstaller.Name)..."
        # /passive = unattended with progress, InstallAllUsers=1, PrependPath=1 adds to PATH
        Start-Process -FilePath $pyInstaller.FullName -ArgumentList "/passive", "InstallAllUsers=1", "PrependPath=1" -Wait

        # Refresh PATH
        $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")

        if (Get-Command python -ErrorAction SilentlyContinue) {
            Write-Log "Python installed successfully" "OK"
        } else {
            Write-Log "Python installation may require restart" "WARN"
        }
    } else {
        Write-Log "No Python installer found in $toolsDir" "WARN"
    }
}

# =============================================================================
# Install VS Code (if needed and installer exists) - Optional
# =============================================================================

if (-not $codeInstalled) {
    $codeInstaller = Get-ChildItem "$toolsDir\VSCode*.exe" -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($codeInstaller) {
        Write-Log "Installing VS Code from: $($codeInstaller.Name)..."
        Start-Process -FilePath $codeInstaller.FullName -ArgumentList "/VERYSILENT", "/NORESTART", "/MERGETASKS=!runcode,addcontextmenufiles,addcontextmenufolders,associatewithfiles,addtopath" -Wait

        # Refresh PATH
        $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")

        if (Get-Command code -ErrorAction SilentlyContinue) {
            Write-Log "VS Code installed successfully" "OK"
        } else {
            Write-Log "VS Code installation may require restart" "WARN"
        }
    } else {
        Write-Log "No VS Code installer found in $toolsDir (optional)" "INFO"
    }
}

# =============================================================================
# Install Python packages from pip-cache (if exists)
# =============================================================================

$pipCache = Join-Path $scriptDir "pip-cache"
if (Test-Path $pipCache) {
    Write-Host ""
    Write-Log "Installing Python packages from offline cache..."

    $pipCmd = "pip install --no-index --find-links=`"$pipCache`" fastapi uvicorn httpx pydantic streamlit requests python-multipart"

    try {
        Invoke-Expression $pipCmd
        Write-Log "Python packages installed from cache" "OK"
    } catch {
        Write-Log "Some packages may have failed: $_" "WARN"
    }
} else {
    Write-Log "No pip-cache found, skipping offline package install" "INFO"
}

# =============================================================================
# Summary
# =============================================================================

Write-Host ""
Write-Host "=" * 60 -ForegroundColor Green
Write-Host "  TOOL INSTALLATION COMPLETE" -ForegroundColor Green
Write-Host "=" * 60 -ForegroundColor Green
Write-Host ""

# Re-check
$gitOk = $null -ne (Get-Command git -ErrorAction SilentlyContinue)
$pyOk = $null -ne (Get-Command python -ErrorAction SilentlyContinue)
$codeOk = $null -ne (Get-Command code -ErrorAction SilentlyContinue)

Write-Host "  Git:     $(if ($gitOk) { 'OK' } else { 'NOT FOUND' })"
Write-Host "  Python:  $(if ($pyOk) { 'OK' } else { 'NOT FOUND' })"
Write-Host "  VS Code: $(if ($codeOk) { 'OK' } else { 'NOT FOUND (optional)' })"
Write-Host ""

if (-not $gitOk -or -not $pyOk) {
    Write-Log "Some tools may require a restart to appear in PATH" "WARN"
}

Write-Host ""
