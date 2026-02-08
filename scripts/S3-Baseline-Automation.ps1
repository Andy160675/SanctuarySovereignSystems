# ================================
# Sanctuary Sovereign Systems
# Season 3 Baseline Automation (Adapted)
# ================================

$repoPath = "C:\Users\user\IdeaProjects\sovereign-system"
$timestamp = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
$evidenceDir = "$repoPath\audit\S3-baseline-$timestamp"

# Create evidence directory
New-Item -ItemType Directory -Force -Path $evidenceDir | Out-Null

Write-Host "=== Sanctuary Sovereign Systems: Season 3 Baseline Run ===" -ForegroundColor Cyan
Write-Host "Repository: $repoPath"
Write-Host "Evidence Directory: $evidenceDir"
Write-Host ""

# 1. Navigate to repo
Set-Location $repoPath

# 2. Capture current commit hash
Write-Host "Capturing current commit..."
$commit = git rev-parse HEAD
$commit | Out-File "$evidenceDir\commit.txt"
Write-Host "Commit: $commit"

# 3. Verify kernel tag exists
Write-Host "Verifying kernel tag..."
$tagCheck = git tag --list "v1.0.0-kernel74"
$tagCheck | Out-File "$evidenceDir\tag_check.txt"
if ($tagCheck) {
    Write-Host "Tag v1.0.0-kernel74 found." -ForegroundColor Green
} else {
    Write-Host "Warning: Tag v1.0.0-kernel74 NOT found." -ForegroundColor Yellow
}

# 4. Run full invariant suite (Adapted from run-all.ps1)
Write-Host "Running invariant suite..."
$testLog = "$evidenceDir\test_results.log"

# Function to run and log
function Run-And-Log {
    param($Title, $File, $ArgsList)
    Write-Host "Executing $Title..." -ForegroundColor Yellow
    "=== $Title ===" | Out-File $testLog -Append
    if ($File.EndsWith(".ps1")) {
        powershell -File $File $ArgsList 2>&1 | Tee-Object -FilePath $testLog -Append
    } else {
        & $File $ArgsList 2>&1 | Tee-Object -FilePath $testLog -Append
    }
    "" | Out-File $testLog -Append
}

# Run the components of run-all.ps1
Run-And-Log "SOVEREIGNTY VALIDATION" "scripts/governance/validate_sovereignty.ps1" "-All"
Run-And-Log "SECURITY SCAN" "scripts/hacking/Invoke-HackingOrchestrator.ps1" "-ScanOnly"
Run-And-Log "SYSTEM HEALTHCHECK" "scripts/Healthcheck.ps1"

# 5. Generate SITREP template
Write-Host "Generating SITREP template..."
$sitrep = @"
# SITREP — Season 3 Merge Cycle
Timestamp: $timestamp
Commit: $commit

## Summary
(Write 3–5 factual lines about the merge cycle.)

## Evidence
- commit.txt
- tag_check.txt
- test_results.log

## Assessment
- Kernel State: LOCKED (v1.0.0-kernel74)
- Extension Surface: Season 3 Active
- Drift: None detected

## Next Actions
1. Review extension PR.
2. Validate Phase‑9 compliance.
3. Run rollback drill if merged.
"@

$sitrep | Out-File "$evidenceDir\SITREP_TEMPLATE.md"

Write-Host ""
Write-Host "=== Baseline Complete ===" -ForegroundColor Green
Write-Host "Commit: $commit"
Write-Host "Tag Check: $tagCheck"
Write-Host "Evidence stored in: $evidenceDir"
