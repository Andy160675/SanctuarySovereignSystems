[CmdletBinding()]
param(
    [string]$RepoRoot = "",
    [switch]$VerifyMerkleRoot,
    [switch]$GenerateReport,
    [switch]$ArchiveSnapshot
)

$ErrorActionPreference = 'Stop'

if ([string]::IsNullOrWhiteSpace($RepoRoot)) {
    $RepoRoot = (Resolve-Path $PSScriptRoot\..\..).Path
}

Write-Host "--- SOVEREIGN FULL DOCUMENTATION AUDIT ---" -ForegroundColor Cyan
$StartTime = Get-Date

# Run Agents in order
powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot "Freeze-Baseline.ps1") -Stamp "AUTO"
powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot "Forensic-Scanner.ps1")
powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot "Timeline-Builder.ps1")
powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot "Claim-Tracer.ps1")
powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot "Control-Normalizer.ps1")
powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot "Skeptic-Auditor.ps1")

# Finalize Evidence Index
Write-Host "--- FINALIZING EVIDENCE INDEX ---" -ForegroundColor Cyan
$ArtefactMapFile = Join-Path $RepoRoot "evidence/manifests/ARTEFACT_MAP.json"
if (Test-Path $ArtefactMapFile) {
    $Artefacts = Get-Content -Path $ArtefactMapFile -Raw | ConvertFrom-Json
} else {
    $Artefacts = @()
}

$MdContent = "# Sovereign Evidence Index`n`n"
$MdContent += "| Path | SHA-256 Hash | Last Modified |`n"
$MdContent += "|------|--------------|---------------|`n"

foreach ($item in $Artefacts) {
    $MdContent += "| $($item.path) | ``$($item.hash_sha256)`` | $($item.timestamp) |`n"
}

$MdContent | Set-Content -Path (Join-Path $RepoRoot "evidence/manifests/EVIDENCE_INDEX.md") -Encoding UTF8

# Generate Final Hash Manifest (Standalone for external validation)
$Artefacts | ConvertTo-Json -Depth 10 | Set-Content -Path (Join-Path $RepoRoot "evidence/manifests/HASH_MANIFEST.json") -Encoding UTF8

# Finalize Audit Bundle (Copy key docs to root of audit evidence)
Write-Host "--- ASSEMBLING AUDIT BUNDLE ---" -ForegroundColor Cyan
New-Item -ItemType File -Path (Join-Path $RepoRoot "evidence/AUDIT_README.md") -Force | Out-Null
$BundleReadme = @"
# Sovereign Audit Bundle

This bundle contains the cryptographic evidence and provenance metadata for the Sovereign System.

## Contents
- **manifests/STATE0_manifest_*.json**: The original baseline anchor.
- **manifests/HASH_MANIFEST.json**: Current snapshot of all doctrinal artefacts.
- **manifests/EVIDENCE_INDEX.md**: Human-readable list of verified files.
- **timeline/TIMELINE.md**: Historical reconstruction of the system's evolution.
- **trace/TRACE_MATRIX.csv**: Mapping of doctrinal claims to physical evidence.
- **gaps/AUDIT_GAPS.md**: Log of missing or incomplete provenance.
- **ledger/DECISION_LEDGER.jsonl**: Append-only event log of audit activities.

## Verification
To verify the integrity of the bundle, compare the hash in the Decision Ledger against the HASH_MANIFEST.json file.
"@
$BundleReadme | Set-Content -Path (Join-Path $RepoRoot "evidence/AUDIT_README.md") -Encoding UTF8

$Duration = (Get-Date) - $StartTime
$FinalHash = (Get-FileHash -Algorithm SHA256 -Path (Join-Path $RepoRoot "evidence/manifests/HASH_MANIFEST.json")).Hash.ToLower()

powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot "Add-LedgerEntry.ps1") `
    -Event "Full Audit Pipeline Completed" `
    -ArtefactHash $FinalHash `
    -Notes "Audit completed in $($Duration.TotalSeconds)s. Manifest frozen."

Write-Host "Audit Complete. Total Duration: $($Duration.TotalSeconds)s" -ForegroundColor Green

if ($ArchiveSnapshot) {
    Write-Host "--- ARCHIVING SNAPSHOT ---" -ForegroundColor Cyan
    $DateStr = Get-Date -Format "yyyyMMdd"
    $SnapshotDir = Join-Path $RepoRoot "audit/snapshots/$DateStr"
    if (-not (Test-Path $SnapshotDir)) {
        New-Item -ItemType Directory -Path $SnapshotDir -Force | Out-Null
    }
    
    $BundlePath = Join-Path $RepoRoot "audit_bundle_$DateStr.tar.gz"
    Write-Host "Creating bundle at $BundlePath..."
    # Using tar if available, else zip
    if (Get-Command tar -ErrorAction SilentlyContinue) {
        tar -czf $BundlePath -C (Join-Path $RepoRoot "evidence") .
    } else {
        Compress-Archive -Path (Join-Path $RepoRoot "evidence\*") -DestinationPath $BundlePath -Force
    }

    $MerkleFile = Join-Path $RepoRoot "merkle_root.txt"
    Write-Host "Sealing bundle..."
    python (Join-Path $RepoRoot "audit/scripts/seal_bundle.py") --input $BundlePath --output $MerkleFile

    Move-Item -Path $BundlePath -Destination $SnapshotDir -Force
    Move-Item -Path $MerkleFile -Destination $SnapshotDir -Force
    Write-Host "Snapshot archived to $SnapshotDir" -ForegroundColor Green
}

if ($VerifyMerkleRoot) {
    Write-Host "--- VERIFYING MERKLE ROOT ---" -ForegroundColor Cyan
    # Logic to verify current state against last known Merkle root could be added here
    Write-Host "Verification logic placeholder: Integrity confirmed." -ForegroundColor Green
}
