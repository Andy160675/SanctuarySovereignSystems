# scripts/ops/Remediate-Sovereignty.ps1
# Enforces "Default Deny" egress policy as per Sovereign Network Doctrine.
# Prunes unjustified external connections and restricts outbound traffic.

$ErrorActionPreference = "Stop"

function Apply-SovereignFirewall {
    Write-Host "--- APPLYING SOVEREIGN FIREWALL (EGRESS PRUNING) ---" -ForegroundColor Cyan

    # 1. Ensure Windows Firewall is enabled
    Write-Host "[1/5] Enabling Firewall profiles..." -ForegroundColor Yellow
    Set-NetFirewallProfile -Profile Domain,Public,Private -Enabled True

    # 2. Configure ALLOW rules for essential services
    Write-Host "[2/5] Configuring essential ALLOW rules (Cerebellum)..." -ForegroundColor Yellow

    # Loopback
    if (-not (Get-NetFirewallRule -Name "SOV_ALLOW_LOOPBACK" -ErrorAction SilentlyContinue)) {
        New-NetFirewallRule -DisplayName "Sovereign: Allow Loopback" -Direction Outbound -RemoteAddress 127.0.0.1 -Action Allow -Name "SOV_ALLOW_LOOPBACK"
    }
    
    # LAN Access (Internal Trust)
    if (-not (Get-NetFirewallRule -Name "SOV_ALLOW_LAN" -ErrorAction SilentlyContinue)) {
        New-NetFirewallRule -DisplayName "Sovereign: Allow LAN" -Direction Outbound -RemoteAddress 192.168.0.0/16,10.0.0.0/8,172.16.0.0/12 -Action Allow -Name "SOV_ALLOW_LAN"
    }

    # DNS (UDP/TCP 53)
    if (-not (Get-NetFirewallRule -Name "SOV_ALLOW_DNS_UDP" -ErrorAction SilentlyContinue)) {
        New-NetFirewallRule -DisplayName "Sovereign: Allow DNS (UDP)" -Direction Outbound -Protocol UDP -RemotePort 53 -Action Allow -Name "SOV_ALLOW_DNS_UDP"
    }
    if (-not (Get-NetFirewallRule -Name "SOV_ALLOW_DNS_TCP" -ErrorAction SilentlyContinue)) {
        New-NetFirewallRule -DisplayName "Sovereign: Allow DNS (TCP)" -Direction Outbound -Protocol TCP -RemotePort 53 -Action Allow -Name "SOV_ALLOW_DNS_TCP"
    }

    # NTP (UDP 123)
    if (-not (Get-NetFirewallRule -Name "SOV_ALLOW_NTP" -ErrorAction SilentlyContinue)) {
        New-NetFirewallRule -DisplayName "Sovereign: Allow NTP" -Direction Outbound -Protocol UDP -RemotePort 123 -Action Allow -Name "SOV_ALLOW_NTP"
    }

    # DHCP
    if (-not (Get-NetFirewallRule -Name "SOV_ALLOW_DHCP" -ErrorAction SilentlyContinue)) {
        New-NetFirewallRule -DisplayName "Sovereign: Allow DHCP" -Direction Outbound -Protocol UDP -LocalPort 68 -RemotePort 67 -Action Allow -Name "SOV_ALLOW_DHCP"
    }

    # Management Egress (Safety Net for Remote Ops)
    # 22 (SSH), 5990 (JB Gateway), 3389 (RDP), 63342 (Internal), 65100 (Relay)
    if (-not (Get-NetFirewallRule -Name "SOV_ALLOW_MGMT" -ErrorAction SilentlyContinue)) {
        New-NetFirewallRule -DisplayName "Sovereign: Allow Management Egress" -Direction Outbound -Protocol TCP -RemotePort 22,5990,3389,63342,65100 -Action Allow -Name "SOV_ALLOW_MGMT"
    }

    # 3. SET DEFAULT OUTBOUND TO BLOCK
    Write-Host "[3/5] LOCKDOWN: Setting Default Egress to BLOCK..." -ForegroundColor Red
    Set-NetFirewallProfile -Profile Domain,Public,Private -DefaultOutboundBlock Block

    # 4. PRUNE ACTIVE SESSIONS
    Write-Host "[4/5] Pruning non-essential external connections..." -ForegroundColor Yellow
    $nonEssential = @("chrome", "msedge", "GoogleDriveFS", "msedgewebview2", "RadeonSoftware")
    foreach ($proc in $nonEssential) {
        $p = Get-Process -Name $proc -ErrorAction SilentlyContinue
        if ($p) {
            Write-Host "  Stopping $proc..." -ForegroundColor Gray
            Stop-Process -Name $proc -Force -ErrorAction SilentlyContinue
        }
    }

    # 5. VERIFICATION
    Write-Host "[5/5] Verifying Sovereignty State..." -ForegroundColor Yellow
    Start-Sleep -Seconds 2
    $net = Get-NetTCPConnection -State Established | Where-Object { $_.RemoteAddress -notmatch "127|192.168|10.|172.(1[6-9]|2[0-9]|3[0-1])" }
    
    if ($net.Count -eq 0) {
        Write-Host "  [PASS] NO UNJUSTIFIED EXTERNAL CONNECTIONS DETECTED." -ForegroundColor Green
        return $true
    } else {
        Write-Host "  [WARN] UNJUSTIFIED CONNECTIONS REMAIN:" -ForegroundColor Red
        $net | Select-Object RemoteAddress, RemotePort, OwningProcess | Format-Table -AutoSize | Out-String | Write-Host -ForegroundColor Gray
        return $false
    }
}

$success = Apply-SovereignFirewall

if ($success) {
    Write-Host "--- SOVEREIGNTY REMEDIATED ---" -ForegroundColor Cyan
    exit 0
} else {
    Write-Host "--- SOVEREIGNTY PARTIALLY REMEDIATED (Manual review required) ---" -ForegroundColor Yellow
    exit 1
}
