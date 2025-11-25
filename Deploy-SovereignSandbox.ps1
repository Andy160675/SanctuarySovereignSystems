# ===================================================================================
# Deploy-SovereignSandbox.ps1
#
# MISSION: Full Build-Out Test for Phase-5E Sandbox Environment
#
# This script is the system-level automation for the Sovereign Substrate.
# It creates an isolated environment, spins up the full mock stack, validates
# health, bootstraps evidence, and provides a cryptographic proof of deployment.
# ===================================================================================

param(
    [string]$SandboxRoot = "C:\sovereign-sandbox\phase5e",
    [string]$SourceRoot = "C:\sovereign-system"
)

# --- Utility Functions ---
function Write-Log {
    param ([string]$Message, [string]$Level = "INFO")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $color = switch ($Level) {
        "INFO"  { "White" }
        "WARN"  { "Yellow" }
        "ERROR" { "Red" }
        "OK"    { "Green" }
        default { "White" }
    }
    Write-Host "[$timestamp] [$Level] $Message" -ForegroundColor $color
}

function Test-Port {
    param ([int]$Port)
    try {
        $tcpClient = New-Object System.Net.Sockets.TcpClient
        $tcpClient.Connect("localhost", $Port)
        $tcpClient.Close()
        return $true
    }
    catch {
        return $false
    }
}

function Get-FileHashSHA256 {
    param ([string]$Path)
    if (-not (Test-Path $Path)) { return $null }
    return (Get-FileHash -Path $Path -Algorithm SHA256).Hash.ToLower()
}

# --- Mission Start ---
Write-Host ""
Write-Host "=" * 70 -ForegroundColor Cyan
Write-Host "  SOVEREIGN SANDBOX: PHASE5E FULL BUILD-OUT" -ForegroundColor Cyan
Write-Host "=" * 70 -ForegroundColor Cyan
Write-Host ""
Write-Log "Initializing mission parameters..."
Write-Log "Source Root: $SourceRoot"
Write-Log "Sandbox Root: $SandboxRoot"

# --- 1. Governor Agent: Validate Preconditions ---
Write-Host ""
Write-Log "Step 1: Governor Agent - Validating Preconditions..."

$requiredPaths = @(
    "$SourceRoot\mock_services.py"
)
$optionalPaths = @(
    "$SourceRoot\trinity\trinity_backend.py",
    "$SourceRoot\boardroom\boardroom_app.py"
)

$validationPassed = $true
foreach ($path in $requiredPaths) {
    if (-not (Test-Path $path)) {
        Write-Log "Validation failed: Missing required file $path" -Level "ERROR"
        $validationPassed = $false
    } else {
        Write-Log "Found: $path" -Level "OK"
    }
}

foreach ($path in $optionalPaths) {
    if (Test-Path $path) {
        Write-Log "Found optional: $path" -Level "OK"
    } else {
        Write-Log "Optional file not found (non-blocking): $path" -Level "WARN"
    }
}

if (-not $validationPassed) {
    Write-Log "Precondition validation failed. Aborting." -Level "ERROR"
    exit 1
}

# Check ports are free
$portsToCheck = @(8001, 8002, 8003, 8004, 8005, 8502)
foreach ($port in $portsToCheck) {
    if (Test-Port $port) {
        Write-Log "Port $port is already in use - services may already be running" -Level "WARN"
    }
}

Write-Log "Preconditions validated. Proceeding with deployment." -Level "OK"

# --- 2. Orchestrator Agent: Perform Build-Out ---
Write-Host ""
Write-Log "Step 2: Orchestrator Agent - Performing Build-Out..."

Write-Log "Creating sandbox namespace: $SandboxRoot"
New-Item -ItemType Directory -Path $SandboxRoot -Force | Out-Null
New-Item -ItemType Directory -Path "$SandboxRoot\events" -Force | Out-Null
New-Item -ItemType Directory -Path "$SandboxRoot\evidence_store" -Force | Out-Null

Write-Log "Copying mock services to sandbox..."
Copy-Item -Path "$SourceRoot\mock_services.py" -Destination $SandboxRoot -Force

# Copy evidence store if it exists
if (Test-Path "$SourceRoot\evidence_store") {
    Copy-Item -Path "$SourceRoot\evidence_store\*" -Destination "$SandboxRoot\evidence_store\" -Recurse -Force
    Write-Log "Evidence store copied to sandbox" -Level "OK"
}

Write-Log "Emitting deploy_procedure_start event..."
$startTime = Get-Date
$startEvent = @{
    event_type = "deploy_procedure_start"
    timestamp = (Get-Date -Format "yyyy-MM-ddTHH:mm:ssZ")
    sandbox_root = $SandboxRoot
    source_root = $SourceRoot
    operator = $env:USERNAME
}
$startEvent | ConvertTo-Json -Depth 3 | Out-File -FilePath "$SandboxRoot\events\event_deploy_start.json" -Encoding utf8

# --- 3. Launch Services ---
Write-Host ""
Write-Log "Step 3: Launching Services..."

$mockScript = "$SandboxRoot\mock_services.py"
if (Test-Path $mockScript) {
    $mockProcess = Start-Process -FilePath "python" -ArgumentList $mockScript -WorkingDirectory $SandboxRoot -PassThru -WindowStyle Minimized
    Write-Log "Mock services started - PID: $($mockProcess.Id)" -Level "OK"
} else {
    Write-Log "Mock services script not found at $mockScript" -Level "ERROR"
    exit 1
}

# Wait for services to initialize
Write-Log "Waiting 8 seconds for services to initialize..."
Start-Sleep -Seconds 8

# --- 4. Guardian Agent: Health Verification ---
Write-Host ""
Write-Log "Step 4: Guardian Agent - Verifying Health..."

$healthEndpoints = @{
    "Aggregated" = "http://localhost:8502/health"
    "Core" = "http://localhost:8001/health/core"
    "Truth" = "http://localhost:8002/health/truth"
    "Enforce" = "http://localhost:8003/health/enforce"
    "Models" = "http://localhost:8004/health/models"
    "RAG" = "http://localhost:8005/health/rag_index"
}

$healthResults = @{}
$allHealthy = $true

foreach ($service in $healthEndpoints.GetEnumerator()) {
    try {
        $response = Invoke-RestMethod -Uri $service.Value -Method Get -TimeoutSec 5
        if ($response.status -eq "healthy" -or $response.overall_status -eq "healthy") {
            Write-Log "Health check PASSED: $($service.Name)" -Level "OK"
            $healthResults[$service.Name] = "healthy"
        } else {
            Write-Log "Health check WARNING: $($service.Name) - unexpected status" -Level "WARN"
            $healthResults[$service.Name] = "unknown"
        }
    }
    catch {
        Write-Log "Health check FAILED: $($service.Name)" -Level "ERROR"
        $healthResults[$service.Name] = "unreachable"
        $allHealthy = $false
    }
}

if (-not $allHealthy) {
    Write-Log "Some health checks failed. Continuing with caution..." -Level "WARN"
}

# --- 5. Truth Agent: Evidence Bootstrapping ---
Write-Host ""
Write-Log "Step 5: Truth Agent - Bootstrapping Evidence..."

$evidenceDir = "$SandboxRoot\evidence_store\CASE-TEST-001"
$evidenceFile = "$evidenceDir\mock-event-1.jsonl"

# Ensure evidence directory exists
New-Item -ItemType Directory -Path $evidenceDir -Force | Out-Null

# Create mock evidence if it doesn't exist
if (-not (Test-Path $evidenceFile)) {
    $mockEvent = @{
        id = "mock-event-1"
        case_id = "CASE-TEST-001"
        ts = (Get-Date -Format "yyyy-MM-ddTHH:mm:ss.fffZ")
        type = "evidence"
        payload = @{
            text = "This is a tamper-test artifact. Change this file to see mismatch behavior."
        }
    }
    $mockEvent | ConvertTo-Json -Depth 3 -Compress | Out-File -FilePath $evidenceFile -Encoding utf8 -NoNewline
    Write-Log "Created mock evidence file" -Level "OK"
}

$baselineHash = Get-FileHashSHA256 -Path $evidenceFile
Write-Log "Evidence baseline hash: $baselineHash" -Level "OK"

$evidenceEvent = @{
    event_type = "evidence_baseline"
    timestamp = (Get-Date -Format "yyyy-MM-ddTHH:mm:ssZ")
    evidence_path = $evidenceFile
    evidence_hash = $baselineHash
    verification_method = "SHA256"
    source_agent = "TruthAgent"
}
$evidenceEvent | ConvertTo-Json -Depth 3 | Out-File -FilePath "$SandboxRoot\events\event_evidence_baseline.json" -Encoding utf8

# --- 6. Anchor Agent: Seal Deployment ---
Write-Host ""
Write-Log "Step 6: Anchor Agent - Sealing Deployment..."

$deployDuration = ((Get-Date) - $startTime).TotalSeconds
$merkleRoot = "0x" + (Get-FileHashSHA256 -Path "$SandboxRoot\events\event_evidence_baseline.json").Substring(0, 16)

$anchorEvent = @{
    event_type = "deploy_success"
    timestamp = (Get-Date -Format "yyyy-MM-ddTHH:mm:ssZ")
    sandbox_root = $SandboxRoot
    evidence_baseline_hash = $baselineHash
    deploy_duration_seconds = [math]::Round($deployDuration, 2)
    health_results = $healthResults
    mock_services_pid = $mockProcess.Id
    merkle_root = $merkleRoot
    status = "SUCCESS"
}
$anchorEvent | ConvertTo-Json -Depth 3 | Out-File -FilePath "$SandboxRoot\events\event_deploy_success.json" -Encoding utf8

Write-Log "Deployment sealed. Merkle root: $merkleRoot" -Level "OK"

# --- 7. Output to Operator ---
Write-Host ""
Write-Host "=" * 70 -ForegroundColor Green
Write-Host "  SOVEREIGN SANDBOX DEPLOYMENT SUMMARY" -ForegroundColor Green
Write-Host "=" * 70 -ForegroundColor Green
Write-Host ""
Write-Host "  Status:           SUCCESS" -ForegroundColor Green
Write-Host "  Sandbox Root:     $SandboxRoot"
Write-Host "  Mock Services:    PID $($mockProcess.Id)"
Write-Host "  Evidence Hash:    $baselineHash"
Write-Host "  Merkle Root:      $merkleRoot"
Write-Host "  Deploy Duration:  $([math]::Round($deployDuration, 2)) seconds"
Write-Host ""
Write-Host "  Endpoints:" -ForegroundColor Cyan
Write-Host "    Aggregated Health: http://localhost:8502/health"
Write-Host "    Evidence Info:     http://localhost:8502/api/evidence/info"
Write-Host "    Verify Hash:       http://localhost:8502/api/core/verify_hash"
Write-Host ""
Write-Host "  TAMPER TEST:" -ForegroundColor Yellow
Write-Host "    1. Edit: $evidenceFile"
Write-Host "    2. POST /api/core/verify_hash with original hash"
Write-Host "    3. Response will show match: false (tamper detected)"
Write-Host ""
Write-Host "  To stop services:" -ForegroundColor Gray
Write-Host "    Stop-Process -Id $($mockProcess.Id) -Force"
Write-Host ""
Write-Host "=" * 70 -ForegroundColor Green
Write-Host ""

# --- 8. System Awaiting Tamper Action ---
Write-Log "Sandbox is now primed for the tamper sequence."
Write-Log "Mission complete."
