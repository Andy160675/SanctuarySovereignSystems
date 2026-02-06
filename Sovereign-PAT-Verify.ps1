<#
.SYNOPSIS
    Sovereign-PAT-Verify.ps1 — Verify encrypted GitHub PAT without revealing it.
    
.DESCRIPTION
    Decrypts 'github_pat.encrypted' to verify it is readable and valid, 
    but only prints metadata (length and SHA-256 hash of the token).
    
.NOTES
    Author:         Sovereign Authority
    Trust Class:    T2 (Operational Support)
    Security:       Viewer-only verification (No PAT output)
#>

[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"

Write-Host "═══ Sovereign PAT Verification Tool ═══" -ForegroundColor Cyan

$artifactPath = Join-Path (Get-Location) "github_pat.encrypted"

if (-not (Test-Path $artifactPath)) {
    Write-Error "Artifact not found: $artifactPath"
    Write-Host "Run .\Sovereign-PAT-Encrypt.ps1 first." -ForegroundColor Yellow
    exit 1
}

try {
    Write-Host "Decrypting and verifying artifact..." -ForegroundColor Gray
    
    # Import from CliXml (uses DPAPI for the SecureString)
    $securePat = Import-CliXml -Path $artifactPath
    
    if ($securePat -isnot [System.Security.SecureString]) {
        Write-Error "Artifact format invalid. Expected SecureString."
        exit 1
    }
    
    # Decrypt to plain text in memory only for verification
    $bstr = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($securePat)
    try {
        $plainPat = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto($bstr)
        
        $tokenLen = $plainPat.Length
        
        # Calculate SHA-256 hash for verification
        $sha256 = [System.Security.Cryptography.SHA256]::Create()
        $tokenBytes = [System.Text.Encoding]::UTF8.GetBytes($plainPat)
        $hashBytes = $sha256.ComputeHash($tokenBytes)
        $hashStr = [System.BitConverter]::ToString($hashBytes).Replace("-", "").ToLower()
        
        Write-Host "`n✓ SUCCESS: Artifact is decryptable." -ForegroundColor Green
        Write-Host "Metadata for verification:" -ForegroundColor White
        Write-Host "  token_len:    $tokenLen"
        Write-Host "  token_sha256: $hashStr"
        Write-Host "`nNote: The actual PAT was never printed to the console." -ForegroundColor Gray
    }
    finally {
        if ($bstr -ne [IntPtr]::Zero) {
            [System.Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr)
        }
    }
}
catch {
    Write-Error "Verification failed: $($_.Exception.Message)"
    Write-Host "`nPossible causes:" -ForegroundColor Yellow
    Write-Host "1. Artifact was encrypted by a different user."
    Write-Host "2. Artifact was encrypted on a different machine."
    Write-Host "3. File is corrupted."
    exit 1
}

Write-Host "`nSovereign status: Verification Complete." -ForegroundColor Gray
