# ============================================================================
# SOVEREIGN SYSTEM - COMPLETE OFFLINE DEPLOYMENT PACKAGE
# Single script - no breadcrumbs - runs to completion
# ============================================================================
# Usage: .\DEPLOYMENT_PACKAGE.ps1 -TargetPath E:\SOVEREIGN
# ============================================================================

param(
    [Parameter(Mandatory=$true)]
    [string]$TargetPath
)

$ErrorActionPreference = "Stop"

function Write-Step { param($n, $t, $msg) Write-Host "[$n/$t] $msg" -ForegroundColor Yellow }
function Write-OK { param($msg) Write-Host "   OK $msg" -ForegroundColor Green }
function Write-Info { param($msg) Write-Host "   $msg" -ForegroundColor Cyan }

Write-Host "`n=== SOVEREIGN OFFLINE DEPLOYMENT PACKAGE ===" -ForegroundColor Red
Write-Host "Target: $TargetPath`n" -ForegroundColor White

# ============================================================================
# 1. CREATE STRUCTURE
# ============================================================================
Write-Step 1 6 "Creating directory structure"

$structure = @(
    "installers", "docker-images", "ollama-models",
    "source\sovereign-system", "source\Blade2AI",
    "corpus", "scripts"
)
foreach ($dir in $structure) {
    New-Item -ItemType Directory -Path "$TargetPath\$dir" -Force | Out-Null
}
Write-OK "Structure created"

# ============================================================================
# 2. DOWNLOAD INSTALLERS (lightweight alternatives)
# ============================================================================
Write-Step 2 6 "Downloading installers"

$downloads = @{
    "python-3.11.9-amd64.exe" = "https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe"
    "Git-2.43.0-64-bit.exe" = "https://github.com/git-for-windows/git/releases/download/v2.43.0.windows.1/Git-2.43.0-64-bit.exe"
    "OllamaSetup.exe" = "https://ollama.com/download/OllamaSetup.exe"
}

foreach ($file in $downloads.Keys) {
    $dest = "$TargetPath\installers\$file"
    if (-not (Test-Path $dest)) {
        Write-Info "Downloading $file..."
        Invoke-WebRequest -Uri $downloads[$file] -OutFile $dest -UseBasicParsing
    }
    Write-OK $file
}

# ============================================================================
# 3. EXPORT DOCKER IMAGES (if Docker available)
# ============================================================================
Write-Step 3 6 "Exporting Docker images"

$dockerAvailable = $null -ne (Get-Command docker -ErrorAction SilentlyContinue)
if ($dockerAvailable) {
    $images = @("ollama/ollama:latest", "python:3.11-slim")
    foreach ($img in $images) {
        $safeName = $img -replace "[:/]", "_"
        $tarPath = "$TargetPath\docker-images\$safeName.tar"
        if (-not (Test-Path $tarPath)) {
            Write-Info "Pulling $img..."
            docker pull $img 2>&1 | Out-Null
            Write-Info "Saving $img..."
            docker save -o $tarPath $img
        }
        Write-OK "$safeName.tar"
    }
} else {
    Write-Info "Docker not available - skipping image export"
    Write-Info "Install Docker on target and pull images manually"
}

# ============================================================================
# 4. EXPORT OLLAMA MODELS
# ============================================================================
Write-Step 4 6 "Exporting Ollama models"

$ollamaModels = "$env:USERPROFILE\.ollama\models"
if (Test-Path $ollamaModels) {
    robocopy $ollamaModels "$TargetPath\ollama-models" /E /MT:4 /R:1 /W:1 /NJH /NJS | Out-Null
    Write-OK "Ollama models exported"
} else {
    Write-Info "No local Ollama models found"
}

# ============================================================================
# 5. COPY SOURCE CODE
# ============================================================================
Write-Step 5 6 "Copying source code"

$sources = @{
    "C:\sovereign-system" = "$TargetPath\source\sovereign-system"
    "C:\Users\andyj\Blade2AI\PrototypeV2.1" = "$TargetPath\source\Blade2AI"
}

foreach ($src in $sources.Keys) {
    if (Test-Path $src) {
        Write-Info "Copying $(Split-Path $src -Leaf)..."
        robocopy $src $sources[$src] /E /MT:8 /R:1 /W:1 /XD node_modules .git __pycache__ .venv /NJH /NJS | Out-Null
        Write-OK (Split-Path $src -Leaf)
    }
}

# Copy corpus if exists
$corpus = "D:\SOVEREIGN-2025-11-19"
if (Test-Path $corpus) {
    Write-Info "Copying corpus..."
    robocopy $corpus "$TargetPath\corpus" /E /MT:8 /R:1 /W:1 /NJH /NJS | Out-Null
    Write-OK "Corpus"
}

# ============================================================================
# 6. CREATE DEPLOYMENT SCRIPTS
# ============================================================================
Write-Step 6 6 "Creating deployment scripts"

# Node deployment script
@'
param([ValidateSet("NODE-01","NODE-02","NODE-03")][string]$Role, [string]$MasterIP="192.168.50.10")
$ErrorActionPreference = "Stop"
Write-Host "SOVEREIGN DEPLOYMENT - $Role" -ForegroundColor Red

# Load Docker images
Get-ChildItem ".\docker-images\*.tar" | ForEach-Object { docker load -i $_.FullName }

# Restore Ollama models
$ollamaDir = "$env:USERPROFILE\.ollama\models"
if (-not (Test-Path $ollamaDir)) { New-Item -ItemType Directory -Path $ollamaDir -Force | Out-Null }
robocopy ".\ollama-models" $ollamaDir /E /MT:4 /R:1 /W:1 | Out-Null

# Copy source
Copy-Item -Path ".\source\sovereign-system" -Destination "C:\sovereign-system" -Recurse -Force

# Start services based on role
Set-Location "C:\sovereign-system"
switch ($Role) {
    "NODE-01" { docker compose up -d boardroom golden-master-api }
    "NODE-02" { docker compose up -d truth-engine ollama }
    "NODE-03" {
        $env:TRUTH_ENGINE_URL = "http://${MasterIP}:5050"
        docker compose up -d executor evidence property
    }
}
Write-Host "DEPLOYED: $Role" -ForegroundColor Green
'@ | Set-Content "$TargetPath\scripts\DEPLOY-NODE.ps1"

# Install prerequisites script
@'
Write-Host "INSTALLING PREREQUISITES" -ForegroundColor Yellow
Start-Process -FilePath ".\installers\python-3.11.9-amd64.exe" -ArgumentList "/quiet InstallAllUsers=1 PrependPath=1" -Wait
Start-Process -FilePath ".\installers\Git-2.43.0-64-bit.exe" -ArgumentList "/VERYSILENT" -Wait
Start-Process -FilePath ".\installers\OllamaSetup.exe" -ArgumentList "/S" -Wait
Write-Host "DONE - Reboot if needed" -ForegroundColor Green
'@ | Set-Content "$TargetPath\scripts\INSTALL-PREREQS.ps1"

# Verification script
@'
param([string]$MasterIP="192.168.50.10", [string]$TruthIP="192.168.50.20")
Write-Host "VERIFYING DEPLOYMENT" -ForegroundColor Yellow
@(
    @{Name="Boardroom"; URL="http://${MasterIP}:3000"},
    @{Name="Truth Engine"; URL="http://${TruthIP}:5050/search?q=test"},
    @{Name="Ollama"; URL="http://${TruthIP}:11434"}
) | ForEach-Object {
    try {
        Invoke-WebRequest -Uri $_.URL -TimeoutSec 5 -ErrorAction Stop | Out-Null
        Write-Host "OK $($_.Name)" -ForegroundColor Green
    } catch {
        Write-Host "FAIL $($_.Name)" -ForegroundColor Red
    }
}
'@ | Set-Content "$TargetPath\scripts\VERIFY.ps1"

Write-OK "Scripts created"

# ============================================================================
# README
# ============================================================================
@"
SOVEREIGN SYSTEM - OFFLINE PACKAGE
==================================
Created: $(Get-Date -Format "yyyy-MM-dd HH:mm")

QUICK START:
1. Run: scripts\INSTALL-PREREQS.ps1
2. Reboot
3. Run: scripts\DEPLOY-NODE.ps1 -Role NODE-01

NODE MAP:
  NODE-01 (192.168.50.10) = Orchestrator
  NODE-02 (192.168.50.20) = Truth Engine
  NODE-03 (192.168.50.30) = Agent Fleet

CONTENTS:
  installers/    - Python, Git, Ollama
  docker-images/ - Pre-built containers
  ollama-models/ - LLM models
  source/        - Source code
  corpus/        - Document corpus
  scripts/       - Deployment automation
"@ | Set-Content "$TargetPath\README.txt"

# ============================================================================
# SUMMARY
# ============================================================================
$size = [Math]::Round((Get-ChildItem -Path $TargetPath -Recurse -File | Measure-Object -Property Length -Sum).Sum / 1GB, 2)

Write-Host "`n=== PACKAGE COMPLETE ===" -ForegroundColor Green
Write-Host "Location: $TargetPath" -ForegroundColor White
Write-Host "Size: $size GB" -ForegroundColor White
Write-Host "`nReady for USB/external transfer`n" -ForegroundColor Yellow
