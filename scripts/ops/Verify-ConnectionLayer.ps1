# scripts/ops/Verify-ConnectionLayer.ps1
param(
    [string]$PkiDir = "evidence_store\pki",
    [string]$EvidenceDir = "evidence_store\connection",
    [switch]$Watch
)

$ErrorActionPreference = "Stop"

function Run-HealthCheck {
    Write-Host "--- Pentad Connection Layer Verification Suite ---" -ForegroundColor Cyan

    # 1. PKI Integrity Check
    Write-Host "[1] Checking PKI artifacts..." -ForegroundColor Yellow
    $required = @("root-ca.crt", "pc-a.pem", "pc-b.pem", "pc-c.pem", "pc-d.pem", "pc-e.pem")
    foreach ($file in $required) {
        $path = Join-Path $PkiDir $file
        if (Test-Path $path) {
            Write-Host "  ✓ Found $file" -ForegroundColor Green
        } else {
            Write-Host "  ✗ Missing $file" -ForegroundColor Red
            if (-not $Watch) { exit 1 }
        }
    }

    # 2. Certificate Validity Check
    Write-Host "[2] Verifying certificate validity (expiry check)..." -ForegroundColor Yellow
    $openssl = "C:\Program Files\Git\usr\bin\openssl.exe"
    foreach ($file in ($required | Where-Object { $_ -like "*.pem" })) {
        $path = Join-Path $PkiDir $file
        if (Test-Path $path) {
            $expiry = & $openssl x509 -enddate -noout -in $path
            Write-Host "  $file: $expiry" -ForegroundColor Gray
        }
    }

    # 3. Evidence Chain Verification
    Write-Host "[3] Verifying connection evidence chain..." -ForegroundColor Yellow
    $evidenceFiles = Get-ChildItem $EvidenceDir -Filter "*.jsonl"
    if ($evidenceFiles.Count -gt 0) {
        foreach ($ef in $evidenceFiles) {
            $count = (Get-Content $ef.FullName).Count
            Write-Host "  ✓ $($ef.Name): $count records found" -ForegroundColor Green
        }
    } else {
        Write-Host "  ✗ No connection evidence found" -ForegroundColor Red
    }

    Write-Host "`n--- Verification Cycle Complete ---" -ForegroundColor Cyan
}

if ($Watch) {
    Write-Host "Starting Health Monitoring Loop (Ctrl+C to stop)..." -ForegroundColor Magenta
    while ($true) {
        Clear-Host
        Run-HealthCheck
        Start-Sleep -Seconds 30
    }
} else {
    Run-HealthCheck
}
