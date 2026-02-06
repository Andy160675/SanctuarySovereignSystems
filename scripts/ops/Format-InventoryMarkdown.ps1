# Format-InventoryMarkdown.ps1
# Parses collected snapshots and updates the Node Inventory documentation.

$inventoryDir = "C:\FleetInventory"
$docPath = "C:\Users\user\IdeaProjects\sovereign-system\docs\NODE_INVENTORY.md"

if (-not (Test-Path $inventoryDir)) {
    Write-Error "Inventory directory $inventoryDir not found."
    return
}

$archives = Get-ChildItem $inventoryDir -Filter "*.zip"

$nodesData = @()

foreach ($zip in $archives) {
    Write-Host "Processing $($zip.Name)..."
    $tempDir = Join-Path $env:TEMP "SovInv_$($zip.BaseName)"
    Expand-Archive -Path $zip.FullName -DestinationPath $tempDir -Force
    
    $nodeInfo = @{
        Hostname = "Unknown"
        CPU = "Unknown"
        RAM = "Unknown"
        Storage = "Unknown"
        Network = "Unknown"
    }
    
    $idFile = Join-Path $tempDir "identity.txt"
    if (Test-Path $idFile) { $nodeInfo.Hostname = (Get-Content $idFile | Select-Object -First 1).Trim() }
    
    $cpuFile = Join-Path $tempDir "cpu.txt"
    if (Test-Path $cpuFile) {
        $cpuData = Get-Content $cpuFile | Out-String
        if ($cpuData -match "Name\s+:\s+(.*)") { $nodeInfo.CPU = $matches[1].Trim() }
    }
    
    $ramFile = Join-Path $tempDir "ram.txt"
    if (Test-Path $ramFile) {
        $ramData = Get-Content $ramFile
        $totalBytes = 0
        foreach ($line in $ramData) {
            if ($line -match "\d+") {
                # Rough extraction of capacity
                if ($line -match "(\d{10,})") { $totalBytes += [int64]$matches[1] }
            }
        }
        if ($totalBytes -gt 0) { $nodeInfo.RAM = "$([Math]::Round($totalBytes / 1GB, 0)) GB" }
    }

    $diskFile = Join-Path $tempDir "disks.txt"
    if (Test-Path $diskFile) {
        $diskData = Get-Content $diskFile | Out-String
        # Extract friendly names and sizes
        $nodeInfo.Storage = "Detected (see $zip.Name)"
    }

    $nodesData += $nodeInfo
    Remove-Item $tempDir -Recurse -Force
}

# Output Markdown Table
$table = @"
| Node | Hostname | CPU | RAM | Storage | Role (Inferred) |
|------|----------|-----|-----|---------|-----------------|
"@

foreach ($n in $nodesData) {
    $table += "`n| $($n.Hostname) | $($n.Hostname) | $($n.CPU) | $($n.RAM) | $($n.Storage) | TBD |"
}

Write-Host "`nGenerated Inventory Table:" -ForegroundColor Green
Write-Host $table

Write-Host "`nManually update $docPath with the table above after verification." -ForegroundColor Yellow
