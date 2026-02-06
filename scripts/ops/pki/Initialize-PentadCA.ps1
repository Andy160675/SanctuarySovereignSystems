# scripts/ops/pki/Initialize-PentadCA.ps1
param(
    [string]$PkiDir = "evidence_store\pki",
    [string]$ConfigDir = "config\pki"
)

$ErrorActionPreference = "Stop"

$openssl = "C:\Program Files\Git\usr\bin\openssl.exe"

if (-not (Test-Path $PkiDir)) { New-Item -ItemType Directory -Path $PkiDir -Force }

Write-Host "--- Generating Pentad Root CA ---" -ForegroundColor Cyan

# 1. Root CA
$rootKey = Join-Path $PkiDir "root-ca.key"
$rootCert = Join-Path $PkiDir "root-ca.crt"
$rootConf = Join-Path $ConfigDir "root-ca.conf"

if (-not (Test-Path $rootKey)) {
    & $openssl genrsa -out $rootKey 4096
}

if (-not (Test-Path $rootCert)) {
    & $openssl req -new -x509 -days 7300 -key $rootKey -out $rootCert -config $rootConf
}

Write-Host "--- Generating Intermediate CAs for Heads ---" -ForegroundColor Cyan

$heads = @("pc-a", "pc-b", "pc-c", "pc-d", "pc-e")

foreach ($head in $heads) {
    $headCert = Join-Path $PkiDir "$head-ca.crt"
    if (Test-Path $headCert) {
        Write-Host "  [SKIP] $head Intermediate CA already exists." -ForegroundColor Gray
        continue
    }
    Write-Host "Processing $head..." -ForegroundColor Yellow
    
    $headKey = Join-Path $PkiDir "$head-ca.key"
    $headCsr = Join-Path $PkiDir "$head-ca.csr"
    $headCert = Join-Path $PkiDir "$head-ca.crt"
    
    if (-not (Test-Path $headKey)) {
        & $openssl genrsa -out $headKey 4096
    }
    
    $subj = "/C=SO/O=Sovereign Systems/OU=Pentad/CN=$head Intermediate CA"
    & $openssl req -new -key $headKey -out $headCsr -subj $subj
    
    # Extension file for signing intermediate CA
    $extFile = Join-Path $PkiDir "$head-ca.ext"
    "basicConstraints=critical,CA:true`nkeyUsage=critical,keyCertSign,cRLSign" | Out-File -FilePath $extFile -Encoding ascii
    
    & $openssl x509 -req -days 3650 -in $headCsr -CA $rootCert -CAkey $rootKey -CAcreateserial -out $headCert -extfile $extFile
    
    Remove-Item $extFile
}

Write-Host "--- PKI Initialization Complete ---" -ForegroundColor Green
