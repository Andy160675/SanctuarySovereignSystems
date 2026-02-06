<#
.SYNOPSIS
    Deploys 10GbE network optimizations and enforces Interface Metric priority.
    Aligned with docs/NETWORK_OPTIMIZATION_PLAN.md

.DESCRIPTION
    1. Sets Receive/Transmit buffers for 10GbE adapters.
    2. Enables Jumbo Packets (9014 Bytes).
    3. Forces Interface Metric 10 (High Priority) for 10GbE and 100 (Low) for Wi-Fi.
    4. Logs current state to validation/network_reconciliation.json

.EXAMPLE
    .\Optimize-NetworkFleet.ps1 -DryRun
#>

param(
    [switch]$DryRun,
    [int]$Metric10GbE = 10,
    [int]$MetricWiFi = 100,
    [string]$LogPath = "validation\network_reconciliation_$(Get-Date -Format 'yyyyMMdd_HHmmss').json"
)

$Results = @{
    Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Optimizations = @()
}

$NICs = Get-NetAdapter | Where-Object { $_.Status -eq "Up" }

foreach ($n in $NICs) {
    $NICInfo = @{
        Name = $n.Name
        InterfaceDescription = $n.InterfaceDescription
        LinkSpeed = $n.LinkSpeed
        Actions = @()
    }

    # 1. 10GbE Specific Optimization
    if ($n.LinkSpeed -eq "10 Gbps") {
        $Props = @(
            @{ Name = "Receive Buffers"; Value = "4096" },
            @{ Name = "Transmit Buffers"; Value = "16384" },
            @{ Name = "Jumbo Packet"; Value = "9014 Bytes" }
        )

        foreach ($p in $Props) {
            if (-not $DryRun) {
                try {
                    Set-NetAdapterAdvancedProperty -Name $n.Name -DisplayName $p.Name -DisplayValue $p.Value -ErrorAction Stop
                    $NICInfo.Actions += "Set $($p.Name) to $($p.Value)"
                } catch {
                    $NICInfo.Actions += "FAILED: Set $($p.Name) - $($_.Exception.Message)"
                }
            } else {
                $NICInfo.Actions += "[DRY RUN] Would set $($p.Name) to $($p.Value)"
            }
        }

        # Priority Metric
        if (-not $DryRun) {
            # Use netsh for compatibility where Set-NetAdapterInterface is missing
            netsh interface ipv4 set interface "$($n.Name)" metric=$Metric10GbE
            $NICInfo.Actions += "Set InterfaceMetric to $Metric10GbE (via netsh)"
        } else {
            $NICInfo.Actions += "[DRY RUN] Would set InterfaceMetric to $Metric10GbE"
        }
    }

    # 2. Wi-Fi De-prioritization
    if ($n.PhysicalMediaType -like "*Native 802.11*" -or $n.Name -like "*Wi-Fi*") {
        if (-not $DryRun) {
            netsh interface ipv4 set interface "$($n.Name)" metric=$MetricWiFi
            $NICInfo.Actions += "De-prioritized Wi-Fi (Metric $MetricWiFi) (via netsh)"
        } else {
            $NICInfo.Actions += "[DRY RUN] Would set Wi-Fi Metric to $MetricWiFi"
        }
    }

    $Results.Optimizations += $NICInfo
}

$Results | ConvertTo-Json -Depth 5 | Out-File $LogPath
Write-Host "Optimization Complete. Log stored at $LogPath" -ForegroundColor Green
