[CmdletBinding()]
param(
  # Repository root (defaults to two levels up from this script)
  [string]$RepoRoot = '',

  # Manifest to verify. If omitted, auto-selects the newest repo_manifest_*.json under evidence/manifests.
  [string]$ManifestPath = '',

  # Directory containing *.RECEIPT.sha256 files
  [string]$ReceiptsDir = '',

  # Optional expected SITREP version string, e.g. "v1.5"
  [string]$ExpectedSITREPVersion = '',

  # If set, mismatch between SITREP Version and this value fails verification (not just WARN).
  [string]$RequiredSITREPVersion = '',

  # If set, require evidence/SITREP.md to reference the selected manifest filename.
  [switch]$RequireSITREPManifestMatch,

  # If set, require evidence/SITREP.md to declare a Version line.
  [switch]$RequireSITREPVersion,

  # If set, require at least one *.RECEIPT.sha256 file and fail if none are present.
  [switch]$RequireReceipts,

  # Where to write a JSON scorecard report (optional). If omitted, writes under evidence/verification.
  [string]$OutReport = ''
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Resolve-RepoRoot {
  if (-not [string]::IsNullOrWhiteSpace($RepoRoot)) {
    return (Resolve-Path -LiteralPath $RepoRoot).Path
  }
  return (Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
}

function Get-LatestManifest([string]$root) {
  $manDir = Join-Path $root 'evidence/manifests'
  if (-not (Test-Path -LiteralPath $manDir)) {
    throw "Manifests directory not found: $manDir"
  }

  $candidates = Get-ChildItem -LiteralPath $manDir -Filter 'repo_manifest_*.json' -File | Sort-Object Name
  if (-not $candidates -or @($candidates).Count -lt 1) {
    throw "No repo manifests found in: $manDir"
  }

  return $candidates[-1].FullName
}

function Read-Manifest([string]$path) {
  if (-not (Test-Path -LiteralPath $path)) {
    throw "Manifest not found: $path"
  }

  try {
    return Get-Content -LiteralPath $path -Raw | ConvertFrom-Json
  } catch {
    throw "Failed to parse manifest JSON ($path): $($_.Exception.Message)"
  }
}

function Get-Sha256([string]$path) {
  return (Get-FileHash -Algorithm SHA256 -LiteralPath $path).Hash.ToLower()
}

function ConvertFrom-ReceiptLine([string]$line) {
  $trim = $line.Trim()
  if ([string]::IsNullOrWhiteSpace($trim)) {
    return $null
  }

  # Support multiple formats:
  # 1. <hash><space(s)><path> (Standard sha256sum format)
  # 2. <filename>|<hash>|<timestamp>|<author> (Legacy/Codex pipe format)
  # 3. <hash><space(s)><filename><space(s)><timestamp> (codex_receipts.txt format)

  if ($trim -like '*|*') {
    $parts = $trim -split '\|'
    if (@($parts).Count -ge 2) {
      return [pscustomobject]@{
        Hash = $parts[1].Trim().ToLower()
        DisplayPath = $parts[0].Trim()
      }
    }
  }

  $parts = $trim -split '\s+'
  if (@($parts).Count -ge 2) {
    # Check if first part looks like a SHA256 (64 chars hex)
    if ($parts[0] -match '^[a-fA-F0-9]{64}$') {
        return [pscustomobject]@{
            Hash = $parts[0].ToLower()
            DisplayPath = $parts[1].Trim()
        }
    }
    # Check if second part looks like a SHA256 (e.g. filename hash ...)
    if ($parts[1] -match '^[a-fA-F0-9]{64}$') {
        return [pscustomobject]@{
            Hash = $parts[1].ToLower()
            DisplayPath = $parts[0].Trim()
        }
    }
  }

  throw "Invalid receipt line format: $trim"
}

function Get-SitrepDeclaredVersion([string]$repoRoot) {
  $sitrepPath = Join-Path $repoRoot 'evidence/SITREP.md'
  if (-not (Test-Path -LiteralPath $sitrepPath)) {
    return $null
  }

  $content = Get-Content -LiteralPath $sitrepPath -Raw
  # Accept:
  #   Version: v1.5
  #   Version = v1.5.2
  #   SITREP Version: v1.5
  $m = [regex]::Match(
    $content,
    '^\s*(?:(?:SITREP\s*)?Version)\s*[:=]\s*(v\d+(?:\.\d+){1,3})\b',
    [System.Text.RegularExpressions.RegexOptions]::IgnoreCase -bor [System.Text.RegularExpressions.RegexOptions]::Multiline
  )
  if ($m.Success) { return $m.Groups[1].Value.Trim() }
  return $null
}

function Get-SitrepReferencedManifest([string]$repoRoot) {
  $sitrepPath = Join-Path $repoRoot 'evidence/SITREP.md'
  if (-not (Test-Path -LiteralPath $sitrepPath)) {
    return $null
  }

  $content = Get-Content -LiteralPath $sitrepPath -Raw
  $m = [regex]::Match(
    $content,
    '(?m)^\s*[-*\u2022]?\s*Seal\s+manifest\s*:\s*([^\r\n]+)',
    [System.Text.RegularExpressions.RegexOptions]::IgnoreCase
  )
  if (-not $m.Success) { return $null }

  $raw = $m.Groups[1].Value.Trim()
  # Trim common wrappers like quotes/backticks/spaces and tolerate a path.
  $raw = $raw.Trim(@([char]96, [char]34, [char]39, [char]32, [char]92))
  $leaf = Split-Path -Leaf $raw
  if ([string]::IsNullOrWhiteSpace($leaf)) { return $null }
  return $leaf.Trim()
}

function Get-OptionalProp($obj, [string]$name) {
  if ($null -eq $obj) { return $null }
  $p = $obj.PSObject.Properties[$name]
  if ($null -eq $p) { return $null }
  return $p.Value
}

$repoRootResolved = Resolve-RepoRoot
Set-Location $repoRootResolved

if ([string]::IsNullOrWhiteSpace($ManifestPath)) {
  $ManifestPath = Get-LatestManifest $repoRootResolved
} else {
  $ManifestPath = (Resolve-Path -LiteralPath $ManifestPath).Path
}

if ([string]::IsNullOrWhiteSpace($ReceiptsDir)) {
  $ReceiptsDir = Join-Path $repoRootResolved 'evidence/receipts'
} else {
  $ReceiptsDir = (Resolve-Path -LiteralPath $ReceiptsDir).Path
}

if ([string]::IsNullOrWhiteSpace($OutReport)) {
  $stamp = (Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssZ')
  $outDir = Join-Path $repoRootResolved 'evidence/verification'
  if (-not (Test-Path -LiteralPath $outDir)) { New-Item -ItemType Directory -Force -Path $outDir | Out-Null }
  $OutReport = Join-Path $outDir ("verify_all_report_{0}.json" -f $stamp)
} else {
  $outDir = Split-Path -Parent $OutReport
  if ($outDir -and -not (Test-Path -LiteralPath $outDir)) { New-Item -ItemType Directory -Force -Path $outDir | Out-Null }
}

Write-Host '=== VERIFY ALL: Integrity Scorecard ===' -ForegroundColor Cyan
Write-Host "RepoRoot:   $repoRootResolved" -ForegroundColor DarkGray
Write-Host "Manifest:   $ManifestPath" -ForegroundColor DarkGray
Write-Host "Receipts:   $ReceiptsDir" -ForegroundColor DarkGray

$manifest = Read-Manifest $ManifestPath
if (-not $manifest.files) {
  throw "Manifest missing required property 'files'"
}

# Verify manifest entries
$fileResults = @()
$seen = @{}
foreach ($f in $manifest.files) {
  $rel = [string]$f.path
  $expected = ([string]$f.sha256).ToLower()

  if ([string]::IsNullOrWhiteSpace($rel) -or [string]::IsNullOrWhiteSpace($expected)) {
    $fileResults += [pscustomobject]@{ kind='manifest_file'; path=$rel; expected=$expected; actual=$null; status='FAIL'; reason='Missing path or sha256 in manifest entry' }
    continue
  }

  if ($seen.ContainsKey($rel)) {
    $fileResults += [pscustomobject]@{ kind='manifest_file'; path=$rel; expected=$expected; actual=$null; status='FAIL'; reason='Duplicate path entry in manifest' }
    continue
  }
  $seen[$rel] = $true

  $abs = Join-Path $repoRootResolved $rel
  if (-not (Test-Path -LiteralPath $abs)) {
    $fileResults += [pscustomobject]@{ kind='manifest_file'; path=$rel; expected=$expected; actual=$null; status='FAIL'; reason='File missing on disk' }
    continue
  }

  $actual = Get-Sha256 $abs
  if ($actual -eq $expected) {
    $fileResults += [pscustomobject]@{ kind='manifest_file'; path=$rel; expected=$expected; actual=$actual; status='OK'; reason='' }
  } else {
    $fileResults += [pscustomobject]@{ kind='manifest_file'; path=$rel; expected=$expected; actual=$actual; status='FAIL'; reason='SHA256 mismatch' }
  }
}

# Verify receipts
$receiptResults = @()
if (Test-Path -LiteralPath $ReceiptsDir) {
  $receiptFiles = Get-ChildItem -LiteralPath $ReceiptsDir -Filter '*.RECEIPT.sha256' -File | Sort-Object Name
  if (-not $receiptFiles -or @($receiptFiles).Count -lt 1) {
    $receiptResults += [pscustomobject]@{
      kind = 'receipt'
      receipt = $null
      displayPath = $null
      expected = $null
      actual = $null
      status = $(if ($RequireReceipts) { 'FAIL' } else { 'WARN' })
      reason = $(if ($RequireReceipts) { 'No receipt files found' } else { 'No receipt files found (non-fatal)' })
    }
  }
  foreach ($rf in $receiptFiles) {
    $line = (Get-Content -LiteralPath $rf.FullName -Raw)
    $parsed = ConvertFrom-ReceiptLine $line
    if ($null -eq $parsed) {
      $receiptResults += [pscustomobject]@{ kind='receipt'; receipt=$rf.Name; displayPath=$null; expected=$null; actual=$null; status='FAIL'; reason='Empty receipt file' }
      continue
    }

    $relPath = $parsed.DisplayPath
    $target = Join-Path $repoRootResolved $relPath
    
    if (-not (Test-Path -LiteralPath $target)) {
      # Try to find file by name if it's just a filename
      $fileName = Split-Path -Leaf $relPath
      $foundFiles = Get-ChildItem -Path $repoRootResolved -Filter $fileName -Recurse -File -ErrorAction SilentlyContinue
      if ($foundFiles) {
        $target = $foundFiles[0].FullName
      }
    }

    if (-not (Test-Path -LiteralPath $target)) {
      $receiptResults += [pscustomobject]@{ kind='receipt'; receipt=$rf.Name; displayPath=$parsed.DisplayPath; expected=$parsed.Hash; actual=$null; status='FAIL'; reason='Target file missing on disk' }
      continue
    }

    $actual = Get-Sha256 $target
    if ($actual -eq $parsed.Hash) {
      $receiptResults += [pscustomobject]@{ kind='receipt'; receipt=$rf.Name; displayPath=$parsed.DisplayPath; expected=$parsed.Hash; actual=$actual; status='OK'; reason='' }
    } else {
      $receiptResults += [pscustomobject]@{ kind='receipt'; receipt=$rf.Name; displayPath=$parsed.DisplayPath; expected=$parsed.Hash; actual=$actual; status='FAIL'; reason='SHA256 mismatch' }
    }
  }
} else {
  $receiptResults += [pscustomobject]@{ kind='receipt'; receipt=$null; displayPath=$null; expected=$null; actual=$null; status='FAIL'; reason="Receipts directory missing: $ReceiptsDir" }
}

# SITREP version alignment (informational)
$sitrepFound = Get-SitrepDeclaredVersion $repoRootResolved
$sitrepManifestRef = Get-SitrepReferencedManifest $repoRootResolved
$selectedManifestName = Split-Path -Leaf $ManifestPath

$sitrepCheck = [pscustomobject]@{
  kind = 'sitrep'
  foundVersion = $sitrepFound
  expectedVersion = $(if ([string]::IsNullOrWhiteSpace($ExpectedSITREPVersion)) { $null } else { $ExpectedSITREPVersion })
  requiredVersion = $(if ([string]::IsNullOrWhiteSpace($RequiredSITREPVersion)) { $null } else { $RequiredSITREPVersion })
  referencedManifest = $sitrepManifestRef
  selectedManifest = $selectedManifestName
  status = 'OK'
  reason = ''
}

if ($RequireSITREPVersion) {
  if ([string]::IsNullOrWhiteSpace($sitrepFound)) {
    $sitrepCheck.status = 'FAIL'
    $sitrepCheck.reason = 'SITREP does not declare a Version'
  }
}
if (-not [string]::IsNullOrWhiteSpace($ExpectedSITREPVersion)) {
  if ($sitrepFound -ne $ExpectedSITREPVersion) {
    $sitrepCheck.status = 'WARN'
    $sitrepCheck.reason = 'SITREP version does not match expectedVersion'
  }
}

if (-not [string]::IsNullOrWhiteSpace($RequiredSITREPVersion)) {
  if ($sitrepFound -ne $RequiredSITREPVersion) {
    $sitrepCheck.status = 'FAIL'
    $sitrepCheck.reason = 'SITREP version does not match requiredVersion'
  }
}

if ($RequireSITREPManifestMatch) {
  if ([string]::IsNullOrWhiteSpace($sitrepManifestRef)) {
    $sitrepCheck.status = 'FAIL'
    $sitrepCheck.reason = 'SITREP does not declare a seal manifest reference'
  } elseif ($sitrepManifestRef.Trim().ToLower() -ne $selectedManifestName.Trim().ToLower()) {
    $sitrepCheck.status = 'FAIL'
    $sitrepCheck.reason = 'SITREP seal manifest reference does not match selected manifest'
  }
}

# Scorecard
$manifestTotal = @($fileResults).Count
$manifestOk = @($fileResults | Where-Object { $_.status -eq 'OK' }).Count
$manifestFail = @($fileResults | Where-Object { $_.status -eq 'FAIL' }).Count

$receiptsTotal = @($receiptResults).Count
$receiptsOk = @($receiptResults | Where-Object { $_.status -eq 'OK' }).Count
$receiptsFail = @($receiptResults | Where-Object { $_.status -eq 'FAIL' }).Count

$sitrepFail = ($sitrepCheck.status -eq 'FAIL')
$integrityOk = ($manifestFail -eq 0 -and $receiptsFail -eq 0 -and -not $sitrepFail)

$report = [pscustomobject]@{
  generated_utc = (Get-Date).ToUniversalTime().ToString('o')
  repoRoot = $repoRootResolved
  manifestPath = (Resolve-Path -LiteralPath $ManifestPath).Path
  manifestMeta = [pscustomobject]@{
    generated_utc = $manifest.generated_utc
    hostname = $manifest.hostname
    phase = Get-OptionalProp $manifest 'phase'
    deployment_format = Get-OptionalProp $manifest 'deployment_format'
  }
  scorecard = [pscustomobject]@{
    manifest = [pscustomobject]@{ total=$manifestTotal; ok=$manifestOk; fail=$manifestFail }
    receipts = [pscustomobject]@{ total=$receiptsTotal; ok=$receiptsOk; fail=$receiptsFail }
    sitrep = $sitrepCheck
    integrity_ok = $integrityOk
  }
  details = [pscustomobject]@{
    manifest_files = $fileResults
    receipts = $receiptResults
  }
}

$report | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $OutReport -Encoding UTF8

Write-Host ''
Write-Host '--- SCORECARD ---' -ForegroundColor Cyan
Write-Host ("Manifest: {0} OK, {1} FAIL (Total {2})" -f $manifestOk, $manifestFail, $manifestTotal)
Write-Host ("Receipts: {0} OK, {1} FAIL (Total {2})" -f $receiptsOk, $receiptsFail, $receiptsTotal)
if ($sitrepCheck.expectedVersion) {
  Write-Host ("SITREP:   {0} (found={1}, expected={2})" -f $sitrepCheck.status, $sitrepCheck.foundVersion, $sitrepCheck.expectedVersion)
} else {
  Write-Host ("SITREP:   {0} (found={1})" -f $sitrepCheck.status, $sitrepCheck.foundVersion)
}

if ($sitrepCheck.requiredVersion) {
  Write-Host ("SITREP:   required={0}" -f $sitrepCheck.requiredVersion) -ForegroundColor DarkGray
}
if ($RequireSITREPManifestMatch) {
  Write-Host ("SITREP:   manifest_ref={0}" -f $sitrepCheck.referencedManifest) -ForegroundColor DarkGray
  Write-Host ("Manifest: selected={0}" -f $sitrepCheck.selectedManifest) -ForegroundColor DarkGray
}

if ($integrityOk) {
  Write-Host 'INTEGRITY: PASS' -ForegroundColor Green
} else {
  Write-Host 'INTEGRITY: FAIL' -ForegroundColor Red
}

Write-Host "Report: $OutReport" -ForegroundColor DarkGray

# Non-zero exit if strict integrity fails
if (-not $integrityOk) {
  exit 2
}
