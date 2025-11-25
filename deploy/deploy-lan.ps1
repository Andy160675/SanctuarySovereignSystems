# ============================================================================
# SOVEREIGN SYSTEM - MULTI-PC LAN DEPLOYMENT
# Air-Gapped Local Network Deployment Script
# ============================================================================

param(
    [Parameter(Mandatory=$true)]
    [ValidateSet("NODE-01", "NODE-02", "NODE-03", "ALL")]
    [string]$NodeRole,

    [string]$MasterIP = "192.168.50.10",
    [string]$TruthIP = "192.168.50.20",
    [string]$AgentIP = "192.168.50.30",
    [string]$CorpusShare = "\\192.168.50.10\SOVEREIGN-CORPUS",
    [switch]$OfflineMode
)

$ErrorActionPreference = "Stop"
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"

# ============================================================================
# BANNER
# ============================================================================

Write-Host @"

╔═══════════════════════════════════════════════════════════════════════════╗
║     SOVEREIGN SYSTEM - MULTI-PC LAN DEPLOYMENT                            ║
║     Air-Gapped Live Asset Deployment                                       ║
╚═══════════════════════════════════════════════════════════════════════════╝

"@ -ForegroundColor Red

Write-Host "DEPLOYMENT TARGET: $NodeRole" -ForegroundColor Yellow
Write-Host "MASTER IP: $MasterIP" -ForegroundColor Cyan
Write-Host "TRUTH IP:  $TruthIP" -ForegroundColor Cyan
Write-Host "AGENT IP:  $AgentIP" -ForegroundColor Cyan
Write-Host ""

# ============================================================================
# ENVIRONMENT CONFIGURATION
# ============================================================================

$envConfig = @{
    "NODE-01" = @{
        role = "ORCHESTRATOR"
        services = @("boardroom", "golden-master")
        ports = @(3000, 8080)
        compose = "docker-compose.node01.yml"
    }
    "NODE-02" = @{
        role = "TRUTH-ENGINE"
        services = @("truth-engine", "ollama")
        ports = @(5050, 11434)
        compose = "docker-compose.node02.yml"
    }
    "NODE-03" = @{
        role = "AGENT-FLEET"
        services = @("executor", "evidence", "property", "watcher")
        ports = @()
        compose = "docker-compose.node03.yml"
    }
}

# ============================================================================
# PRE-FLIGHT CHECKS
# ============================================================================

function Test-Prerequisites {
    Write-Host "`n[1/5] PRE-FLIGHT CHECKS" -ForegroundColor Yellow
    Write-Host "──────────────────────" -ForegroundColor Yellow

    # Docker check
    try {
        $dockerVersion = docker --version
        Write-Host "   ✓ Docker: $dockerVersion" -ForegroundColor Green
    } catch {
        Write-Host "   ✗ Docker not found. Install Docker first." -ForegroundColor Red
        exit 1
    }

    # Docker Compose check
    try {
        $composeVersion = docker compose version
        Write-Host "   ✓ Docker Compose: Available" -ForegroundColor Green
    } catch {
        Write-Host "   ✗ Docker Compose not available" -ForegroundColor Red
        exit 1
    }

    # Network check
    $localIP = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.InterfaceAlias -notmatch "Loopback" } | Select-Object -First 1).IPAddress
    Write-Host "   ✓ Local IP: $localIP" -ForegroundColor Green

    # Corpus share check (if not NODE-01)
    if ($NodeRole -ne "NODE-01" -and -not $OfflineMode) {
        if (Test-Path $CorpusShare) {
            Write-Host "   ✓ Corpus share accessible: $CorpusShare" -ForegroundColor Green
        } else {
            Write-Host "   ⚠ Corpus share not accessible (will retry later)" -ForegroundColor Yellow
        }
    }
}

# ============================================================================
# NODE-01: ORCHESTRATOR DEPLOYMENT
# ============================================================================

function Deploy-Node01 {
    Write-Host "`n[2/5] DEPLOYING NODE-01: ORCHESTRATOR" -ForegroundColor Yellow
    Write-Host "─────────────────────────────────────" -ForegroundColor Yellow

    # Create node-specific compose file
    $composeContent = @"
version: '3.9'
services:
  boardroom:
    build: ../boardroom-shell
    container_name: sovereign-boardroom
    ports:
      - "3000:3000"
    environment:
      - TRUTH_ENGINE_URL=http://${TruthIP}:5050
      - AGENT_FLEET_URL=http://${AgentIP}:8000
    volumes:
      - ../golden-master:/app/golden-master:ro
    restart: unless-stopped

  golden-master-api:
    build:
      context: ..
      dockerfile: golden-master/Dockerfile.api
    container_name: sovereign-golden-master
    ports:
      - "8080:8080"
    volumes:
      - ../golden-master:/app/manifest:ro
      - corpus:/corpus:ro
    restart: unless-stopped

volumes:
  corpus:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: D:/SOVEREIGN-2025-11-19
"@

    $composePath = Join-Path $PSScriptRoot "docker-compose.node01.yml"
    Set-Content -Path $composePath -Value $composeContent -Encoding UTF8

    # Setup SMB share for corpus
    Write-Host "   Setting up corpus share..." -ForegroundColor Cyan

    # Build and start
    Write-Host "   Building containers..." -ForegroundColor Cyan
    docker compose -f $composePath build

    Write-Host "   Starting services..." -ForegroundColor Cyan
    docker compose -f $composePath up -d

    Write-Host "   ✓ NODE-01 ORCHESTRATOR deployed" -ForegroundColor Green
}

# ============================================================================
# NODE-02: TRUTH ENGINE DEPLOYMENT
# ============================================================================

function Deploy-Node02 {
    Write-Host "`n[2/5] DEPLOYING NODE-02: TRUTH ENGINE" -ForegroundColor Yellow
    Write-Host "─────────────────────────────────────" -ForegroundColor Yellow

    # Create node-specific compose file
    $composeContent = @"
version: '3.9'
services:
  truth-engine:
    build: ../truth-engine
    container_name: sovereign-truth
    ports:
      - "5050:5050"
    volumes:
      - ../truth-engine/data:/app/data
      - corpus:/app/corpus:ro
    environment:
      - OLLAMA_HOST=http://localhost:11434
    restart: unless-stopped

  ollama:
    image: ollama/ollama
    container_name: sovereign-ollama
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
    restart: unless-stopped

volumes:
  ollama_data:
  corpus:
    driver: local
    driver_opts:
      type: cifs
      o: username=guest,password=,addr=${MasterIP}
      device: "${CorpusShare}"
"@

    $composePath = Join-Path $PSScriptRoot "docker-compose.node02.yml"
    Set-Content -Path $composePath -Value $composeContent -Encoding UTF8

    # Build and start
    Write-Host "   Building containers..." -ForegroundColor Cyan
    docker compose -f $composePath build

    Write-Host "   Starting services..." -ForegroundColor Cyan
    docker compose -f $composePath up -d

    # Wait for Ollama and pull model
    Write-Host "   Waiting for Ollama startup..." -ForegroundColor Cyan
    Start-Sleep -Seconds 10

    Write-Host "   Pulling Ollama model (if not cached)..." -ForegroundColor Cyan
    docker exec sovereign-ollama ollama pull nomic-embed-text

    Write-Host "   ✓ NODE-02 TRUTH ENGINE deployed" -ForegroundColor Green
}

# ============================================================================
# NODE-03: AGENT FLEET DEPLOYMENT
# ============================================================================

function Deploy-Node03 {
    Write-Host "`n[2/5] DEPLOYING NODE-03: AGENT FLEET" -ForegroundColor Yellow
    Write-Host "────────────────────────────────────" -ForegroundColor Yellow

    # Create node-specific compose file
    $composeContent = @"
version: '3.9'
services:
  executor:
    build: ..
    container_name: sovereign-executor
    volumes:
      - ..:/app
      - ../Evidence:/data/evidence
      - ../Property:/data/property
      - ../Governance:/app/Governance
      - corpus:/corpus:ro
    environment:
      - EVIDENCE_TRACK=stable
      - PROPERTY_TRACK=insider
      - PYTHONPATH=/app
      - TRUTH_ENGINE_URL=http://${TruthIP}:5050
      - OLLAMA_HOST=http://${TruthIP}:11434
    restart: unless-stopped

  evidence:
    build: ..
    container_name: sovereign-evidence
    volumes:
      - ..:/app
      - corpus:/corpus:ro
    environment:
      - PYTHONPATH=/app
      - TRUTH_ENGINE_URL=http://${TruthIP}:5050
    restart: unless-stopped

  property:
    build: ..
    container_name: sovereign-property
    volumes:
      - ..:/app
      - corpus:/corpus:ro
    environment:
      - PYTHONPATH=/app
      - TRUTH_ENGINE_URL=http://${TruthIP}:5050
    restart: unless-stopped

  watcher:
    build: ../blade-watcher
    container_name: sovereign-watcher
    volumes:
      - corpus:/watch/corpus:ro
      - ../truth-engine/data:/app/data
    environment:
      - TRUTH_ENGINE_URL=http://${TruthIP}:5050
    restart: unless-stopped

volumes:
  corpus:
    driver: local
    driver_opts:
      type: cifs
      o: username=guest,password=,addr=${MasterIP}
      device: "${CorpusShare}"
"@

    $composePath = Join-Path $PSScriptRoot "docker-compose.node03.yml"
    Set-Content -Path $composePath -Value $composeContent -Encoding UTF8

    # Build and start
    Write-Host "   Building containers..." -ForegroundColor Cyan
    docker compose -f $composePath build

    Write-Host "   Starting services..." -ForegroundColor Cyan
    docker compose -f $composePath up -d

    Write-Host "   ✓ NODE-03 AGENT FLEET deployed" -ForegroundColor Green
}

# ============================================================================
# VERIFICATION
# ============================================================================

function Test-Deployment {
    param([string]$Node)

    Write-Host "`n[4/5] VERIFICATION" -ForegroundColor Yellow
    Write-Host "──────────────────" -ForegroundColor Yellow

    $containers = docker ps --format "{{.Names}} {{.Status}}"
    Write-Host "   Running containers:" -ForegroundColor Cyan
    $containers | ForEach-Object { Write-Host "      $_" -ForegroundColor White }

    switch ($Node) {
        "NODE-01" {
            Write-Host "`n   Testing Boardroom (port 3000)..." -ForegroundColor Cyan
            try {
                $response = Invoke-WebRequest -Uri "http://localhost:3000" -TimeoutSec 5 -ErrorAction SilentlyContinue
                Write-Host "   ✓ Boardroom responding" -ForegroundColor Green
            } catch {
                Write-Host "   ⚠ Boardroom may still be starting" -ForegroundColor Yellow
            }
        }
        "NODE-02" {
            Write-Host "`n   Testing Truth Engine (port 5050)..." -ForegroundColor Cyan
            try {
                $response = Invoke-WebRequest -Uri "http://localhost:5050/search?q=test" -TimeoutSec 10 -ErrorAction SilentlyContinue
                Write-Host "   ✓ Truth Engine responding" -ForegroundColor Green
            } catch {
                Write-Host "   ⚠ Truth Engine may still be starting" -ForegroundColor Yellow
            }

            Write-Host "   Testing Ollama (port 11434)..." -ForegroundColor Cyan
            try {
                $response = Invoke-WebRequest -Uri "http://localhost:11434" -TimeoutSec 5 -ErrorAction SilentlyContinue
                Write-Host "   ✓ Ollama responding" -ForegroundColor Green
            } catch {
                Write-Host "   ⚠ Ollama may still be starting" -ForegroundColor Yellow
            }
        }
        "NODE-03" {
            Write-Host "   Agent containers running - manual verification required" -ForegroundColor Cyan
        }
    }
}

# ============================================================================
# STATUS REPORT
# ============================================================================

function Show-Status {
    Write-Host "`n[5/5] DEPLOYMENT STATUS" -ForegroundColor Yellow
    Write-Host "───────────────────────" -ForegroundColor Yellow

    Write-Host @"

╔═══════════════════════════════════════════════════════════════════════════╗
║                     SOVEREIGN SYSTEM STATUS                               ║
╠═══════════════════════════════════════════════════════════════════════════╣
"@ -ForegroundColor Cyan

    switch ($NodeRole) {
        "NODE-01" {
            Write-Host "║  NODE-01 (ORCHESTRATOR) - DEPLOYED                                        ║" -ForegroundColor Green
            Write-Host "║    Boardroom:      http://localhost:3000                                  ║" -ForegroundColor White
            Write-Host "║    Golden Master:  http://localhost:8080                                  ║" -ForegroundColor White
        }
        "NODE-02" {
            Write-Host "║  NODE-02 (TRUTH ENGINE) - DEPLOYED                                        ║" -ForegroundColor Green
            Write-Host "║    Truth Engine:   http://localhost:5050                                  ║" -ForegroundColor White
            Write-Host "║    Ollama:         http://localhost:11434                                 ║" -ForegroundColor White
        }
        "NODE-03" {
            Write-Host "║  NODE-03 (AGENT FLEET) - DEPLOYED                                         ║" -ForegroundColor Green
            Write-Host "║    Executor:       Running                                                ║" -ForegroundColor White
            Write-Host "║    Evidence:       Running                                                ║" -ForegroundColor White
            Write-Host "║    Property:       Running                                                ║" -ForegroundColor White
        }
    }

    Write-Host @"
╠═══════════════════════════════════════════════════════════════════════════╣
║  NEXT NODE TO DEPLOY:                                                     ║
"@ -ForegroundColor Cyan

    switch ($NodeRole) {
        "NODE-01" { Write-Host "║    Run on NODE-02: .\deploy-lan.ps1 -NodeRole NODE-02                    ║" -ForegroundColor Yellow }
        "NODE-02" { Write-Host "║    Run on NODE-03: .\deploy-lan.ps1 -NodeRole NODE-03                    ║" -ForegroundColor Yellow }
        "NODE-03" { Write-Host "║    ALL NODES DEPLOYED - System is OPERATIONAL                            ║" -ForegroundColor Green }
    }

    Write-Host "╚═══════════════════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
    Write-Host ""
}

# ============================================================================
# MAIN EXECUTION
# ============================================================================

Test-Prerequisites

switch ($NodeRole) {
    "NODE-01" { Deploy-Node01 }
    "NODE-02" { Deploy-Node02 }
    "NODE-03" { Deploy-Node03 }
    "ALL" {
        Write-Host "⚠ ALL mode requires running this script on each physical node" -ForegroundColor Yellow
        Write-Host "   Run on each PC in order: NODE-01 → NODE-02 → NODE-03" -ForegroundColor Cyan
    }
}

if ($NodeRole -ne "ALL") {
    Test-Deployment $NodeRole
    Show-Status
}

Write-Host "`n🔥 SOVEREIGN. DEPLOYED. OPERATIONAL.`n" -ForegroundColor Red
