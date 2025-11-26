# anchor-svc-bundle.ps1
# =====================
# Zips SVC commits, computes SHA-256, and prepares for IPFS/Arweave upload
#
# Usage:
#   .\scripts\anchor-svc-bundle.ps1
#   .\scripts\anchor-svc-bundle.ps1 -Upload   # Actually upload to IPFS (requires ipfs CLI)

param(
    [switch]$Upload
)

$ErrorActionPreference = "Stop"
$base = "C:\sovereign-system"
$svcDir = "$base\sov_vc\commits"
$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$bundleName = "svc-bundle-$timestamp"
$zipPath = "$base\$bundleName.zip"
$hashPath = "$base\$bundleName.sha256"
$anchorPath = "$base\$bundleName.anchor.json"

Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host "  SVC ANCHOR BUNDLE GENERATOR" -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host ""

# 1. Check for commits
$commits = Get-ChildItem "$svcDir\*.json" -ErrorAction SilentlyContinue
if (-not $commits) {
    Write-Host "No SVC commits found in $svcDir" -ForegroundColor Yellow
    exit 0
}

Write-Host "Found $($commits.Count) commit(s) to bundle" -ForegroundColor Green
Write-Host ""

# 2. Create ZIP bundle
Write-Host "[1/4] Creating ZIP bundle..." -ForegroundColor Cyan
Compress-Archive -Path "$svcDir\*.json" -DestinationPath $zipPath -Force
Write-Host "  Created: $zipPath" -ForegroundColor Gray

# 3. Compute SHA-256
Write-Host "[2/4] Computing SHA-256 hash..." -ForegroundColor Cyan
$hash = (Get-FileHash $zipPath -Algorithm SHA256).Hash.ToLower()
$hash | Out-File -FilePath $hashPath -Encoding utf8 -NoNewline
Write-Host "  Hash: $hash" -ForegroundColor White
Write-Host "  Saved: $hashPath" -ForegroundColor Gray

# 4. Get HEAD commit info
Write-Host "[3/4] Reading HEAD commit..." -ForegroundColor Cyan
$headFile = "$base\sov_vc\HEAD"
$headCommit = $null
if (Test-Path $headFile) {
    $headFilename = Get-Content $headFile -Raw
    $headFilename = $headFilename.Trim()
    $headCommitPath = "$svcDir\$headFilename"
    if (Test-Path $headCommitPath) {
        $headCommit = Get-Content $headCommitPath -Raw | ConvertFrom-Json
        Write-Host "  HEAD: $($headCommit.commit_hash.Substring(0,8))... ($($headCommit.case_id))" -ForegroundColor White
    }
}

# 5. Create anchor manifest
Write-Host "[4/4] Creating anchor manifest..." -ForegroundColor Cyan
$anchor = @{
    bundle_name = $bundleName
    created_at = (Get-Date -Format "o")
    bundle_hash = $hash
    commit_count = $commits.Count
    head_commit = if ($headCommit) { $headCommit.commit_hash } else { $null }
    head_case_id = if ($headCommit) { $headCommit.case_id } else { $null }
    head_integrity = if ($headCommit) { $headCommit.integrity_status } else { $null }
    ipfs_cid = $null
    arweave_uri = $null
}

$anchor | ConvertTo-Json -Depth 10 | Out-File -FilePath $anchorPath -Encoding utf8
Write-Host "  Manifest: $anchorPath" -ForegroundColor Gray

# 6. Optional IPFS upload
if ($Upload) {
    Write-Host ""
    Write-Host "[UPLOAD] Uploading to IPFS..." -ForegroundColor Yellow

    $ipfsCheck = Get-Command ipfs -ErrorAction SilentlyContinue
    if ($ipfsCheck) {
        try {
            $cid = ipfs add -Q $zipPath
            Write-Host "  IPFS CID: $cid" -ForegroundColor Green

            # Update anchor with CID
            $anchor.ipfs_cid = $cid
            $anchor | ConvertTo-Json -Depth 10 | Out-File -FilePath $anchorPath -Encoding utf8
        } catch {
            Write-Host "  IPFS upload failed: $_" -ForegroundColor Red
        }
    } else {
        Write-Host "  IPFS CLI not found. Install with: choco install ipfs" -ForegroundColor DarkYellow
        Write-Host "  Or manually upload $zipPath to https://web3.storage" -ForegroundColor Gray
    }
}

Write-Host ""
Write-Host "=" * 60 -ForegroundColor Green
Write-Host "  BUNDLE READY" -ForegroundColor Green
Write-Host "=" * 60 -ForegroundColor Green
Write-Host ""
Write-Host "Files created:" -ForegroundColor Cyan
Write-Host "  ZIP:      $zipPath"
Write-Host "  Hash:     $hashPath"
Write-Host "  Manifest: $anchorPath"
Write-Host ""
Write-Host "Bundle SHA-256: $hash" -ForegroundColor White
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Upload ZIP to IPFS/Arweave/S3"
Write-Host "  2. Record CID/URI in anchor manifest"
Write-Host "  3. Commit manifest to git"
Write-Host ""
