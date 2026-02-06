# scripts/governance/rapid_self_improvement.ps1
param(
    [string]$NodeId = $env:COMPUTERNAME,
    [string]$TargetDir = "."
)

Write-Host "=== RAPID SELF-IMPROVEMENT TASK: $NodeId ===" -ForegroundColor Cyan
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$reportPath = "validation/improvement/report_$($NodeId)_$timestamp.json"
New-Item -ItemType Directory -Force (Split-Path $reportPath) | Out-Null

$results = @{
    node_id = $NodeId
    timestamp = Get-Date -Format "o"
    audit = @()
    fixes = @()
    futureproofing = @()
}

# 1. File Structure Audit
Write-Host "[1/3] Auditing file structure..." -ForegroundColor Yellow
$misplaced = Get-ChildItem -Path $TargetDir -Recurse -File | Where-Object {
    $_.FullName -notmatch ".venv|.git|.junie" -and $_.Name -match "test_.*\.py" -and $_.DirectoryName -notmatch "tests"
}
foreach ($f in $misplaced) {
    $results.audit += @{
        issue = "Misplaced test file"
        path = $f.FullName
        recommendation = "Move to tests/ directory"
    }
}

# 2. Debugging Sweep
Write-Host "[2/3] Debugging sweep..." -ForegroundColor Yellow
$debugTarget = Get-ChildItem -Path $TargetDir -Filter "*.py" -Recurse | Where-Object { $_.FullName -notmatch ".venv" }
foreach ($file in $debugTarget) {
    $content = Get-Content $file.FullName
    if ($content -match "print\(.*\)") {
        $results.audit += @{
            issue = "Unstructured logging (print)"
            path = $file.FullName
            recommendation = "Use logging module or decision_ledger"
        }
    }
}

# 3. Futureproofing Check
Write-Host "[3/3] Futureproofing check..." -ForegroundColor Yellow
$hardcoded = Get-ChildItem -Path $TargetDir -Recurse -File | Where-Object { $_.Extension -match "\.(ps1|py|json|yml)" -and $_.FullName -notmatch ".venv|.git" }
foreach ($file in $hardcoded) {
    $content = Get-Content $file.FullName -Raw
    if ($content -match "[C-Z]:\\(?!Users|Windows|Program Files)") {
        $results.futureproofing += @{
            issue = "Potential hardcoded absolute path"
            path = $file.FullName
            pattern = $matches[0]
        }
    }
}

$results | ConvertTo-Json -Depth 10 | Out-File $reportPath
Write-Host "Self-improvement report generated: $reportPath" -ForegroundColor Green

# Log to decision ledger if possible
if (Test-Path "scripts/governance/log_decision.py") {
    python scripts/governance/log_decision.py "Self-improvement audit completed for $NodeId. Found $($results.audit.Count) audit items and $($results.futureproofing.Count) futureproofing items."
}
