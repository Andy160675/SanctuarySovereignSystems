# ============================================================================
# SOVEREIGN SYSTEM - FULL OFFLINE READINESS PACKAGE
# Downloads ALL dependencies for air-gapped deployment
# ============================================================================

param(
    [string]$OutputPath = "C:\SOVEREIGN-OFFLINE-PACKAGE",
    [switch]$SkipDocker,
    [switch]$SkipPython,
    [switch]$SkipOllama,
    [switch]$SkipInstallers
)

$ErrorActionPreference = "Continue"
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"

Write-Host ""
Write-Host "================================================================" -ForegroundColor Red
Write-Host "  SOVEREIGN SYSTEM - OFFLINE READINESS PACKAGE BUILDER" -ForegroundColor Red
Write-Host "  Full Air-Gapped Deployment Preparation" -ForegroundColor Red
Write-Host "================================================================" -ForegroundColor Red
Write-Host ""

# ============================================================================
# DIRECTORY STRUCTURE
# ============================================================================

$dirs = @(
    "$OutputPath",
    "$OutputPath\installers",
    "$OutputPath\installers\docker",
    "$OutputPath\installers\python",
    "$OutputPath\installers\git",
    "$OutputPath\docker-images",
    "$OutputPath\python-packages",
    "$OutputPath\ollama-models",
    "$OutputPath\source-code",
    "$OutputPath\corpus",
    "$OutputPath\scripts"
)

Write-Host "[1/7] Creating directory structure..." -ForegroundColor Yellow

foreach ($dir in $dirs) {
    New-Item -ItemType Directory -Path $dir -Force | Out-Null
    Write-Host "   + $dir" -ForegroundColor Gray
}

# ============================================================================
# SOFTWARE INSTALLERS
# ============================================================================

if (-not $SkipInstallers) {
    Write-Host ""
    Write-Host "[2/7] Downloading software installers..." -ForegroundColor Yellow

    # Docker Desktop
    $dockerUrl = "https://desktop.docker.com/win/main/amd64/Docker%20Desktop%20Installer.exe"
    $dockerPath = "$OutputPath\installers\docker\DockerDesktopInstaller.exe"
    if (-not (Test-Path $dockerPath)) {
        Write-Host "   Downloading Docker Desktop..." -ForegroundColor Cyan
        try {
            Invoke-WebRequest -Uri $dockerUrl -OutFile $dockerPath -UseBasicParsing
            Write-Host "   OK Docker Desktop downloaded" -ForegroundColor Green
        } catch {
            Write-Host "   WARN Failed to download Docker Desktop" -ForegroundColor Yellow
        }
    } else {
        Write-Host "   OK Docker Desktop already cached" -ForegroundColor Green
    }

    # Python 3.11
    $pythonUrl = "https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe"
    $pythonPath = "$OutputPath\installers\python\python-3.11.9-amd64.exe"
    if (-not (Test-Path $pythonPath)) {
        Write-Host "   Downloading Python 3.11..." -ForegroundColor Cyan
        try {
            Invoke-WebRequest -Uri $pythonUrl -OutFile $pythonPath -UseBasicParsing
            Write-Host "   OK Python 3.11 downloaded" -ForegroundColor Green
        } catch {
            Write-Host "   WARN Failed to download Python" -ForegroundColor Yellow
        }
    } else {
        Write-Host "   OK Python 3.11 already cached" -ForegroundColor Green
    }

    # Git
    $gitUrl = "https://github.com/git-for-windows/git/releases/download/v2.43.0.windows.1/Git-2.43.0-64-bit.exe"
    $gitPath = "$OutputPath\installers\git\Git-2.43.0-64-bit.exe"
    if (-not (Test-Path $gitPath)) {
        Write-Host "   Downloading Git..." -ForegroundColor Cyan
        try {
            Invoke-WebRequest -Uri $gitUrl -OutFile $gitPath -UseBasicParsing
            Write-Host "   OK Git downloaded" -ForegroundColor Green
        } catch {
            Write-Host "   WARN Failed to download Git" -ForegroundColor Yellow
        }
    } else {
        Write-Host "   OK Git already cached" -ForegroundColor Green
    }

    # Ollama
    $ollamaUrl = "https://ollama.com/download/OllamaSetup.exe"
    $ollamaPath = "$OutputPath\installers\OllamaSetup.exe"
    if (-not (Test-Path $ollamaPath)) {
        Write-Host "   Downloading Ollama..." -ForegroundColor Cyan
        try {
            Invoke-WebRequest -Uri $ollamaUrl -OutFile $ollamaPath -UseBasicParsing
            Write-Host "   OK Ollama downloaded" -ForegroundColor Green
        } catch {
            Write-Host "   WARN Failed to download Ollama" -ForegroundColor Yellow
        }
    } else {
        Write-Host "   OK Ollama already cached" -ForegroundColor Green
    }
}

# ============================================================================
# DOCKER IMAGES
# ============================================================================

if (-not $SkipDocker) {
    Write-Host ""
    Write-Host "[3/7] Pulling and exporting Docker images..." -ForegroundColor Yellow

    $dockerImages = @(
        "ollama/ollama:latest",
        "python:3.11-slim",
        "node:20-alpine",
        "nginx:alpine"
    )

    foreach ($image in $dockerImages) {
        Write-Host "   Pulling $image..." -ForegroundColor Cyan
        docker pull $image 2>&1 | Out-Null
    }

    foreach ($image in $dockerImages) {
        $safeName = $image -replace "[:/]", "_"
        $tarPath = "$OutputPath\docker-images\$safeName.tar"

        if (-not (Test-Path $tarPath)) {
            Write-Host "   Exporting $image..." -ForegroundColor Cyan
            docker save -o $tarPath $image
            Write-Host "   OK Saved: $safeName.tar" -ForegroundColor Green
        } else {
            Write-Host "   OK $safeName.tar exists" -ForegroundColor Green
        }
    }

    # Create load script
    $loadScript = "# Load Docker images`nGet-ChildItem -Path '.\docker-images\*.tar' | ForEach-Object { docker load -i `$_.FullName }"
    Set-Content -Path "$OutputPath\docker-images\load-images.ps1" -Value $loadScript
}

# ============================================================================
# PYTHON PACKAGES
# ============================================================================

if (-not $SkipPython) {
    Write-Host ""
    Write-Host "[4/7] Downloading Python packages..." -ForegroundColor Yellow

    $packages = @(
        "fastapi",
        "uvicorn",
        "httpx",
        "pydantic",
        "python-dotenv",
        "pyyaml",
        "requests",
        "pytest"
    )

    $wheelDir = "$OutputPath\python-packages"
    $reqFile = "$OutputPath\python-packages\requirements-offline.txt"
    $packages | Set-Content -Path $reqFile

    Write-Host "   Downloading wheels..." -ForegroundColor Cyan
    pip download -d $wheelDir -r $reqFile 2>&1 | Out-Null
    Write-Host "   OK Python packages downloaded" -ForegroundColor Green
}

# ============================================================================
# OLLAMA MODELS
# ============================================================================

if (-not $SkipOllama) {
    Write-Host ""
    Write-Host "[5/7] Downloading Ollama models..." -ForegroundColor Yellow

    $models = @("nomic-embed-text")

    foreach ($model in $models) {
        Write-Host "   Pulling $model..." -ForegroundColor Cyan
        ollama pull $model 2>&1 | Out-Null
    }

    $ollamaDir = "$env:USERPROFILE\.ollama"
    if (Test-Path $ollamaDir) {
        Write-Host "   Copying Ollama model cache..." -ForegroundColor Cyan
        robocopy "$ollamaDir\models" "$OutputPath\ollama-models" /E /MT:4 /R:1 /W:1 2>&1 | Out-Null
        Write-Host "   OK Ollama models copied" -ForegroundColor Green
    }
}

# ============================================================================
# SOURCE CODE
# ============================================================================

Write-Host ""
Write-Host "[6/7] Copying source code..." -ForegroundColor Yellow

if (Test-Path "C:\sovereign-system") {
    Write-Host "   Copying sovereign-system..." -ForegroundColor Cyan
    robocopy "C:\sovereign-system" "$OutputPath\source-code\sovereign-system" /E /MT:8 /R:1 /W:1 /XD node_modules .git __pycache__ .venv 2>&1 | Out-Null
    Write-Host "   OK sovereign-system copied" -ForegroundColor Green
}

if (Test-Path "C:\Users\andyj\Blade2AI\PrototypeV2.1") {
    Write-Host "   Copying Blade2AI..." -ForegroundColor Cyan
    robocopy "C:\Users\andyj\Blade2AI\PrototypeV2.1" "$OutputPath\source-code\Blade2AI" /E /MT:8 /R:1 /W:1 /XD node_modules .git __pycache__ .venv 2>&1 | Out-Null
    Write-Host "   OK Blade2AI copied" -ForegroundColor Green
}

$corpusSrc = "D:\SOVEREIGN-2025-11-19"
if (Test-Path $corpusSrc) {
    Write-Host "   Copying corpus (may take a while)..." -ForegroundColor Cyan
    robocopy $corpusSrc "$OutputPath\corpus" /E /MT:8 /R:1 /W:1 2>&1 | Out-Null
    Write-Host "   OK Corpus copied" -ForegroundColor Green
}

# ============================================================================
# DEPLOYMENT SCRIPTS
# ============================================================================

Write-Host ""
Write-Host "[7/7] Creating deployment scripts..." -ForegroundColor Yellow

Copy-Item -Path "C:\sovereign-system\deploy\*.ps1" -Destination "$OutputPath\scripts\" -Force -ErrorAction SilentlyContinue
Copy-Item -Path "C:\sovereign-system\deploy\*.md" -Destination "$OutputPath\scripts\" -Force -ErrorAction SilentlyContinue

# Create README
$readme = @"
SOVEREIGN SYSTEM - OFFLINE DEPLOYMENT PACKAGE
Created: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")

CONTENTS:
---------
/installers/        - Docker, Python, Git, Ollama installers
/docker-images/     - Pre-built Docker images (.tar)
/python-packages/   - Python wheels
/ollama-models/     - LLM models
/source-code/       - Sovereign System + Blade2AI
/corpus/            - Document corpus
/scripts/           - Deployment scripts

INSTALLATION:
-------------
1. Install Docker: installers\docker\DockerDesktopInstaller.exe
2. Install Python: installers\python\python-3.11.9-amd64.exe
3. Load Docker images: docker-images\load-images.ps1
4. Deploy: scripts\deploy-lan.ps1 -NodeRole NODE-01

NODE ASSIGNMENTS:
-----------------
NODE-01 (192.168.50.10) - Orchestrator
NODE-02 (192.168.50.20) - Truth Engine
NODE-03 (192.168.50.30) - Agent Fleet
"@

Set-Content -Path "$OutputPath\README.txt" -Value $readme

# ============================================================================
# SUMMARY
# ============================================================================

$totalSize = (Get-ChildItem -Path $OutputPath -Recurse -File -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum / 1GB

Write-Host ""
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "  OFFLINE PACKAGE COMPLETE" -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Location: $OutputPath" -ForegroundColor White
Write-Host "  Size:     $([Math]::Round($totalSize, 2)) GB" -ForegroundColor White
Write-Host ""
Write-Host "  Copy to USB/External drive for transfer" -ForegroundColor Yellow
Write-Host ""
