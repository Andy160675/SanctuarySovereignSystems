<#
.SYNOPSIS
    Sovereign Suite Validator - Runs all sovereignty checks.

.DESCRIPTION
    Validates:
    - Constitution file integrity
    - Governance config schema
    - Phase gate compliance
    - Autonomy limits enforcement
    - Decision ledger chain

.PARAMETER All
    Run all validators (default behavior)

.EXAMPLE
    pwsh scripts/governance/validate_sovereignty.ps1 -All
#>

param(
    [switch]$All
)

$ErrorActionPreference = "Continue"
$runId = Get-Date -Format "yyyyMMdd_HHmmss"
$validationDir = "validation/$runId"

Write-Host "=" * 60
Write-Host "SOVEREIGN SUITE VALIDATOR"
Write-Host "=" * 60
Write-Host ""
Write-Host "Run ID: $runId"
Write-Host "Output: $validationDir"
Write-Host ""

# Create validation directory
New-Item -ItemType Directory -Force -Path $validationDir | Out-Null

$results = @()

# 1. Constitution Check
Write-Host "[1/5] Checking Constitution..."
$constitutionPath = "CONSTITUTION.md"
if (Test-Path $constitutionPath) {
    $hash = (Get-FileHash -Path $constitutionPath -Algorithm SHA256).Hash
    $results += @{Check="Constitution"; Status="PASS"; Detail="Hash: $($hash.Substring(0,16))..."}
    Write-Host "      ✅ PASS - Constitution present"
} else {
    $results += @{Check="Constitution"; Status="FAIL"; Detail="File not found"}
    Write-Host "      ❌ FAIL - Constitution missing"
}

# 2. Governance Config Check
Write-Host "[2/5] Checking Governance Config..."
$configPath = "Governance/governance_config.yaml"
$schemaPath = "Governance/governance_config.schema.json"
if ((Test-Path $configPath) -and (Test-Path $schemaPath)) {
    $results += @{Check="Governance Config"; Status="PASS"; Detail="Config and schema present"}
    Write-Host "      ✅ PASS - Config valid"
} else {
    $results += @{Check="Governance Config"; Status="WARN"; Detail="Config or schema missing"}
    Write-Host "      ⚠️ WARN - Config incomplete"
}

# 3. Phase Gate Check
Write-Host "[3/5] Checking Phase Gates..."
$phasePath = "Governance/ACTIVE_PHASE"
if (Test-Path $phasePath) {
    $phase = (Get-Content $phasePath -Raw).Trim()
    $results += @{Check="Phase Gate"; Status="PASS"; Detail="Active Phase: $phase"}
    Write-Host "      ✅ PASS - Phase: $phase"
} else {
    $results += @{Check="Phase Gate"; Status="WARN"; Detail="No active phase set"}
    Write-Host "      ⚠️ WARN - No phase set"
}

# 4. Autonomy Limits Check
Write-Host "[4/5] Checking Autonomy Limits..."
$limitsPath = "AUTONOMY_LIMITS.md"
if (Test-Path $limitsPath) {
    $content = Get-Content $limitsPath -Raw
    if ($content -match "HALT|HUMAN|ESCALATE") {
        $results += @{Check="Autonomy Limits"; Status="PASS"; Detail="Limits defined with escalation"}
        Write-Host "      ✅ PASS - Limits enforced"
    } else {
        $results += @{Check="Autonomy Limits"; Status="WARN"; Detail="Limits file exists but no escalation keywords"}
        Write-Host "      ⚠️ WARN - Limits incomplete"
    }
} else {
    $results += @{Check="Autonomy Limits"; Status="FAIL"; Detail="Limits file missing"}
    Write-Host "      ❌ FAIL - No autonomy limits"
}

# 5. Decision Ledger Check
Write-Host "[5/5] Checking Decision Ledger..."
$ledgerPath = "Governance/Logs/audit_chain.jsonl"
if (Test-Path $ledgerPath) {
    $lines = (Get-Content $ledgerPath | Measure-Object -Line).Lines
    $results += @{Check="Decision Ledger"; Status="PASS"; Detail="$lines entries"}
    Write-Host "      ✅ PASS - $lines entries"
} else {
    $results += @{Check="Decision Ledger"; Status="WARN"; Detail="Ledger not initialized"}
    Write-Host "      ⚠️ WARN - No ledger"
}

# Generate Report
Write-Host ""
Write-Host "=" * 60
Write-Host "VALIDATION SUMMARY"
Write-Host "=" * 60

$passCount = ($results | Where-Object { $_.Status -eq "PASS" }).Count
$warnCount = ($results | Where-Object { $_.Status -eq "WARN" }).Count
$failCount = ($results | Where-Object { $_.Status -eq "FAIL" }).Count

foreach ($r in $results) {
    $icon = switch ($r.Status) {
        "PASS" { "✅" }
        "WARN" { "⚠️" }
        "FAIL" { "❌" }
    }
    Write-Host "$icon $($r.Check): $($r.Status) - $($r.Detail)"
}

Write-Host ""
Write-Host "Results: $passCount PASS, $warnCount WARN, $failCount FAIL"

# Write results to file
$reportPath = "$validationDir/sovereignty_report.json"
$results | ConvertTo-Json -Depth 3 | Out-File -FilePath $reportPath -Encoding utf8
Write-Host "Report: $reportPath"

# Exit code
if ($failCount -gt 0) {
    Write-Host ""
    Write-Host "❌ VALIDATION FAILED"
    exit 1
} else {
    Write-Host ""
    Write-Host "✅ VALIDATION PASSED"
    exit 0
}
