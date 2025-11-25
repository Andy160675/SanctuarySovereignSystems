# ============================================================================
# SOVEREIGN SYSTEM - USB DEPLOYMENT PACKAGE BUILDER
# Creates offline deployment package for air-gapped transfer
# ============================================================================

param(
    [string]$TargetDrive = "E:",
    [switch]$IncludeOllamaModels,
    [switch]$IncludeDockerImages,
    [switch]$VerifyOnly
)

$ErrorActionPreference = "Stop"
$timestamp = Get-Date -Format "yyyyMMdd"
$packageName = "SOVEREIGN-DEPLOY-$timestamp"

Write-Host @"

╔═══════════════════════════════════════════════════════════════════════════╗
║     SOVEREIGN SYSTEM - USB PACKAGE BUILDER                                ║
║     Air-Gapped Deployment Package                                          ║
╚═══════════════════════════════════════════════════════════════════════════╝

"@ -ForegroundColor Red

# ============================================================================
# PACKAGE STRUCTURE
# ============================================================================

$packageStructure = @{
    root = @(
        "DEPLOY-README.txt",
        "deploy-lan.ps1",
        "verify-package.ps1"
    )
    node01 = @(
        "docker-compose.node01.yml",
        "boardroom-shell/",
        "golden-master/"
    )
    node02 = @(
        "docker-compose.node02.yml",
        "truth-engine/"
    )
    node03 = @(
        "docker-compose.node03.yml",
        "src/",
        "blade-watcher/"
    )
    corpus = @(
        "SOVEREIGN-CORPUS/"
    )
    docker_images = @(
        "images/"
    )
}

# ============================================================================
# BUILD PACKAGE
# ============================================================================

function Build-Package {
    $packagePath = Join-Path $TargetDrive $packageName

    Write-Host "[1/5] Creating package structure at $packagePath" -ForegroundColor Yellow

    New-Item -ItemType Directory -Path $packagePath -Force | Out-Null
    New-Item -ItemType Directory -Path "$packagePath\node01" -Force | Out-Null
    New-Item -ItemType Directory -Path "$packagePath\node02" -Force | Out-Null
    New-Item -ItemType Directory -Path "$packagePath\node03" -Force | Out-Null
    New-Item -ItemType Directory -Path "$packagePath\corpus" -Force | Out-Null
    New-Item -ItemType Directory -Path "$packagePath\images" -Force | Out-Null

    # Copy deployment scripts
    Write-Host "[2/5] Copying deployment scripts..." -ForegroundColor Yellow
    Copy-Item -Path "$PSScriptRoot\deploy-lan.ps1" -Destination $packagePath
    Copy-Item -Path "$PSScriptRoot\LAN_DEPLOYMENT_TOPOLOGY.md" -Destination $packagePath

    # Copy source directories
    Write-Host "[3/5] Copying source code..." -ForegroundColor Yellow

    $sourceBase = "C:\sovereign-system"

    # NODE-01 files
    if (Test-Path "$sourceBase\boardroom-shell") {
        Copy-Item -Path "$sourceBase\boardroom-shell" -Destination "$packagePath\node01\" -Recurse
    }
    if (Test-Path "$sourceBase\golden-master") {
        Copy-Item -Path "$sourceBase\golden-master" -Destination "$packagePath\node01\" -Recurse
    }

    # NODE-02 files
    if (Test-Path "$sourceBase\truth-engine") {
        Copy-Item -Path "$sourceBase\truth-engine" -Destination "$packagePath\node02\" -Recurse
    }

    # NODE-03 files
    if (Test-Path "$sourceBase\src") {
        Copy-Item -Path "$sourceBase\src" -Destination "$packagePath\node03\" -Recurse
    }
    if (Test-Path "$sourceBase\blade-watcher") {
        Copy-Item -Path "$sourceBase\blade-watcher" -Destination "$packagePath\node03\" -Recurse
    }

    # Export Docker images if requested
    if ($IncludeDockerImages) {
        Write-Host "[3b/5] Exporting Docker images (this takes a while)..." -ForegroundColor Yellow

        $images = @(
            "ollama/ollama:latest"
        )

        foreach ($image in $images) {
            $safeName = $image -replace "[:/]", "_"
            $imagePath = Join-Path "$packagePath\images" "$safeName.tar"
            Write-Host "   Exporting $image..." -ForegroundColor Cyan
            docker save -o $imagePath $image
        }
    }

    # Copy corpus
    Write-Host "[4/5] Copying corpus..." -ForegroundColor Yellow
    $corpusSource = "D:\SOVEREIGN-2025-11-19"
    if (Test-Path $corpusSource) {
        Write-Host "   Copying from $corpusSource (this may take a while)..." -ForegroundColor Cyan
        robocopy $corpusSource "$packagePath\corpus" /E /MT:8 /R:1 /W:1 | Out-Null
    } else {
        Write-Host "   ⚠ Corpus not found at $corpusSource" -ForegroundColor Yellow
    }

    # Create deployment readme
    $readmeContent = @"
═══════════════════════════════════════════════════════════════════════════
                    SOVEREIGN SYSTEM - DEPLOYMENT PACKAGE
                    Air-Gapped Multi-PC LAN Deployment
═══════════════════════════════════════════════════════════════════════════

Package Created: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")

DEPLOYMENT ORDER:
─────────────────
1. NODE-01 (192.168.50.10) - ORCHESTRATOR
   > Copy node01\ to C:\sovereign-system\
   > Run: .\deploy-lan.ps1 -NodeRole NODE-01

2. NODE-02 (192.168.50.20) - TRUTH ENGINE
   > Copy node02\ to C:\sovereign-system\
   > Run: .\deploy-lan.ps1 -NodeRole NODE-02

3. NODE-03 (192.168.50.30) - AGENT FLEET
   > Copy node03\ to C:\sovereign-system\
   > Run: .\deploy-lan.ps1 -NodeRole NODE-03

CORPUS SETUP:
─────────────
Copy corpus\ to D:\SOVEREIGN-2025-11-19 on NODE-01
Share as: \\192.168.50.10\SOVEREIGN-CORPUS (read-only)

DOCKER IMAGES (if included):
────────────────────────────
Load with: docker load -i images\<image>.tar

VERIFICATION:
─────────────
After all nodes deployed, run verify-package.ps1 on any node.

═══════════════════════════════════════════════════════════════════════════
                         SOVEREIGN. OPERATIONAL.
═══════════════════════════════════════════════════════════════════════════
"@

    Set-Content -Path "$packagePath\DEPLOY-README.txt" -Value $readmeContent -Encoding UTF8

    # Create verification script
    $verifyContent = @'
# Verification script for deployed nodes
param([string]$MasterIP = "192.168.50.10", [string]$TruthIP = "192.168.50.20")

Write-Host "`nSOVEREIGN SYSTEM - DEPLOYMENT VERIFICATION" -ForegroundColor Yellow
Write-Host "──────────────────────────────────────────`n" -ForegroundColor Yellow

$endpoints = @(
    @{ Name = "Boardroom"; URL = "http://${MasterIP}:3000"; Node = "NODE-01" }
    @{ Name = "Golden Master"; URL = "http://${MasterIP}:8080"; Node = "NODE-01" }
    @{ Name = "Truth Engine"; URL = "http://${TruthIP}:5050/search?q=test"; Node = "NODE-02" }
    @{ Name = "Ollama"; URL = "http://${TruthIP}:11434"; Node = "NODE-02" }
)

foreach ($ep in $endpoints) {
    try {
        $response = Invoke-WebRequest -Uri $ep.URL -TimeoutSec 5 -ErrorAction Stop
        Write-Host "✓ $($ep.Node) - $($ep.Name): ONLINE" -ForegroundColor Green
    } catch {
        Write-Host "✗ $($ep.Node) - $($ep.Name): OFFLINE" -ForegroundColor Red
    }
}

Write-Host "`n──────────────────────────────────────────" -ForegroundColor Yellow
Write-Host "Verification complete.`n" -ForegroundColor Yellow
'@

    Set-Content -Path "$packagePath\verify-package.ps1" -Value $verifyContent -Encoding UTF8

    # Calculate package size
    Write-Host "[5/5] Finalizing package..." -ForegroundColor Yellow
    $packageSize = (Get-ChildItem -Path $packagePath -Recurse | Measure-Object -Property Length -Sum).Sum / 1GB

    Write-Host @"

╔═══════════════════════════════════════════════════════════════════════════╗
║                      PACKAGE BUILD COMPLETE                               ║
╠═══════════════════════════════════════════════════════════════════════════╣
║  Location: $packagePath
║  Size:     $([Math]::Round($packageSize, 2)) GB
╠═══════════════════════════════════════════════════════════════════════════╣
║  CONTENTS:                                                                ║
║    /node01     - Orchestrator files (Boardroom, Golden Master)           ║
║    /node02     - Truth Engine files (txtai, Ollama config)               ║
║    /node03     - Agent Fleet files (Executor, Evidence, Property)        ║
║    /corpus     - Document corpus (read-only mount)                       ║
║    /images     - Pre-built Docker images (if requested)                  ║
╚═══════════════════════════════════════════════════════════════════════════╝

"@ -ForegroundColor Cyan

    Write-Host "Transfer this USB to each node and follow DEPLOY-README.txt" -ForegroundColor Yellow
    Write-Host ""
}

# ============================================================================
# MAIN
# ============================================================================

if ($VerifyOnly) {
    Write-Host "Verification mode - checking target drive..." -ForegroundColor Yellow
    if (Test-Path $TargetDrive) {
        $space = (Get-PSDrive ($TargetDrive -replace ":","")).Free / 1GB
        Write-Host "   Drive $TargetDrive available: $([Math]::Round($space, 2)) GB free" -ForegroundColor Green
    } else {
        Write-Host "   Drive $TargetDrive not found" -ForegroundColor Red
    }
} else {
    Build-Package
}
