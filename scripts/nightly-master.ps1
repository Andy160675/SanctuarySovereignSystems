# Nightly Golden Master Generation – Sovereign Phase 5
# Automated backup, hashing, and GPG signing

[CmdletBinding()]
param(
    [string]$Root = "D:\SOVEREIGN-2025-11-19",
    [string]$ArchiveBase = "C:\SovereignArchives"
)

$DateStamp = Get-Date -Format "yyyy-MM-dd-HHmm"
$Archive = "$ArchiveBase\golden-master-$DateStamp.zip"
$ManifestDir = "$Root\HASH_MANIFESTS"
$ManifestFile = "$ManifestDir\MASTER_MANIFEST_$DateStamp.sha256"

Write-Host "🔥 SOVEREIGN NIGHTLY MASTER - Phase 5" -ForegroundColor Red
Write-Host "=====================================" -ForegroundColor Red
Write-Host "Date: $DateStamp" -ForegroundColor Cyan
Write-Host "Root: $Root" -ForegroundColor Cyan
Write-Host "Archive: $Archive" -ForegroundColor Cyan
Write-Host ""

# Ensure directories exist
if (!(Test-Path $ArchiveBase)) {
    New-Item -ItemType Directory -Path $ArchiveBase -Force | Out-Null
    Write-Host "✅ Created archive directory: $ArchiveBase" -ForegroundColor Green
}

if (!(Test-Path $ManifestDir)) {
    New-Item -ItemType Directory -Path $ManifestDir -Force | Out-Null
    Write-Host "✅ Created manifest directory: $ManifestDir" -ForegroundColor Green
}

# Generate hash manifest
Write-Host "📊 Generating hash manifest..." -ForegroundColor Yellow
try {
    $Files = Get-ChildItem -Path $Root -Recurse -File | Where-Object { 
        $_.Extension -in @('.md', '.txt', '.py', '.ps1', '.yaml', '.yml', '.json') -and
        $_.FullName -notlike "*\.git\*" -and
        $_.FullName -notlike "*\node_modules\*"
    }
    
    $Manifest = @()
    $TotalFiles = $Files.Count
    $Current = 0
    
    foreach ($File in $Files) {
        $Current++
        Write-Progress -Activity "Hashing files" -Status "$Current of $TotalFiles" -PercentComplete (($Current / $TotalFiles) * 100)
        
        # Use incremental hash cache
        $ResultJson = python scripts/lib/hash_cache.py $File.FullName
        $Result = $ResultJson | ConvertFrom-Json
        $HashValue = $Result.hash
        $IsCached = $Result.cached

        $RelativePath = $File.FullName.Replace($Root, "").TrimStart('\\')
        $Manifest += "$($HashValue)  $RelativePath"
        
        if ($IsCached -eq $false) {
            Write-Host "   (Re-hashed: $RelativePath)" -ForegroundColor Gray
        }
    }
    
    $Manifest | Out-File -FilePath $ManifestFile -Encoding UTF8
    Write-Host "✅ Hash manifest created: $ManifestFile" -ForegroundColor Green
    Write-Host "   Files processed: $TotalFiles" -ForegroundColor Cyan
    
} catch {
    Write-Host "❌ Error generating hash manifest: $_" -ForegroundColor Red
    exit 1
}

# GPG sign manifest
Write-Host "🔐 GPG signing manifest..." -ForegroundColor Yellow
try {
    $GpgResult = gpg --batch --yes --detach-sign --armor $ManifestFile 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ GPG signature created: $ManifestFile.asc" -ForegroundColor Green
    } else {
        Write-Host "⚠️  GPG signing failed (continuing): $GpgResult" -ForegroundColor Yellow
    }
} catch {
    Write-Host "⚠️  GPG signing error (continuing): $_" -ForegroundColor Yellow
}

# Create archive snapshot
Write-Host "📦 Creating archive snapshot..." -ForegroundColor Yellow
try {
    Compress-Archive -Path $Root -DestinationPath $Archive -Force -CompressionLevel Optimal
    $ArchiveSize = (Get-Item $Archive).Length / 1MB
    Write-Host "✅ Archive created: $Archive" -ForegroundColor Green
    Write-Host "   Size: $([math]::Round($ArchiveSize, 2)) MB" -ForegroundColor Cyan
} catch {
    Write-Host "❌ Error creating archive: $_" -ForegroundColor Red
    exit 1
}

# Update system status
$StatusFile = "$ArchiveBase\nightly-status.json"
$Status = @{
    timestamp = $DateStamp
    manifest = $ManifestFile
    archive = $Archive
    files_processed = $TotalFiles
    archive_size_mb = [math]::Round($ArchiveSize, 2)
    gpg_signed = Test-Path "$ManifestFile.asc"
} | ConvertTo-Json

$Status | Out-File -FilePath $StatusFile -Encoding UTF8

Write-Host ""
Write-Host "✅ NIGHTLY GOLDEN MASTER COMPLETE" -ForegroundColor Green
Write-Host "📁 Archive: $Archive" -ForegroundColor Cyan
Write-Host "🔐 Manifest: $ManifestFile" -ForegroundColor Cyan
Write-Host "📊 Status: $StatusFile" -ForegroundColor Cyan
Write-Host ""
Write-Host "🏆 Sovereign continuity achieved." -ForegroundColor Yellow
Write-Host "💾 Take the SSD off-site. Sleep." -ForegroundColor Yellow