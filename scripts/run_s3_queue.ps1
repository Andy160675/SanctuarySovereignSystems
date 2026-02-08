[CmdletBinding()]
param(
    [string]$RepoPath = "C:\Users\user\Downloads\SanctuarySovereignSystems",
    [string]$BaselineRef = "v1.0.0-kernel74",
    [string]$QueueFile = "extensions/QUEUE_S3.json",
    [switch]$Push,
    [switch]$CreatePr,
    [switch]$ContinueOnFailure
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Fail([string]$msg) { Write-Host "FAIL: $msg" -ForegroundColor Red; exit 1 }
function Info([string]$msg) { Write-Host "INFO: $msg" -ForegroundColor Cyan }
function Ok([string]$msg)   { Write-Host "OK:   $msg" -ForegroundColor Green }

if (-not (Test-Path -LiteralPath $RepoPath)) { Fail "RepoPath not found: $RepoPath" }
Set-Location -LiteralPath $RepoPath

$runner = Join-Path $RepoPath "scripts\run_s3_extension.ps1"
if (-not (Test-Path -LiteralPath $runner)) {
    Fail "Missing required runner: $runner"
}

# Create default queue if missing (deterministic order)
if (-not (Test-Path -LiteralPath $QueueFile)) {
    $defaultQueue = @(
        @{ id = "S3-EXT-001"; slug = "confluence";  enabled = $true  },
        @{ id = "S3-EXT-002"; slug = "vestibule";   enabled = $true  },
        @{ id = "S3-EXT-003"; slug = "tribunal";    enabled = $true  },
        @{ id = "S3-EXT-004"; slug = "gazette";     enabled = $true  },
        @{ id = "S3-EXT-005"; slug = "bazaar";      enabled = $true  },
        @{ id = "S3-EXT-006"; slug = "observatory"; enabled = $true  }
    )
    $json = $defaultQueue | ConvertTo-Json -Depth 5
    $dir = Split-Path -Parent $QueueFile
    if ($dir -and -not (Test-Path -LiteralPath $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
    Set-Content -Path $QueueFile -Value $json -Encoding UTF8
    Info "Created default queue file: $QueueFile"
}

# Load queue
$queueRaw = Get-Content -Path $QueueFile -Raw -Encoding UTF8
$queue = $queueRaw | ConvertFrom-Json
if (-not $queue) { Fail "Queue file is empty/invalid: $QueueFile" }

# Verify strict ordering by ID
$expected = @("S3-EXT-001","S3-EXT-002","S3-EXT-003","S3-EXT-004","S3-EXT-005","S3-EXT-006")
$actualEnabled = @($queue | Where-Object { $_.enabled -ne $false } | ForEach-Object { $_.id })
$actualSorted = $actualEnabled | Sort-Object
if (-not ($actualEnabled -join "," -eq ($expected | Where-Object { $actualEnabled -contains $_ } -join ","))) {
    Fail "Queue order must be strict ascending extension IDs. Current enabled order: $($actualEnabled -join ', ')"
}

# Verify clean tree before queue run
$dirty = git status --porcelain
if ($dirty) { Fail "Working tree not clean. Commit/stash first." }

$ts = Get-Date -Format "yyyyMMdd-HHmmss"
$outDir = Join-Path "audit/queue" $ts
New-Item -ItemType Directory -Path $outDir -Force | Out-Null
$runLog = Join-Path $outDir "QUEUE_RUN.log"
$sitrep = Join-Path $outDir "QUEUE_SITREP.md"

$results = @()
$start = Get-Date

Add-Content -Path $runLog -Value "Queue Start: $start"
Add-Content -Path $runLog -Value "BaselineRef: $BaselineRef"
Add-Content -Path $runLog -Value "QueueFile: $QueueFile"

foreach ($item in $queue) {
    if ($item.enabled -eq $false) {
        Info "Skipping disabled item: $($item.id)"
        continue
    }

    $id = [string]$item.id
    $slug = [string]$item.slug
    if (-not $id -or -not $slug) { Fail "Queue item missing id/slug." }

    Info "Running $id ($slug)..."
    Add-Content -Path $runLog -Value "START $id $slug $(Get-Date -Format o)"

    try {
        & powershell -NoProfile -ExecutionPolicy Bypass -File $runner `
            -RepoPath $RepoPath `
            -ExtensionId $id `
            -ExtensionSlug $slug `
            -BaselineRef $BaselineRef `
            @($Push ? "-Push" : $null) `
            @($CreatePr ? "-CreatePr" : $null)

        if ($LASTEXITCODE -ne 0) {
            throw "Runner exit code: $LASTEXITCODE"
        }

        $head = (git rev-parse --short HEAD).Trim()
        $results += [pscustomobject]@{
            id = $id; slug = $slug; status = "PASS"; head = $head; timestamp = (Get-Date).ToString("o")
        }
        Add-Content -Path $runLog -Value "PASS  $id $slug $head $(Get-Date -Format o)"
        Ok "$id PASS at $head"
    }
    catch {
        $head = (git rev-parse --short HEAD).Trim()
        $results += [pscustomobject]@{
            id = $id; slug = $slug; status = "FAIL"; head = $head; error = $_.Exception.Message; timestamp = (Get-Date).ToString("o")
        }
        Add-Content -Path $runLog -Value "FAIL  $id $slug $head $($_.Exception.Message) $(Get-Date -Format o)"
        Write-Host "FAIL at $id: $($_.Exception.Message)" -ForegroundColor Red

        if (-not $ContinueOnFailure) {
            Info "Halting queue (Stop-on-first-failure is active)."
            break
        }
    }
}

$end = Get-Date
$passCount = @($results | Where-Object { $_.status -eq "PASS" }).Count
$failCount = @($results | Where-Object { $_.status -eq "FAIL" }).Count
$total = @($results).Count

# Write SITREP
$lines = @()
$lines += "# QUEUE SITREP"
$lines += "Start: $($start.ToString('o'))"
$lines += "End:   $($end.ToString('o'))"
$lines += "BaselineRef: $BaselineRef"
$lines += "QueueFile: $QueueFile"
$lines += ""
$lines += "## Summary"
$lines += "- Total executed: $total"
$lines += "- Passed: $passCount"
$lines += "- Failed: $failCount"
$lines += "- Mode: " + ($(if ($ContinueOnFailure) { "continue-on-failure" } else { "halt-on-first-failure" }))
$lines += ""
$lines += "## Results"
foreach ($r in $results) {
    $err = if ($r.PSObject.Properties.Name -contains "error") { " | error: $($r.error)" } else { "" }
    $lines += "- $($r.id) ($($r.slug)): $($r.status) | head: $($r.head) | ts: $($r.timestamp)$err"
}
$lines | Set-Content -Path $sitrep -Encoding UTF8

# Save JSON results
$resultsJson = Join-Path $outDir "QUEUE_RESULTS.json"
$results | ConvertTo-Json -Depth 5 | Set-Content -Path $resultsJson -Encoding UTF8

# Hash manifest
$manifest = Join-Path $outDir "MANIFEST_SHA256.txt"
$filesToHash = @($runLog, $sitrep, $resultsJson)
$hashLines = foreach ($f in $filesToHash) {
    $h = Get-FileHash -Algorithm SHA256 -Path $f
    "{0}  {1}" -f $h.Hash, (Resolve-Path $f).Path
}
$hashLines | Set-Content -Path $manifest -Encoding UTF8

if ($failCount -gt 0 -and -not $ContinueOnFailure) {
    Fail "Queue halted due to failure. See $sitrep"
}

Ok "Queue completed. SITREP: $sitrep"
Write-Host "Artifacts: $outDir" -ForegroundColor Cyan
