<#
.SYNOPSIS
  Bumps policy_rev in policy/revision.json and updates critical hashes.

.DESCRIPTION
  - Computes current hashes of security-critical files.
  - Updates policy_rev (defaults to current UTC date).
  - Updates security_critical_hashes in policy/revision.json.
  - Appends to CHANGELOG.md.

.USAGE
  powershell -File tools\bump_policy_rev.ps1 -Message "Hardened governance patterns"
#>

[CmdletBinding()]
param(
  [string]$RepoRoot = (Get-Location).Path,
  [Parameter(Mandatory=$true)][string]$Message
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$RevisionPath = Join-Path $RepoRoot "policy\revision.json"
if (-not (Test-Path $RevisionPath)) { throw "policy/revision.json not found." }

$Revision = Get-Content $RevisionPath | ConvertFrom-Json

# Define security-critical files
$CriticalFiles = @(
  "governance.py",
  "tests\red_team\test_tool_abuse.py",
  "tests\red_team\test_prompt_injection.py",
  "tests\test_st_michael.py",
  "src\core\config.py"
)

# 1. Update hashes
$newHashes = @{}
foreach ($file in $CriticalFiles) {
  $fullPath = Join-Path $RepoRoot $file
  if (Test-Path $fullPath) {
    $newHashes[$file] = (Get-FileHash -Algorithm SHA256 -Path $fullPath).Hash.ToLowerInvariant()
  }
}
$Revision.security_critical_hashes = $newHashes

# 2. Bump policy_rev
$date = Get-Date -Format "yyyy.MM.dd"
$existingRev = $Revision.policy_rev
if ($existingRev -match "^$date\.(\d+)$") {
  $seq = [int]$Matches[1] + 1
  $newRev = "$date.$seq"
} else {
  $newRev = "$date.1"
}
$Revision.policy_rev = $newRev

# 3. Save revision.json
$Revision | ConvertTo-Json -Depth 10 | Out-File -FilePath $RevisionPath -Encoding UTF8

# 4. Update CHANGELOG.md
$changelogPath = Join-Path $RepoRoot "CHANGELOG.md"
if (Test-Path $changelogPath) {
  $entry = "- [POLICY] ${newRev}: $Message"
  Add-Content -Path $changelogPath -Value $entry
}

Write-Host "Policy bumped: $existingRev -> $newRev" -ForegroundColor Green
Write-Host "Security hashes updated in policy/revision.json"
