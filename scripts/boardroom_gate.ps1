param(
  [string]$RepoPath = "C:\Users\user\IdeaProjects\sovereign-system"
)

$ErrorActionPreference = "Stop"
Set-Location $RepoPath

Write-Host "=== S3 Boardroom Gate ==="

# 1) kernel invariants
python -m sovereign_engine.tests.run_all | Tee-Object -FilePath "audit\boardroom_gate_kernel.log"
if ($LASTEXITCODE -ne 0) { throw "Kernel invariants failed." }

# 2) locate latest verdict
$root = Join-Path $RepoPath "audit\boardroom"
if (!(Test-Path $root)) { throw "Missing audit\boardroom evidence." }

$latest = Get-ChildItem $root -Directory | Sort-Object Name -Descending | Select-Object -First 1
if ($null -eq $latest) { throw "No boardroom runs found." }

$verdictFile = Join-Path $latest.FullName "BOARDROOM_VERDICT.json"
if (!(Test-Path $verdictFile)) { throw "Missing BOARDROOM_VERDICT.json." }

$data = Get-Content $verdictFile -Raw | ConvertFrom-Json
$final = $data.final.final

Write-Host "Latest decision final verdict: $final"
Write-Host "Evidence: $verdictFile"

if ($final -eq "HALT") { throw "Boardroom verdict HALT. Merge blocked." }

Write-Host "Boardroom gate passed."
exit 0
