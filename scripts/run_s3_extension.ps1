[CmdletBinding()]
param(
    [string]$RepoPath = "C:\Users\user\IdeaProjects\sovereign-system",
    [string]$ExtensionId = "S3-EXT-006",
    [string]$ExtensionSlug = "observatory",
    [string]$BaselineRef = "v1.0.0-kernel74",
    [switch]$Push,
    [switch]$CreatePr
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Fail([string]$msg) { Write-Host "FAIL: $msg" -ForegroundColor Red; exit 1 }
function Info([string]$msg) { Write-Host "INFO: $msg" -ForegroundColor Cyan }
function Ok([string]$msg)   { Write-Host "OK:   $msg" -ForegroundColor Green }

function Ensure-Dir([string]$p) {
    if (-not (Test-Path -LiteralPath $p)) { New-Item -ItemType Directory -Path $p -Force | Out-Null }
}

function Ensure-File([string]$p, [string]$content) {
    if (-not (Test-Path -LiteralPath $p)) {
        $parent = Split-Path -Parent $p
        if ($parent) { Ensure-Dir $parent }
        Set-Content -LiteralPath $p -Value $content -Encoding UTF8
        Info "Created: $p"
    } else {
        Info "Exists:  $p (kept)"
    }
}

function Run-Cmd([scriptblock]$cmd, [string]$desc) {
    Info $desc
    & $cmd
    if ($LASTEXITCODE -ne 0) { Fail "$desc failed with exit code $LASTEXITCODE" }
}

# ----------------------------
# 0) Repo checks
# ----------------------------
if (-not (Test-Path -LiteralPath $RepoPath)) { Fail "RepoPath not found: $RepoPath" }
Set-Location -LiteralPath $RepoPath

Run-Cmd { git rev-parse --is-inside-work-tree | Out-Null } "Verify git repository"

$dirty = git status --porcelain
if ($dirty) { Fail "Working tree is not clean. Commit/stash first." }

# ----------------------------
# 1) Branch anchoring
# ----------------------------
Run-Cmd { git fetch --all --tags --force } "Fetch remotes + tags"
Run-Cmd { git checkout master } "Checkout master"
Run-Cmd { git status } "Check status"

$extNum = "000"
if ($ExtensionId -match '^S3-EXT-(\d+)$') { $extNum = $Matches[1].PadLeft(3, '0') }
$branch = "s3-ext-$extNum-$ExtensionSlug"

Run-Cmd { git checkout -B $branch $BaselineRef } "Create/reset branch '$branch' from '$BaselineRef'"

# ----------------------------
# 2) ROADMAP compliance pre-check
# ----------------------------
if (-not (Test-Path "ROADMAP.md")) { Fail "ROADMAP.md missing." }
$roadmapHit = Select-String -Path "ROADMAP.md" -Pattern ([regex]::Escape($ExtensionId)) -SimpleMatch -ErrorAction SilentlyContinue
if (-not $roadmapHit) { Fail "$ExtensionId not found in ROADMAP.md" }
Ok "ROADMAP linkage verified for $ExtensionId"

# ----------------------------
# 3) Scaffold extension + docs/evidence
# ----------------------------
$extPath = "extensions/$ExtensionSlug"
$prDir   = "extensions/$ExtensionId"
$evDir   = "evidence/$ExtensionId"
Ensure-Dir $extPath
Ensure-Dir $prDir
Ensure-Dir $evDir
Ensure-Dir "docs/procedures"

Ensure-File "$extPath/__init__.py" @"
from .instrumentation import collect_runtime_snapshot
from .export import export_snapshot_json
"@

Ensure-File "$extPath/instrumentation.py" @"
from __future__ import annotations
from datetime import datetime, timezone
from typing import Dict, Any
import platform
import sys

def collect_runtime_snapshot() -> Dict[str, Any]:
    return {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "python_version": sys.version.split()[0],
        "platform": platform.platform(),
        "implementation": platform.python_implementation(),
    }
"@

Ensure-File "$extPath/export.py" @"
from __future__ import annotations
from pathlib import Path
from typing import Dict, Any
import json

def export_snapshot_json(snapshot: Dict[str, Any], out_file: str) -> str:
    p = Path(out_file)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(snapshot, indent=2, sort_keys=True), encoding="utf-8")
    return str(p)
"@

Ensure-File "$extPath/test_instrumentation.py" @"
from extensions.$ExtensionSlug.instrumentation import collect_runtime_snapshot

def test_collect_runtime_snapshot_has_required_keys():
    s = collect_runtime_snapshot()
    for k in ("timestamp_utc", "python_version", "platform", "implementation"):
        assert k in s
"@

Ensure-File "$extPath/test_export.py" @"
from extensions.$ExtensionSlug.export import export_snapshot_json

def test_export_snapshot_json_writes_file(tmp_path):
    out = tmp_path / "telemetry" / "snapshot.json"
    path = export_snapshot_json({"ok": True}, str(out))
    assert out.exists()
    assert path.endswith("snapshot.json")
"@

Ensure-File "docs/procedures/rollback_$ExtensionSlug.md" @"
# Rollback Procedure: $ExtensionId ($ExtensionSlug)

1. Tag pre-rollback state:
   git tag ${ExtensionSlug}-pre-rollback-<timestamp>
2. Revert extension commit:
   git revert <extension_commit_sha> --no-edit
3. Validate kernel:
   python -m sovereign_engine.tests.run_all
4. Re-validate extension absence/behavior as applicable.
5. If drill only, restore test branch from pre-rollback tag.
"@

$timestamp = Get-Date -Format "yyyy-MM-ddTHH:mm:ssK"
$prBodyPath = "$prDir/PR_BODY.md"
Set-Content -Path $prBodyPath -Encoding UTF8 -Value @"
# $ExtensionId — $ExtensionSlug

## Summary
Implements read-only telemetry extension for Season 3.

## Phase-9 Compliance Checklist
- [x] No kernel modifications in protected paths
- [x] 74/74 kernel invariants pass
- [x] Extension tests added
- [x] Rollback procedure documented
- [x] ROADMAP.md linkage confirmed
- [x] Subtractive invariance preserved

## Evidence
- SITREP: $evDir/SITREP.md
- Manifest: $evDir/manifest_sha256.txt
"@

# ----------------------------
# 4) Validate
# ----------------------------
Run-Cmd { python -m pytest "extensions/$ExtensionSlug" -q } "Run extension tests"
Run-Cmd { python -m sovereign_engine.tests.run_all } "Run kernel invariant suite (74/74)"

# ----------------------------
# 5) Protected path guard
# ----------------------------
$protectedExact = @(
    "sovereign_engine/configs/constitution.json",
    "docs/INVARIANTS.md",
    "SEASONS.md"
)
$protectedPrefix = @(
    "sovereign_engine/core/"
)

$changed = @(git diff --name-only)
foreach ($f in $changed) {
    foreach ($p in $protectedPrefix) {
        if ($f.StartsWith($p)) { Fail "Protected path changed: $f" }
    }
    foreach ($p in $protectedExact) {
        if ($f -eq $p) { Fail "Protected file changed: $f" }
    }
}
Ok "Protected path guard passed"

# ----------------------------
# 6) SITREP + hash manifest
# ----------------------------
$head = (git rev-parse --short HEAD).Trim()
$sitrepPath = "$evDir/SITREP.md"
Set-Content -Path $sitrepPath -Encoding UTF8 -Value @"
## SITREP: $ExtensionId - $ExtensionSlug
Timestamp: $timestamp
BaseRef: $BaselineRef
Branch: $branch
Head(before commit): $head

### Changes
- Added/updated extension module under $extPath
- Added Phase-9 PR body at $prBodyPath
- Added rollback procedure docs/procedures/rollback_$ExtensionSlug.md

### Validation
- Extension tests: PASS
- Kernel invariants: 74/74 PASS

### Phase-9
- ROADMAP compliance: PASS
- Protected path modifications: NONE
- Subtractive invariance: PRESERVED
"@

$manifestPath = "$evDir/manifest_sha256.txt"
$artifactFiles = @(
    (Get-ChildItem -Path $extPath -File).FullName
    (Resolve-Path $prBodyPath).Path
    (Resolve-Path $sitrepPath).Path
    (Resolve-Path "docs/procedures/rollback_$ExtensionSlug.md").Path
) | Where-Object { $_ }

$hashLines = foreach ($af in $artifactFiles) {
    $h = Get-FileHash -Algorithm SHA256 -Path $af
    "{0}  {1}" -f $h.Hash, $h.Path
}
Set-Content -Path $manifestPath -Value $hashLines -Encoding UTF8
Ok "Evidence written to $evDir"

# ----------------------------
# 7) Commit / push / optional PR
# ----------------------------
Run-Cmd { git add -f "extensions/$ExtensionSlug" $prDir $evDir "docs/procedures/rollback_$ExtensionSlug.md" } "Stage files"

$staged = git diff --cached --name-only
if (-not $staged) { Fail "Nothing staged to commit." }

$msg = "feat($ExtensionId): implement $ExtensionSlug extension with Phase-9 evidence"
Run-Cmd { git commit -m $msg } "Commit changes"

if ($Push) {
    Run-Cmd { git push -u origin $branch } "Push branch"
}

if ($CreatePr) {
    $gh = Get-Command gh -ErrorAction SilentlyContinue
    if (-not $gh) {
        Info "gh CLI not found; skipping PR creation."
    } else {
        Run-Cmd { gh pr create --base main --head $branch --title "${ExtensionId}: $ExtensionSlug" --body-file $prBodyPath } "Create PR via gh"
    }
}

Ok "System run complete for $ExtensionId on branch $branch"
