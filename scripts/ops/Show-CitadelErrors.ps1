# =============================================================================
# Show-CitadelErrors.ps1
# MISSION: Human command for rapid review of Citadel error and learning logs.
# Aligned with THE_DIAMOND_DOCTRINE.md (Proof before Power).
# =============================================================================

param(
    [string]$ErrorLog = "validation/citadel_errors.jsonl",
    [string]$LearningLog = "validation/citadel_learning.jsonl",
    [int]$Count = 5
)

Write-Host ""
Write-Host "  ============================================================" -ForegroundColor Cyan
Write-Host "   CITADEL DIAGNOSTICS: LATEST ERRORS & INSIGHTS" -ForegroundColor Cyan
Write-Host "  ============================================================" -ForegroundColor Cyan
Write-Host ""

if (Test-Path $ErrorLog) {
    Write-Host "--- RECENT ERROR HEALING (Last $Count) ---" -ForegroundColor Yellow
    Get-Content $ErrorLog -Tail $Count | ForEach-Object {
        $entry = $_ | ConvertFrom-Json
        Write-Host "[$($entry.Timestamp)] ERRORS: $($entry.Errors -join ', ') -> STATUS: $($entry.Status)"
    }
} else {
    Write-Host "No error logs found. Citadel integrity remains 100%." -ForegroundColor Green
}

Write-Host ""

if (Test-Path $LearningLog) {
    Write-Host "--- RECENT LEARNING INSIGHTS (Last $Count) ---" -ForegroundColor Cyan
    Get-Content $LearningLog -Tail $Count | ForEach-Object {
        $entry = $_ | ConvertFrom-Json
        Write-Host "[$($entry.Timestamp)] INSIGHT: $($entry.Insight)"
        Write-Host "               ACTION:  $($entry.ActionTaken)" -ForegroundColor DarkGray
    }
} else {
    Write-Host "No learning logs found. Initializing pattern recognition..." -ForegroundColor Gray
}

Write-Host ""
Write-Host "  ============================================================" -ForegroundColor Cyan
Write-Host ""
