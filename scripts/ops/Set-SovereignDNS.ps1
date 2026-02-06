<#
.SYNOPSIS
    Re-routes DNS to the Sovereign NAS Gateway.
    Aligned with THE_DIAMOND_DOCTRINE.md (Infrastructure is Governance).

.DESCRIPTION
    1. Sets primary DNS to 192.168.4.78 (NAS).
    2. Removes external fallback resolvers to enforce sovereignty.
#>

param(
    [string]$NAS_IP = "192.168.4.114"
)

Write-Host "Re-routing DNS to Sovereign NAS ($NAS_IP)..." -ForegroundColor Cyan

$Adapters = Get-NetAdapter | Where-Object { $_.Status -eq "Up" }

foreach ($a in $Adapters) {
    try {
        Set-DnsClientServerAddress -InterfaceIndex $a.InterfaceIndex -ServerAddresses $NAS_IP -ErrorAction Stop
        Write-Host "[OK] DNS Set for $($a.Name)"
    } catch {
        Write-Host "[FAILED] DNS Set for $($a.Name): $($_.Exception.Message)" -ForegroundColor Red
    }
}
