# scripts/ops/pki/Generate-HeadCertificates.ps1
param(
    [string]$PkiDir = "evidence_store\pki"
)

$ErrorActionPreference = "Stop"

$heads = @(
    @{ id = "pc-a"; role = "constitutional"; ip = "10.0.100.11" },
    @{ id = "pc-b"; role = "orchestration"; ip = "10.0.100.12" },
    @{ id = "pc-c"; role = "verification"; ip = "10.0.100.13" },
    @{ id = "pc-d"; role = "analytics"; ip = "10.0.100.14" },
    @{ id = "pc-e"; role = "safety"; ip = "10.0.100.15" }
)

Write-Host "--- Generating Pentad Head Certificates ---" -ForegroundColor Cyan

foreach ($head in $heads) {
    $bundlePath = Join-Path $PkiDir "$($head.id).pem"
    if (Test-Path $bundlePath) {
        Write-Host "  [SKIP] $($head.id) cert already exists: $bundlePath" -ForegroundColor Gray
        continue
    }
    
    Write-Host "Generating cert for $($head.id) ($($head.role))..." -ForegroundColor Yellow
    
    $cmd = @"
from core.transport.certificate_generator import HeadCertificateGenerator
from pathlib import Path
import os

gen = HeadCertificateGenerator(
    head_id='$($head.id)',
    role='$($head.role)',
    ip_address='$($head.ip)',
    pki_dir=Path('$($PkiDir.Replace('\','\\'))')
)
res = gen.generate_certificate()
print('Generated: ' + str(res.bundle))
"@

    python -c $cmd
}

Write-Host "--- Head Certificate Generation Complete ---" -ForegroundColor Green
