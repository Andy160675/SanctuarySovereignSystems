[CmdletBinding()]
param(
  # Optional deterministic stamp, e.g. 20260204T030617Z
  [string]$ManifestStamp = '',

  # Rebuild immutable control-plane zip as part of the build.
  [switch]$RebuildImmutablePackage,

  # Version for Build-ImmutablePackage.ps1 (only used when -RebuildImmutablePackage is set)
  [string]$PackageVersion = '1.0.0'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Invoke-Step([string]$name, [scriptblock]$action, [switch]$ContinueOnError) {
  Write-Host ("=== {0} ===" -f $name) -ForegroundColor Cyan
  try {
    & $action
    Write-Host ("[OK] {0}" -f $name) -ForegroundColor Green
    return $true
  } catch {
    Write-Host ("[FAIL] {0}: {1}" -f $name, $_.Exception.Message) -ForegroundColor Red
    if (-not $ContinueOnError) { throw }
    return $false
  }
}

function Update-SitrepSealManifest([string]$sitrepPath, [string]$manifestName) {
  $content = Get-Content -LiteralPath $sitrepPath -Raw
  $pattern = '^(?:-\s*Seal\s+manifest\s*:\s*).*$'

  if ([regex]::IsMatch($content, $pattern, [System.Text.RegularExpressions.RegexOptions]::IgnoreCase -bor [System.Text.RegularExpressions.RegexOptions]::Multiline)) {
    $updated = [regex]::Replace(
      $content,
      $pattern,
      ("- Seal manifest: {0}" -f $manifestName),
      [System.Text.RegularExpressions.RegexOptions]::IgnoreCase -bor [System.Text.RegularExpressions.RegexOptions]::Multiline
    )
  } else {
    $suffix = "`r`n- Seal manifest: {0}`r`n" -f $manifestName
    $updated = $content.TrimEnd() + $suffix
  }

  if ($updated -ne $content) {
    Set-Content -LiteralPath $sitrepPath -Encoding UTF8 -Value $updated
  }
}

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
Set-Location $repoRoot

$stamp = if ([string]::IsNullOrWhiteSpace($ManifestStamp)) {
  (Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssZ')
} else {
  $ManifestStamp.Trim()
}

$hostName = $env:COMPUTERNAME
$manifestName = ("repo_manifest_{0}_{1}.json" -f $hostName, $stamp)
$manifestPath = Join-Path $repoRoot (Join-Path 'evidence/manifests' $manifestName)

# 1) Healthcheck (non-fatal)
Invoke-Step 'Healthcheck (Local)' {
  & powershell -NoProfile -ExecutionPolicy Bypass -File "$repoRoot/scripts/Healthcheck.ps1"
  if ($LASTEXITCODE -ne 0) { throw "Healthcheck failed ($LASTEXITCODE)" }
} -ContinueOnError | Out-Null

# 2) Dependency lockfile preflight (non-fatal; repo may not use lockfiles yet)
Invoke-Step 'Preflight: Dependency Lockfiles (advisory)' {
  & powershell -NoProfile -ExecutionPolicy Bypass -File "$repoRoot/scripts/Preflight-DependencyLockfiles.ps1" -Root "$repoRoot"
  if ($LASTEXITCODE -ne 0) {
    Write-Warning "Dependency lockfile preflight failed ($LASTEXITCODE). This is advisory in Citadel local builds."
  }
} -ContinueOnError | Out-Null

# 3) Run test suite (fatal if deterministic fails)
Invoke-Step 'Empathy Tests (Headless)' {
  & powershell -NoProfile -ExecutionPolicy Bypass -File "$repoRoot/scripts/Run-Empathy-Tests.ps1"
  if ($LASTEXITCODE -ne 0) { throw "Empathy tests failed ($LASTEXITCODE)" }
} | Out-Null

# 4) Seal Phase 2.5 engine evidence capsule (local)
Invoke-Step 'Seal Phase 2.5 Engine (Local Evidence)' {
  & powershell -NoProfile -ExecutionPolicy Bypass -File "$repoRoot/scripts/ops/seal_phase2_5_engine.ps1"
  if ($LASTEXITCODE -ne 0) { throw "Phase 2.5 seal failed ($LASTEXITCODE)" }
} | Out-Null

# 5) Optional: rebuild immutable package
if ($RebuildImmutablePackage) {
  Invoke-Step ("Build Immutable Package ({0})" -f $PackageVersion) {
    & powershell -NoProfile -ExecutionPolicy Bypass -File "$repoRoot/deploy/Build-ImmutablePackage.ps1" -Version $PackageVersion
    if ($LASTEXITCODE -ne 0) { throw "Immutable package build failed ($LASTEXITCODE)" }
  } | Out-Null
}

# 6) Update SITREP to reference the (about-to-be-written) manifest
$sitrepPath = Join-Path $repoRoot 'evidence/SITREP.md'
Invoke-Step 'Update SITREP Seal Manifest Reference' {
  Update-SitrepSealManifest -sitrepPath $sitrepPath -manifestName $manifestName
} | Out-Null

# 7) Write SITREP receipt
Invoke-Step 'Receipt: SITREP' {
  & powershell -NoProfile -ExecutionPolicy Bypass -File "$repoRoot/scripts/ops/Write-Sha256-Receipt.ps1" `
    -InputFile $sitrepPath `
    -OutputFile (Join-Path $repoRoot 'evidence/receipts/SITREP.md.RECEIPT.sha256') `
    -DisplayPath 'evidence/SITREP.md'
  if ($LASTEXITCODE -ne 0) { throw "SITREP receipt failed ($LASTEXITCODE)" }
} | Out-Null

# 8) Generate repo manifest with the same stamp
Invoke-Step 'Generate Repo Manifest' {
  & powershell -NoProfile -ExecutionPolicy Bypass -File "$repoRoot/scripts/make_repo_manifest.ps1" -ManifestStamp $stamp
  if ($LASTEXITCODE -ne 0) { throw "Manifest generation failed ($LASTEXITCODE)" }
} | Out-Null

# 9) Verify integrity strictly
Invoke-Step 'Verify-All (Strict)' {
  & powershell -NoProfile -ExecutionPolicy Bypass -File "$repoRoot/scripts/ops/Verify-All.ps1" `
    -ManifestPath $manifestPath `
    -RequireSITREPManifestMatch `
    -RequireSITREPVersion `
    -RequireReceipts
  if ($LASTEXITCODE -ne 0) { throw "Verify-All failed ($LASTEXITCODE)" }
} | Out-Null

Write-Host "DONE: Citadel build complete." -ForegroundColor Green
Write-Host ("Manifest: {0}" -f $manifestPath) -ForegroundColor DarkGray
