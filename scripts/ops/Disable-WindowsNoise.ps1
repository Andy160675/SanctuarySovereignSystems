<#
.SYNOPSIS
    Decommissions Windows telemetry and noise to secure the Sovereignty Gate.
    Aligned with THE_DIAMOND_DOCTRINE.md (Action follows restraint).

.DESCRIPTION
    1. Disables DiagTrack (Connected User Experiences and Telemetry).
    2. Disables WSearch (optional but recommended for I/O hygiene).
    3. Sets Registry keys to stop telemetry and data collection.
    4. Blocks common telemetry hosts at the OS level (Hosts file).
#>

param(
    [switch]$DryRun
)

$RegistryPaths = @(
    "HKLM:\SOFTWARE\Policies\Microsoft\Windows\DataCollection",
    "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\DataCollection"
)

Write-Host "Decommissioning Windows Noise..." -ForegroundColor Cyan

if (-not $DryRun) {
    # 1. Disable Services
    Stop-Service -Name "DiagTrack" -ErrorAction SilentlyContinue
    Set-Service -Name "DiagTrack" -StartupType Disabled
    Write-Host "[OK] DiagTrack Disabled."

    # 2. Enforce Registry Doctrine
    foreach ($path in $RegistryPaths) {
        if (-not (Test-Path $path)) { New-Item -Path $path -Force | Out-Null }
        Set-ItemProperty -Path $path -Name "AllowTelemetry" -Value 0 -Type DWord
    }
    Write-Host "[OK] Registry Telemetry Gates Locked."

    # 3. Block Telemetry Endpoints (Hosts File)
    $HostsPath = "$env:SystemRoot\System32\drivers\etc\hosts"
    $BlockList = @(
        "0.0.0.0 telemetry.microsoft.com",
        "0.0.0.0 v10.events.data.microsoft.com",
        "0.0.0.0 v20.events.data.microsoft.com",
        "0.0.0.0 watson.telemetry.microsoft.com"
    )

    $CurrentHosts = Get-Content $HostsPath
    foreach ($line in $BlockList) {
        if ($CurrentHosts -notcontains $line) {
            Add-Content -Path $HostsPath -Value $line
        }
    }
    Write-Host "[OK] Hosts file hardened."
} else {
    Write-Host "[DRY RUN] Would disable DiagTrack, set Registry to AllowTelemetry=0, and update Hosts file."
}
