# Create-Sovereign-Bundle.ps1
# The Blade of Truth - Bundle & Download Engine
# MISSION: Gather all proof artifacts, canon, and core scripts into a sealed download package.

$ErrorActionPreference = "Stop"
$repoRoot = (Get-Location).Path
$ts = (Get-Date).ToUniversalTime().ToString("yyyyMMddTHHmmssZ")
$bundleDir = Join-Path $repoRoot "exports\bundle_$ts"
New-Item -ItemType Directory -Force -Path $bundleDir | Out-Null

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  THE BLADE OF TRUTH - BUNDLE CREATOR" -ForegroundColor Cyan
Write-Host "  Path: $bundleDir" -ForegroundColor Gray
Write-Host "============================================================" -ForegroundColor Cyan

# 1. Gather Canon & Codex
Write-Host "[1/5] Gathering Canon & Codex..." -ForegroundColor Yellow
$canonDir = Join-Path $bundleDir "CANON"
$codexDir = Join-Path $bundleDir "Codex"
Copy-Item "CANON" -Destination $canonDir -Recurse -Force
Copy-Item "Codex" -Destination $codexDir -Recurse -Force

# 2. Gather Ledgers
Write-Host "[2/5] Gathering Ledgers..." -ForegroundColor Yellow
$ledgerDir = Join-Path $bundleDir "Ledgers"
New-Item -ItemType Directory -Force -Path $ledgerDir | Out-Null
if (Test-Path "Governance/ledger/decisions.jsonl") { Copy-Item "Governance/ledger/decisions.jsonl" -Destination $ledgerDir }
if (Test-Path "governance/ledger/best_practices.jsonl") { Copy-Item "governance/ledger/best_practices.jsonl" -Destination $ledgerDir }
if (Test-Path "governance/ledger/sovereign_events.jsonl") { Copy-Item "governance/ledger/sovereign_events.jsonl" -Destination $ledgerDir }

# 3. Gather Evidence & Validation
Write-Host "[3/5] Gathering Latest Evidence..." -ForegroundColor Yellow
$evDir = Join-Path $bundleDir "Evidence"
New-Item -ItemType Directory -Force -Path $evDir | Out-Null
# Get the most recent validation run
$latestVal = Get-ChildItem "validation" -Directory | Sort-Object LastWriteTime -Descending | Select-Object -First 1
if ($latestVal) {
    Copy-Item $latestVal.FullName -Destination (Join-Path $evDir $latestVal.Name) -Recurse -Force
}
if (Test-Path "evidence/visuals") { Copy-Item "evidence/visuals" -Destination $evDir -Recurse -Force }
if (Test-Path "evidence/proof_cases") { Copy-Item "evidence/proof_cases" -Destination $evDir -Recurse -Force }

# 4. Create Bundle Manifest
Write-Host "[4/5] Sealing Bundle (SHA256 Manifest)..." -ForegroundColor Yellow
$manifestLines = @()
Get-ChildItem $bundleDir -Recurse -File | ForEach-Object {
    $hash = (Get-FileHash $_.FullName -Algorithm SHA256).Hash.ToLower()
    $rel = $_.FullName.Replace($bundleDir, "").TrimStart("\")
    $manifestLines += "$hash  $rel"
}
$manifestPath = Join-Path $bundleDir "BUNDLE_MANIFEST_SHA256.txt"
$manifestLines | Set-Content -Path $manifestPath -Encoding UTF8

# 5. Create Zip Archive
Write-Host "[5/5] Creating Zip Archive..." -ForegroundColor Yellow
$zipPath = Join-Path $repoRoot "exports\Sovereign_Bundle_$ts.zip"
Compress-Archive -Path "$bundleDir\*" -DestinationPath $zipPath -Force

Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host "  BUNDLE COMPLETE" -ForegroundColor Green
Write-Host "  Zip: $zipPath" -ForegroundColor Cyan
Write-Host "  Size: $((Get-Item $zipPath).Length / 1KB) KB" -ForegroundColor Gray
Write-Host "============================================================" -ForegroundColor Green
