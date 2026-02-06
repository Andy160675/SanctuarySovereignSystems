<#
.SYNOPSIS
    Generate SITREP Evidence Pack with cryptographic proofs.

.DESCRIPTION
    Produces a time-stamped evidence pack under validation/SITREP_PACK_<ts>/
    containing:
    - Sovereignty validator log summary
    - Network/process snapshots
    - Ledger tail (if present)
    - Healthcheck results
    - Ledger verification results
    - Deterministic pack_checksums.sha256
    - Receipt RECEIPT.sha256 (hash of checksum file)

.EXAMPLE
    pwsh scripts/governance/generate_sitrep_pack.ps1
#>

$ErrorActionPreference = "Stop"
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$packDir = "validation/SITREP_PACK_$timestamp"
$evidenceDir = "evidence"

Write-Host "=" * 60
Write-Host "SITREP EVIDENCE PACK GENERATOR"
Write-Host "=" * 60
Write-Host ""
Write-Host "Timestamp: $timestamp"
Write-Host "Pack Directory: $packDir"
Write-Host ""

# Create directories
New-Item -ItemType Directory -Force -Path $packDir | Out-Null
New-Item -ItemType Directory -Force -Path $evidenceDir | Out-Null

# 1. Run Sovereignty Validator (if exists)
$validatorLog = "$packDir/validate_sovereignty.log"
$validatorScript = "scripts/governance/validate_sovereignty.ps1"
if (Test-Path $validatorScript) {
    Write-Host "[1/6] Running Sovereignty Validator..."
    try {
        & pwsh $validatorScript -All 2>&1 | Out-File -FilePath $validatorLog -Encoding utf8
        Write-Host "      ✅ Validator completed"
    } catch {
        "VALIDATOR ERROR: $_" | Out-File -FilePath $validatorLog -Encoding utf8
        Write-Host "      ⚠️ Validator failed: $_"
    }
} else {
    Write-Host "[1/6] Sovereignty Validator not found, skipping..."
    "VALIDATOR NOT FOUND" | Out-File -FilePath $validatorLog -Encoding utf8
}

# 2. Run Healthcheck
$healthLog = "$packDir/healthcheck.log"
Write-Host "[2/6] Running Healthcheck..."
try {
    python healthcheck.py 2>&1 | Out-File -FilePath $healthLog -Encoding utf8
    $healthResult = "PASS"
    Write-Host "      ✅ Healthcheck completed"
} catch {
    "HEALTHCHECK ERROR: $_" | Out-File -FilePath $healthLog -Encoding utf8
    $healthResult = "FAIL"
    Write-Host "      ⚠️ Healthcheck failed"
}

# 3. Run Ledger Verification
$ledgerLog = "$packDir/ledger_verify.log"
$ledgerScript = "scripts/governance/verify_decision_ledger.py"
Write-Host "[3/6] Verifying Decision Ledger..."
if (Test-Path $ledgerScript) {
    try {
        python $ledgerScript 2>&1 | Out-File -FilePath $ledgerLog -Encoding utf8
        $ledgerResult = "PASS"
        Write-Host "      ✅ Ledger verification completed"
    } catch {
        "LEDGER VERIFY ERROR: $_" | Out-File -FilePath $ledgerLog -Encoding utf8
        $ledgerResult = "FAIL"
        Write-Host "      ⚠️ Ledger verification failed"
    }
} else {
    "LEDGER VERIFIER NOT FOUND" | Out-File -FilePath $ledgerLog -Encoding utf8
    $ledgerResult = "SKIP"
    Write-Host "      ⚠️ Ledger verifier not found"
}

# 4. Capture Network/Process Snapshots
Write-Host "[4/6] Capturing System Snapshots..."
try {
    if ($IsLinux -or $IsMacOS) {
        netstat -tuln 2>&1 | Out-File -FilePath "$packDir/netstat.txt" -Encoding utf8
        ps aux 2>&1 | Out-File -FilePath "$packDir/processes.txt" -Encoding utf8
    } else {
        netstat -an 2>&1 | Out-File -FilePath "$packDir/netstat.txt" -Encoding utf8
        Get-Process | Out-File -FilePath "$packDir/processes.txt" -Encoding utf8
    }
    Write-Host "      ✅ Snapshots captured"
} catch {
    Write-Host "      ⚠️ Snapshot capture partial"
}

# 5. Copy Ledger Tail (if exists)
$ledgerPath = "Governance/Logs/audit_chain.jsonl"
Write-Host "[5/6] Extracting Ledger Tail..."
if (Test-Path $ledgerPath) {
    Get-Content $ledgerPath -Tail 50 | Out-File -FilePath "$packDir/ledger_tail.jsonl" -Encoding utf8
    $ledgerEntries = (Get-Content $ledgerPath | Measure-Object -Line).Lines
    Write-Host "      ✅ Ledger tail extracted ($ledgerEntries total entries)"
} else {
    "LEDGER NOT FOUND" | Out-File -FilePath "$packDir/ledger_tail.jsonl" -Encoding utf8
    $ledgerEntries = 0
    Write-Host "      ⚠️ Ledger not found"
}

# 6. Generate Checksums and Receipt
Write-Host "[6/6] Generating Checksums and Receipt..."
$checksumFile = "$packDir/pack_checksums.sha256"
$receiptFile = "$packDir/RECEIPT.sha256"

# Get all files in pack (excluding checksum files)
$packFiles = Get-ChildItem -Path $packDir -File | Where-Object { $_.Name -notmatch "checksums|RECEIPT" } | Sort-Object Name

$checksums = @()
foreach ($file in $packFiles) {
    $hash = (Get-FileHash -Path $file.FullName -Algorithm SHA256).Hash
    $checksums += "$hash  $($file.Name)"
}
$checksums | Out-File -FilePath $checksumFile -Encoding utf8

# Generate receipt (hash of checksum file)
$receiptHash = (Get-FileHash -Path $checksumFile -Algorithm SHA256).Hash
$receiptHash | Out-File -FilePath $receiptFile -Encoding utf8

Write-Host "      ✅ Checksums: $checksumFile"
Write-Host "      ✅ Receipt: $receiptFile"

# 7. Create ZIP Archive
$zipPath = "$evidenceDir/SITREP_PACK_$timestamp.zip"
Write-Host ""
Write-Host "Creating archive: $zipPath"
Compress-Archive -Path "$packDir/*" -DestinationPath $zipPath -Force
Write-Host "✅ Archive created"

# 8. Update evidence/SITREP.md
$sitrepPath = "$evidenceDir/SITREP.md"
Write-Host ""
Write-Host "Updating SITREP: $sitrepPath"

$sitrepContent = @"
# SOVEREIGN SYSTEM SITREP

**Generated:** $(Get-Date -Format "yyyy-MM-dd HH:mm:ss") UTC
**Pack ID:** SITREP_PACK_$timestamp

## Verification Summary

| Check | Result |
|-------|--------|
| Healthcheck | $healthResult |
| Ledger Verification | $ledgerResult |
| Ledger Entries | $ledgerEntries |

## Evidence Pack Contents

- ``validate_sovereignty.log`` - Sovereignty validator output
- ``healthcheck.log`` - System health check results
- ``ledger_verify.log`` - Decision ledger integrity verification
- ``netstat.txt`` - Network connections snapshot
- ``processes.txt`` - Running processes snapshot
- ``ledger_tail.jsonl`` - Last 50 ledger entries
- ``pack_checksums.sha256`` - Deterministic file checksums
- ``RECEIPT.sha256`` - Pack seal (hash of checksums)

## Cryptographic Seal

**Receipt Hash:** ``$receiptHash``

To verify:
``````powershell
`$expected = Get-Content "$packDir/RECEIPT.sha256" -Raw
`$actual = (Get-FileHash "$packDir/pack_checksums.sha256" -Algorithm SHA256).Hash
if (`$expected.Trim() -eq `$actual) { "RECEIPT OK" } else { "RECEIPT MISMATCH" }
``````

## Archive

- **Path:** ``$zipPath``
- **Pack Directory:** ``$packDir``

---
*Generated by generate_sitrep_pack.ps1*
"@

$sitrepContent | Out-File -FilePath $sitrepPath -Encoding utf8
Write-Host "✅ SITREP updated"

Write-Host ""
Write-Host "=" * 60
Write-Host "SITREP PACK GENERATION COMPLETE"
Write-Host "=" * 60
Write-Host ""
Write-Host "Pack: $packDir"
Write-Host "Archive: $zipPath"
Write-Host "SITREP: $sitrepPath"
Write-Host "Receipt: $receiptHash"
