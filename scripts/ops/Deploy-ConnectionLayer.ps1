# scripts/ops/Deploy-ConnectionLayer.ps1
param(
    [string]$PkiDir = "evidence_store\pki",
    [string]$EvidenceDir = "evidence_store\connection"
)

$ErrorActionPreference = "Stop"

Write-Host "--- Starting Pentad Connection Layer Deployment ---" -ForegroundColor Cyan

# 1. Initialize PKI infrastructure
Write-Host "[Step 1] Initializing Root and Intermediate CAs..." -ForegroundColor Yellow
powershell -ExecutionPolicy Bypass -File scripts\ops\pki\Initialize-PentadCA.ps1

# 2. Generate Head Certificates
Write-Host "[Step 2] Generating head certificates for all nodes..." -ForegroundColor Yellow
powershell -ExecutionPolicy Bypass -File scripts\ops\pki\Generate-HeadCertificates.ps1

# 3. Simulate Distribution
Write-Host "[Step 3] Simulating certificate distribution and lock-down..." -ForegroundColor Yellow
$heads = @("pc-a", "pc-b", "pc-c", "pc-d", "pc-e")
foreach ($head in $heads) {
    Write-Host "  Locking down certs for $head..."
    $pem = Join-Path $PkiDir "$head.pem"
    if (Test-Path $pem) {
        Write-Host "  OK: $head.pem ready" -ForegroundColor Green
    }
}

# 4. Verify Local Loopback
Write-Host "[Step 4] Running local loopback verification test..." -ForegroundColor Yellow
$env:PYTHONPATH = "."
python scripts/ops/test_connection_loopback.py

Write-Host "--- Connection Layer Deployment Complete ---" -ForegroundColor Cyan
Write-Host "Evidence artifacts available in $EvidenceDir" -ForegroundColor Gray
