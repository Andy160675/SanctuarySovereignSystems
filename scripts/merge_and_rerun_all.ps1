[CmdletBinding()]
param(
    [string]$RepoPath = "C:\Users\user\Downloads\SanctuarySovereignSystems",
    [Parameter(Mandatory = $true)][string]$SourceBranch,      # e.g. s3-ext-009-autonomous_build_command
    [Parameter(Mandatory = $true)][string]$ExtensionId,       # e.g. S3-EXT-009
    [Parameter(Mandatory = $true)][string]$ExtensionSlug,     # e.g. autonomous_build_command
    [string]$BaselineTag = "v1.0.0-kernel74",
    [switch]$RunQueueAfterMerge,
    [switch]$CreateMergeTag
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Fail([string]$m) { Write-Host "FAIL: $m" -ForegroundColor Red; exit 1 }
function Info([string]$m) { Write-Host "INFO: $m" -ForegroundColor Cyan }
function Ok([string]$m)   { Write-Host "OK:   $m" -ForegroundColor Green }

function Run([string[]]$cmd, [string]$logPath = "") {
    if ($cmd.Count -eq 0) { Fail "Empty command" }
    $exe = $cmd[0]
    $args = @()
    if ($cmd.Count -gt 1) { $args = $cmd[1..($cmd.Count - 1)] }

    $out = & $exe @args 2>$null
    if ($logPath) { $out | Tee-Object -FilePath $logPath -Append | Out-Host } else { $out | Out-Host }
    if ($LASTEXITCODE -ne 0) { Fail ("Command failed: " + ($cmd -join " ")) }
    return $out
}

if (-not (Test-Path -LiteralPath $RepoPath)) { Fail "RepoPath not found: $RepoPath" }
Set-Location -LiteralPath $RepoPath

Run @("git","rev-parse","--is-inside-work-tree")
Run @("git","fetch","--all","--tags")

# Clean tree gate
$dirty = git status --porcelain
if ($dirty) { Fail "Working tree is not clean. Commit/stash first." }

# Ensure branches available
Run @("git","checkout","main")
Run @("git","pull","--ff-only","origin","main")
Run @("git","rev-parse","--verify",$SourceBranch)

# Baseline tag gate in ancestry (merge-base must be contained by baseline tag)
$mergeBase = (Run @("git","merge-base","main",$SourceBranch) | Select-Object -Last 1).Trim()
$tagsContaining = Run @("git","tag","--contains",$mergeBase)
if (-not ($tagsContaining -match ("^" + [regex]::Escape($BaselineTag) + "$"))) {
    Fail "Baseline tag '$BaselineTag' not found in ancestry of merge-base $mergeBase"
}
Ok "Baseline ancestry gate passed: $BaselineTag"

# Scope gate: extension-only changes (plus evidence/procedure paths)
$diffFiles = Run @("git","diff","--name-only","main...$SourceBranch")
$allowed = @(
    "^sovereign_engine/extensions/$([regex]::Escape($ExtensionSlug))/",
    "^extensions/$([regex]::Escape($ExtensionId))/",
    "^evidence/$([regex]::Escape($ExtensionId))/",
    "^docs/procedures/rollback_$([regex]::Escape($ExtensionSlug))\.md$",
    "^audit/queue/",
    "^audit/merge/"
)

$unauthorized = @()
foreach ($f in $diffFiles) {
    $file = "$f".Trim()
    if (-not $file) { continue }
    $ok = $false
    foreach ($rx in $allowed) {
        if ($file -match $rx) { $ok = $true; break }
    }
    if (-not $ok) { $unauthorized += $file }
}
if ($unauthorized.Count -gt 0) {
    $unauthorized | Set-Content -Encoding UTF8 "audit\merge\unauthorized_${ExtensionId}.txt"
    Fail "Unauthorized changes detected outside extension scope."
}
Ok "Isolation gate passed (extension-only scope)"

# Evidence directory
$ts = Get-Date -Format "yyyyMMdd-HHmmss"
$eDir = "audit\merge\${ts}_${ExtensionId}"
New-Item -ItemType Directory -Force -Path $eDir | Out-Null

# Pre-merge validations on source branch
Run @("git","checkout",$SourceBranch)
$kernelLogPre = Join-Path $eDir "kernel_premerge.log"
$extLogPre = Join-Path $eDir "extension_premerge.log"

$kernelPre = Run @("python","-m","sovereign_engine.tests.run_all") $kernelLogPre
if (-not ($kernelPre -match "74/74")) { Fail "Pre-merge kernel validation did not report 74/74." }

Run @("python","-m","pytest","sovereign_engine/extensions/$ExtensionSlug","-q") $extLogPre

# Merge on main
Run @("git","checkout","main")
Run @("git","pull","--ff-only","origin","main")

$mergeMessage = @"
merge($ExtensionId): $ExtensionSlug under Phase-9 governance gate

Compliance:
- Kernel invariants preserved (74/74 pre-merge)
- Extension isolation scope verified
- Evidence path: $eDir
- Rollback procedure required in docs/procedures/rollback_$ExtensionSlug.md
"@

Run @("git","merge","--no-ff",$SourceBranch,"-m",$mergeMessage)

# Post-merge validations
$kernelLogPost = Join-Path $eDir "kernel_postmerge.log"
$kernelPost = Run @("python","-m","sovereign_engine.tests.run_all") $kernelLogPost
if (-not ($kernelPost -match "74/74")) { Fail "Post-merge kernel validation did not report 74/74." }

$extLogPost = Join-Path $eDir "extension_postmerge.log"
Run @("python","-m","pytest","sovereign_engine/extensions/$ExtensionSlug","-q") $extLogPost

# Performance no-regression gate (if baseline exists)
if (Test-Path "baseline_metrics.json") {
    $perfLog = Join-Path $eDir "performance_gate.log"
    Run @("python",".\scripts\validate_performance.py","--baseline","baseline_metrics.json","--threshold","no_regression") $perfLog
    Ok "Performance gate passed"
} else {
    Info "baseline_metrics.json not found; performance gate skipped."
}

# Manifest + SITREP
$manifest = Join-Path $eDir "manifest_sha256.txt"
$filesToHash = Get-ChildItem -Recurse -File $eDir | Select-Object -ExpandProperty FullName
$lines = foreach ($f in $filesToHash) {
    $h = Get-FileHash -Algorithm SHA256 -Path $f
    "{0}  {1}" -f $h.Hash, $h.Path
}
$lines | Set-Content -Encoding UTF8 $manifest

$head = (Run @("git","rev-parse","HEAD") | Select-Object -Last 1).Trim()
$short = (Run @("git","rev-parse","--short","HEAD") | Select-Object -Last 1).Trim()
$sitrep = @"
# SITREP — Merge Closure $ExtensionId

Timestamp: $(Get-Date -Format o)
Branch merged: $SourceBranch
Extension: $ExtensionId / $ExtensionSlug
Main HEAD: $head ($short)
Baseline tag: $BaselineTag

## Gates
- Isolation scope: PASS
- Kernel pre-merge: PASS (74/74)
- Kernel post-merge: PASS (74/74)
- Extension tests pre/post: PASS
- Performance no-regression: $(if (Test-Path "baseline_metrics.json") {"PASS"} else {"SKIPPED (no baseline_metrics.json)"})

## Evidence
- $eDir
- manifest_sha256.txt

## Decision
APPROVE-MERGED under Phase-9 constitutional protocol.
"@
$sitrepPath = Join-Path $eDir "POST_MERGE_SITREP.md"
$sitrep | Set-Content -Encoding UTF8 $sitrepPath

# Optional tag
if ($CreateMergeTag) {
    $tag = "s3-merged-$($ExtensionId.ToLower())-$ts"
    Run @("git","tag",$tag)
    Run @("git","push","origin",$tag)
    Ok "Created merge tag: $tag"
}

# Push merge
Run @("git","push","origin","main")
Ok "Merged and pushed main."

# Optional queue rerun
if ($RunQueueAfterMerge) {
    $queueScript = ".\scripts\run_s3_queue.ps1"
    if (-not (Test-Path $queueScript)) { Fail "Queue script missing: $queueScript" }
    Run @("powershell","-ExecutionPolicy","Bypass","-File",$queueScript,
          "-RepoPath",$RepoPath,
          "-BaselineRef",$BaselineTag,
          "-QueueFile","extensions/QUEUE_S3.json",
          "-Push","-CreatePr")
    Ok "Queue rerun complete."
}

Ok "All done. Evidence: $eDir"
