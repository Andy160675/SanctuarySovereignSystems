# Collect-FleetInventory.ps1
# Pulls the latest ZIP snapshots from remote nodes to PC4.

$nodes = @(
    "NODE-MOBILE",
    "PC-CORE-1"
)

$central = "C:\FleetInventory"
if (-not (Test-Path $central)) {
    New-Item -ItemType Directory -Force -Path $central | Out-Null
}

foreach ($node in $nodes) {
    Write-Host "Collecting from $node..." -ForegroundColor Cyan

    $remote = "\\$node\C$\SovereignInventory"
    if (Test-Path $remote) {
        $latest = Get-ChildItem $remote -Filter "*.zip" |
                  Sort-Object LastWriteTime -Descending |
                  Select-Object -First 1

        if ($latest) {
            Write-Host "Found latest snapshot: $($latest.Name)"
            $targetPath = Join-Path $central "$($latest.Name)"
            if (-not (Test-Path $targetPath)) {
                Copy-Item $latest.FullName $central -Verbose
            } else {
                Write-Host "Snapshot already collected: $($latest.Name)" -ForegroundColor Gray
            }
        } else {
            Write-Host "No snapshots found on $node" -ForegroundColor Yellow
        }
    } else {
        Write-Host "Remote path $remote is inaccessible." -ForegroundColor Red
    }
}

# Build summary index
$report = Join-Path $central "FleetSummary.txt"
"Fleet Inventory Summary" | Out-File $report
Get-Date | Out-File $report -Append
"`nCollected archives:" | Out-File $report -Append

Get-ChildItem $central *.zip |
Select-Object Name, @{Name="Size(MB)";Expression={ [Math]::Round($_.Length / 1MB, 2) }}, LastWriteTime |
Format-Table |
Out-File $report -Append

Write-Host "`nFleet inventory collected → $central" -ForegroundColor Green
