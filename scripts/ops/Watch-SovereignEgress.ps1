<#
.SYNOPSIS
    The Sovereignty Gate (v2): Monitors 10GbE substrate against an Approved Allowlist.
    Aligned with THE_DIAMOND_DOCTRINE.md (Signal > Noise).

.DESCRIPTION
    1. Monitors Established TCP connections.
    2. Filters against an Allowlist (Local, Tailscale, DNS, Approved IPs).
    3. Logs non-approved egress to validation/egress_violations.jsonl.
    
.ALLOWLIST_LOGIC
    - Local Subnet: 192.168.4.0/24
    - Tailscale: 100.64.0.0 to 100.127.255.255 (100.64.0.0/10)
    - DNS/NTP: Explicitly approved external resolvers (e.g. 1.1.1.1, 8.8.8.8)
#>

param(
    [string[]]$AllowedSubnets = @("192.168.4.", "127.0.0.1", "::1"),
    [string[]]$AllowedIPs = @("1.1.1.1", "8.8.8.8", "9.9.9.9"), # DNS
    [string[]]$AllowedProcesses = @("tailscaled", "idea64", "python", "git", "ssh"),
    [int]$ScanIntervalSeconds = 5,
    [string]$ViolationLog = "validation/egress_violations.jsonl"
)

function Test-IsTailscale {
    param([string]$IP)
    if ($IP -match "^100\.(6[4-9]|[7-9][0-9]|1[0-1][0-9]|12[0-7])\.") { return $true }
    return $false
}

Write-Host "Sovereignty Gate v2.1 ACTIVE. Logic: Approved Boundary + Process Allowlist." -ForegroundColor Cyan

while ($true) {
    $Connections = Get-NetTCPConnection -State Established | Where-Object { 
        $_.RemoteAddress -notlike "0.0.0.0" -and $_.RemoteAddress -notlike "::"
    }

    foreach ($c in $Connections) {
        $Remote = $c.RemoteAddress
        $ProcessName = (Get-Process -Id $c.OwningProcess -ErrorAction SilentlyContinue).Name
        $IsAllowed = $false

        # 1. Check Subnets
        foreach ($s in $AllowedSubnets) { if ($Remote -like "$s*") { $IsAllowed = $true; break } }
        
        # 2. Check Explicit IPs
        if (-not $IsAllowed) { if ($AllowedIPs -contains $Remote) { $IsAllowed = $true } }

        # 3. Check Tailscale (100.64.0.0/10)
        if (-not $IsAllowed) { if (Test-IsTailscale $Remote) { $IsAllowed = $true } }

        # 4. Check Process Allowlist
        if (-not $IsAllowed) { if ($AllowedProcesses -contains $ProcessName) { $IsAllowed = $true } }

        if (-not $IsAllowed) {
            $Violation = @{
                Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
                Local = "$($c.LocalAddress):$($c.LocalPort)"
                Remote = "$($c.RemoteAddress):$($c.RemotePort)"
                Process = $ProcessName
            }

            $Violation | ConvertTo-Json -Compress | Out-File $ViolationLog -Append -Encoding UTF8
            Write-Host "[!!!] SIGNAL: $($Violation.Process) -> $($Violation.Remote)" -ForegroundColor Red
        }
    }

    Start-Sleep -Seconds $ScanIntervalSeconds
}
