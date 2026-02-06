# scripts/learning/Invoke-LearningSuite.ps1
# MISSION: Execute the Collective Learning & Kaizen Loop
# Part of Phase 2.0: High Autonomy (Self-Learning/Healing)

param(
    [string]$NodeId = $env:COMPUTERNAME,
    [switch]$All
)

$ErrorActionPreference = "Continue"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Resolve-Path "$ScriptDir\..\.."

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  THE BLADE OF TRUTH - LEARNING SUITE" -ForegroundColor Cyan
Write-Host "  Phase 2.0: Collective Learning & Kaizen Loop" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# 1. GembaBot (Go-See-Fix-Share)
Write-Host "[1/3] Running GembaBot (Kaizen Loop)..." -ForegroundColor Yellow
& powershell -File "$ScriptDir\gemba_bot.ps1" -NodeId $NodeId
if ($LASTEXITCODE -ne 0) {
    Write-Host "  [WARN] GembaBot encountered issues." -ForegroundColor Yellow
}

# 2. Rapid Self-Improvement (Audit & Fix)
Write-Host "[2/3] Running Rapid Self-Improvement Audit..." -ForegroundColor Yellow
& powershell -File "$ScriptDir\rapid_self_improvement.ps1" -NodeId $NodeId -TargetDir $RepoRoot
if ($LASTEXITCODE -ne 0) {
    Write-Host "  [WARN] Self-improvement audit encountered issues." -ForegroundColor Yellow
}

# 3. Learning Engine (Report Generation)
Write-Host "[3/3] Generating Learning Report..." -ForegroundColor Yellow
$eventsPath = "$RepoRoot\evidence\session-logs\self_heal_events.jsonl"
$reportPath = "$RepoRoot\evidence\visuals\LEARNING_REPORT.md"

if (Test-Path $eventsPath) {
    $venvPy = "$RepoRoot\.venv\Scripts\python.exe"
    if (-not (Test-Path $venvPy)) { $venvPy = "python" }
    
    & $venvPy "$ScriptDir\learn_engine.py" --events $eventsPath --out $reportPath
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  [OK] Learning report generated: $reportPath" -ForegroundColor Green
    } else {
        Write-Host "  [FAIL] Learning engine failed." -ForegroundColor Red
    }
} else {
    Write-Host "  [SKIP] No self-heal events found at $eventsPath" -ForegroundColor Gray
}

# 4. Final Ledger Entry
Write-Host ""
Write-Host "Recording Learning Suite execution in Sovereign Ledger..." -ForegroundColor Yellow
$summary = "Learning Suite executed for $NodeId. GembaBot, Self-Improvement, and Learning Engine cycles completed."
$venvPy = "$RepoRoot\.venv\Scripts\python.exe"
if (-not (Test-Path $venvPy)) { $venvPy = "python" }

& $venvPy "$RepoRoot\scripts\governance\log_decision.py" "$summary"
Write-Host "  [DONE] Learning cycle registered." -ForegroundColor Green

Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host "  LEARNING SUITE COMPLETE" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""
