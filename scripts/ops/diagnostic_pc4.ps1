Write-Host "=== HOSTNAME & IDENTITY ===" -ForegroundColor Cyan
$env:COMPUTERNAME
[System.Net.Dns]::GetHostName()

Write-Host "`n=== NETWORK ADAPTERS ===" -ForegroundColor Cyan
Get-NetAdapter | Where-Object Status -eq "Up" | Format-Table Name, InterfaceDescription, LinkSpeed, MacAddress -AutoSize

Write-Host "`n=== IP CONFIGURATION ===" -ForegroundColor Cyan
Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.IPAddress -notlike "127.*" } | Format-Table InterfaceAlias, IPAddress, PrefixLength -AutoSize

Write-Host "`n=== ROUTE TO NAS (192.168.4.78) ===" -ForegroundColor Cyan
Test-Connection -ComputerName 192.168.4.78 -Count 2 | Format-Table Address, ResponseTime -AutoSize

Write-Host "`n=== ROUTE TO OTHER NODES ===" -ForegroundColor Cyan
$nodes = [Ordered]@{
    "PC-1 (ECHO)" = "192.168.4.136"
    "PC-2 (BACKDROP3)" = "192.168.4.143"
    "PC-3 (RELAY)" = "192.168.4.139"
    "NAS" = "192.168.4.78"
}
foreach ($node in $nodes.GetEnumerator()) {
    $result = Test-Connection -ComputerName $node.Value -Count 1 -Quiet
    $status = if ($result) { "✅ REACHABLE" } else { "❌ UNREACHABLE" }
    Write-Host "$($node.Key) ($($node.Value)): $status"
}

Write-Host "`n=== TAILSCALE STATUS ===" -ForegroundColor Cyan
$tailscale = Get-Command tailscale -ErrorAction SilentlyContinue
if ($tailscale) {
    tailscale status
} else {
    Write-Host "❌ TAILSCALE NOT INSTALLED" -ForegroundColor Red
}

Write-Host "`n=== NAS SMB ACCESS ===" -ForegroundColor Cyan
$nasPath = "\\192.168.4.78\Sovereign"
if (Test-Path $nasPath -ErrorAction SilentlyContinue) {
    Write-Host "✅ NAS Sovereign share accessible" -ForegroundColor Green
    Get-ChildItem $nasPath -ErrorAction SilentlyContinue | Select-Object Name, Mode | Format-Table -AutoSize
} else {
    Write-Host "❌ NAS Sovereign share NOT accessible (may need mapping)" -ForegroundColor Yellow
}
