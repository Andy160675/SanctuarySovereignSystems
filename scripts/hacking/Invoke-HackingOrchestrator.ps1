# scripts/hacking/Invoke-HackingOrchestrator.ps1
# MISSION: Orchestrate the Hacking Solution & Intel Ingestion

param(
    [string]$NodeId = $env:COMPUTERNAME,
    [switch]$ScanOnly,
    [switch]$IngestOnly
)

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Resolve-Path "$ScriptDir\..\.."
$venvPy = "$RepoRoot\.venv\Scripts\python.exe"
if (-not (Test-Path $venvPy)) { $venvPy = "python" }

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  THE BLADE OF TRUTH - HACKING ORCHESTRATOR" -ForegroundColor Cyan
Write-Host "  Operational Hacking Solution & Intel Suite" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# 1. External Intel Ingestion
if (-not $ScanOnly) {
    Write-Host "[1/2] Ingesting Elite Hacking Intelligence..." -ForegroundColor Yellow
    & $venvPy "$RepoRoot\scripts\learning\ingest_hacking_intel.py" --seed
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  [OK] Intelligence ingested and codified." -ForegroundColor Green
    } else {
        Write-Host "  [FAIL] Intel ingestion failed." -ForegroundColor Red
    }
} else {
    Write-Host "[SKIP] Intel ingestion skipped (--ScanOnly)" -ForegroundColor Gray
}

# 2. Sovereign Security Scanner (The Hacking Solution)
if (-not $IngestOnly) {
    Write-Host "[2/2] Running Sovereign Security Scanner..." -ForegroundColor Yellow
    & $venvPy "$ScriptDir\sovereign_security_scanner.py"
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  [PASS] No critical vulnerabilities found." -ForegroundColor Green
    } else {
        Write-Host "  [WARN] Security scan identified issues. See report for details." -ForegroundColor Yellow
    }
} else {
    Write-Host "[SKIP] Security scan skipped (--IngestOnly)" -ForegroundColor Gray
}

# 3. Log execution to ledger
Write-Host ""
Write-Host "Recording Hacking Suite execution in Sovereign Ledger..." -ForegroundColor Yellow
$summary = "Hacking Orchestrator executed for $NodeId. Intel ingestion and security scan cycles completed."
& $venvPy "$RepoRoot\scripts\governance\log_decision.py" "$summary"
Write-Host "  [DONE] Hacking cycle registered." -ForegroundColor Green

Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host "  HACKING ORCHESTRATION COMPLETE" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""
