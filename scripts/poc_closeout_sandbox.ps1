param(
  [string]$RepoPath = ".",
  [string]$KernelTag = "v1.0.0-kernel74"
)

$ErrorActionPreference = "Stop"
function Fail($m){ Write-Host "FAIL: $m" -ForegroundColor Red; exit 1 }
function Ok($m){ Write-Host "OK: $m" -ForegroundColor Green }

Set-Location $RepoPath

$ts = Get-Date -Format "yyyyMMdd-HHmmss"
$outDir = Join-Path "audit/closeout" $ts
New-Item -ItemType Directory -Force -Path $outDir | Out-Null

# 1) Kernel tests
$testLog = Join-Path $outDir "TEST_RUN.log"
python -m sovereign_engine.tests.run_all *>&1 | Tee-Object -FilePath $testLog
if ($LASTEXITCODE -ne 0) { Fail "Test harness failed." }
Ok "Test harness exit code PASS."

# 2) Tag check
$tag = git tag --list $KernelTag
if (-not $tag) { Fail "Missing required tag $KernelTag" }
Ok "Tag present: $KernelTag"

# 3) Required docs check
$required = @(
  "SEASONS.md",
  "ROADMAP.md",
  "docs/STATUS.md",
  "docs/INTEGRATION_CLOSEOUT_S2_to_S3.md",
  "docs/RELEASE_NOTES_v1.0.0-kernel74.md"
)
foreach ($f in $required) {
  if (-not (Test-Path $f)) { Fail "Missing required artifact: $f" }
}
Ok "Required governance artifacts present."

# 4) Snapshot metadata
$head = (git rev-parse HEAD).Trim()
$branch = (git branch --show-current).Trim()
$sitrep = Join-Path $outDir "CLOSEOUT_SITREP.md"

$sitrepContent = @"
# CLOSEOUT SITREP
Timestamp: $ts
Branch: $branch
HEAD: $head
Kernel Tag: $KernelTag

## Verification
- Test Harness: PASS
- Tag Check: PASS
- Artifact Check: PASS

## Decision
GO: Season 2 sealed, Season 3 governance intake active.
"@ 

$sitrepContent | Set-Content -Path $sitrep -Encoding UTF8

# 5) Hash manifest
$manifest = Join-Path $outDir "MANIFEST_SHA256.txt"
$allFiles = @($sitrep, $testLog) + ($required | ForEach-Object { Resolve-Path $_ | Select-Object -ExpandProperty Path })
$allFiles | ForEach-Object {
  $h = Get-FileHash -Algorithm SHA256 -Path $_
  "{0}  {1}" -f $h.Hash, $h.Path
} | Set-Content -Path $manifest -Encoding UTF8

Ok "POC close-out complete."
Write-Host "Artifacts: $outDir" -ForegroundColor Cyan
