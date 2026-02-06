<#
.SYNOPSIS
    Sovereign-PAT-Encrypt.ps1 — Encrypt GitHub PAT for Sovereign System.
    
.DESCRIPTION
    Takes a GitHub Personal Access Token (PAT) and encrypts it using Windows DPAPI.
    The resulting file 'github_pat.encrypted' is intended for use by the 
    Sovereign GitHub Auth automation.
    
    This is a one-time setup script for local machines.
    
.NOTES
    Author:         Sovereign Authority
    Trust Class:    T2 (Operational Support)
    Security:       Uses DPAPI (Machine/User-scoped encryption)
#>

[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"

Write-Host "═══ Sovereign PAT Encryption Tool ═══" -ForegroundColor Cyan
Write-Host "This tool will encrypt your GitHub Personal Access Token for secure use."

# 1. Get the PAT
$pat = Read-Host "Enter your GitHub PAT" -AsSecureString

if (-not $pat) {
    Write-Error "No PAT provided. Operation aborted."
    exit 1
}

# 2. Encrypt
try {
    Write-Host "Encrypting PAT..." -ForegroundColor Gray
    
    # We use Export-CliXml as it uses DPAPI by default for SecureStrings
    # and handles the serialization/deserialization safely in a PowerShell environment.
    $outputPath = Join-Path (Get-Location) "github_pat.encrypted"
    
    $pat | Export-CliXml -Path $outputPath
    
    if (Test-Path $outputPath) {
        Write-Host "`n✓ SUCCESS: PAT encrypted and saved to:" -ForegroundColor Green
        Write-Host "$outputPath" -ForegroundColor White
        Write-Host "`nNEXT STEPS:" -ForegroundColor Yellow
        Write-Host "1. Upload 'github_pat.encrypted' to SOVEREIGN_SYSTEM/secrets/"
        Write-Host "2. Ensure the destination directory has restricted access."
        Write-Host "3. You may now delete this script if preferred."
    }
}
catch {
    Write-Error "Encryption failed: $($_.Exception.Message)"
    exit 1
}

Write-Host "`nSovereign status: Persistent Auth Ready." -ForegroundColor Gray
