[CmdletBinding()]
param(
    [string]$RepoRoot = "",
    [string]$OutFile = "evidence/gaps/AUDIT_GAPS.md"
)

$ErrorActionPreference = 'Stop'

if ([string]::IsNullOrWhiteSpace($RepoRoot)) {
    $RepoRoot = (Resolve-Path $PSScriptRoot\..\..).Path
}

Write-Host "--- AGENT 5: SKEPTIC AUDITOR ---" -ForegroundColor Cyan
Write-Host "Searching for evidence gaps..." -ForegroundColor Gray

$Gaps = @()

# Gap 1: Missing Canon Deployment Protocol (as noted in earlier telemetry)
if (-not (Test-Path (Join-Path $RepoRoot "CANON/TRINITY_DEPLOYMENT_PROTOCOL.md"))) {
    $Gaps += @{ 
        Area = "Core Protocol"; 
        Gap = "TRINITY_DEPLOYMENT_PROTOCOL.md is missing from CANON."; 
        Impact = "Unable to verify physical deployment invariants." 
    }
}

# Gap 2: Check for untracked scripts in critical paths
$criticalScripts = Get-ChildItem -Path (Join-Path $RepoRoot "scripts/ops") -File
foreach ($s in $criticalScripts) {
    if ($s.Name -match "Temp|test") {
        $Gaps += @{ 
            Area = "Operational Security"; 
            Gap = "Potential transient script found in production path: $($s.Name)"; 
            Impact = "Possible unauthorized code execution path." 
        }
    }
}

# Gap 3: Missing Operator Contract
if (-not (Test-Path (Join-Path $RepoRoot "docs/governance/OPERATOR_CONTRACT.md"))) {
    $Gaps += @{ 
        Area = "Accountability"; 
        Gap = "OPERATOR_CONTRACT.md not found."; 
        Impact = "Authority chain remains informal, not legally/procedurally bound." 
    }
}

# Write Gaps report
$MdContent = "# Sovereign System Audit Gaps`n`n"
$MdContent += "> Disagreement or absence is signal. Missing evidence is logged, not hidden.`n`n"
$MdContent += "| Focus Area | Identified Gap | Impact / Risk |`n"
$MdContent += "|------------|----------------|---------------|`n"

if ($Gaps.Count -eq 0) {
    $MdContent += "| N/A | No significant gaps identified in current scan. | GREEN |`n"
} else {
    foreach ($g in $Gaps) {
        $MdContent += "| $($g.Area) | $($g.Gap) | $($g.Impact) |`n"
    }
}

$MdContent | Set-Content -Path (Join-Path $RepoRoot $OutFile) -Encoding UTF8

Write-Host "Audit Gaps report written to: $OutFile" -ForegroundColor Yellow
