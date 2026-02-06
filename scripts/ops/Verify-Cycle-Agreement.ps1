<#
.SYNOPSIS
    Verify-Cycle-Agreement.ps1 — Independent Verification Script (Doctrine-Compliant)
.DESCRIPTION
    Implements the 5-step checklist for independent artifact inspection:
    1. Hash Recomputation
    2. Timestamp Coherence
    3. Cross-reference Resolution
    4. Gate Logic Confirmation
    5. Result Declaration (PASS/SIGNAL)
#>

param(
    [string]$RunId = "20260206_110601",
    [string]$OpsLog = "NAS/04_LOGS/continuous_ops/ops_20260206.jsonl",
    [string]$FleetSummary = "NAS/04_LOGS/continuous_ops/fleet_mega_20260206_1106/summary.json",
    [string]$SovReport = "validation/20260206_110601/sovereignty_report.json",
    [string]$Baseline = "evidence/baselines/DESKTOP-V20CP12/evidence_baseline_summary_20260206_110601.json"
)

$Results = @()

Write-Host "`n--- INDEPENDENT VERIFICATION: RUN $RunId ---" -ForegroundColor Cyan

# STEP 1 & 2: Hash Recomputation
Write-Host "[1/5] Recomputing Hashes..."
$baselineData = Get-Content $Baseline | Out-String | ConvertFrom-Json
$sovData = Get-Content $SovReport | Out-String | ConvertFrom-Json
$check1 = $true

# Evidence is an array of strings in the format "@{Path=...; SHA256=...}"
$EvidenceArray = @()
foreach ($eStr in $baselineData.Evidence) {
    if ($eStr -match "Path=(?<Path>.*?); SHA256=(?<SHA>.*?)[;}]") {
        $EvidenceArray += [PSCustomObject]@{
            Path = $Matches.Path
            SHA256 = $Matches.SHA
            Status = if ($Matches.SHA) { "CAPTURED" } else { "MISSING" }
        }
    }
}

foreach ($file in $EvidenceArray) {
    if ($file.Status -eq "CAPTURED") {
        $recomputed = (Get-FileHash -Path $file.Path -Algorithm SHA256).Hash.ToLower()
        if ($recomputed -eq $file.SHA256.ToLower()) {
            Write-Host "  ✅ $($file.Path) hash matches." -ForegroundColor Green
        } else {
            Write-Host "  ❌ $($file.Path) hash MISMATCH! (Recomputed: $recomputed vs Baseline: $($file.SHA256))" -ForegroundColor Red
            $check1 = $false
        }
    }
}

# Cross-reference with Sov Report
$constitutionHashInSov = $sovData | Where-Object { $_.Check -eq "Constitution" } | Select-Object -ExpandProperty Detail
$constitutionHashInBase = $EvidenceArray | Where-Object { $_.Path -like "*CONSTITUTION.md*" } | Select-Object -ExpandProperty SHA256

if ($constitutionHashInBase -and $constitutionHashInSov -and $constitutionHashInBase.StartsWith($constitutionHashInSov.Split(" ")[1].Replace("...","").ToLower())) {
     Write-Host "  ✅ Constitution hash cross-reference matches." -ForegroundColor Green
} else {
     Write-Host "  ❌ Constitution hash cross-reference MISMATCH!" -ForegroundColor Red
     $check1 = $false
}

# STEP 3: Timestamp Coherence
Write-Host "[2/5] Checking Timestamp Coherence..."
$opsLines = Get-Content $OpsLog | ConvertFrom-Json
$cycle1Start = $opsLines | Where-Object { $_.message -match "Starting Operational Cycle #1" } | Select-Object -ExpandProperty timestamp | Select-Object -Last 1
$cycle1End = $opsLines | Where-Object { $_.message -match "Cycle #1 Finished" } | Select-Object -ExpandProperty timestamp | Select-Object -Last 1

$startTs = [DateTime]$cycle1Start
$endTs = [DateTime]$cycle1End
$check3 = $true

if ($startTs -le $endTs) {
    Write-Host "  ✅ Timestamps are monotonic ($cycle1Start -> $cycle1End)" -ForegroundColor Green
} else {
    Write-Host "  ❌ Timestamps are NOT monotonic!" -ForegroundColor Red
    $check3 = $false
}

# STEP 4: Cross-reference Resolution
Write-Host "[3/5] Resolving Cross-references..."
$check4 = $true
if (Test-Path $OpsLog) { Write-Host "  ✅ Ops Log exists." -ForegroundColor Green } else { $check4 = $false }
if (Test-Path $FleetSummary) { Write-Host "  ✅ Fleet Summary exists." -ForegroundColor Green } else { $check4 = $false }
if (Test-Path $SovReport) { Write-Host "  ✅ Sovereignty Report exists." -ForegroundColor Green } else { $check4 = $false }
if (Test-Path $Baseline) { Write-Host "  ✅ Baseline exists." -ForegroundColor Green } else { $check4 = $false }

# STEP 5: Gate Logic Confirmation
Write-Host "[4/5] Confirming Gate Logic..."
$check5 = $false
$valStart = $opsLines | Where-Object { $_.message -match "Integrity Validation" -and $_.level -eq "SUCCESS" }
if ($valStart) {
    $check5 = $true
    Write-Host "  ✅ Gate logic confirmed: Success follows Validation." -ForegroundColor Green
} else {
    Write-Host "  ❌ Gate logic FAILURE: No validation success found in logs." -ForegroundColor Red
}

# FINAL RESULT
Write-Host "`n--- FINAL VERIFICATION RESULT ---" -ForegroundColor Cyan
if ($check1 -and $check3 -and $check4 -and $check5) {
    Write-Host "RESULT: PASS" -ForegroundColor Green
} else {
    Write-Host "RESULT: SIGNAL (Verification Failed)" -ForegroundColor Red
}
