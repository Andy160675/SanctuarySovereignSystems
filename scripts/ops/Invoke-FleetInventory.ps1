# Invoke-FleetInventory.ps1
# Triggers remote inventory collection across known Windows nodes.

$nodes = @(
    "NODE-MOBILE",
    "PC-CORE-1"
)

# Note: NAS-01 and Node-1 Tenerife (if Linux) require SSH-based inventory collection.
# This script focuses on the Windows nodes with WinRM/PSRemoting enabled.

foreach ($node in $nodes) {
    Write-Host "`n=== Triggering inventory on $node ===" -ForegroundColor Cyan
    
    try {
        Invoke-Command -ComputerName $node -ScriptBlock {
            # Assumes the script has been deployed to the node
            $inventoryScript = "C:\SovereignInventory\Run-NodeInventory.ps1"
            if (Test-Path $inventoryScript) {
                Write-Host "Executing local inventory script..."
                PowerShell -ExecutionPolicy Bypass -File $inventoryScript
            } else {
                Write-Error "Inventory script not found on $node at $inventoryScript"
            }
        } -ErrorAction Stop
    } catch {
        Write-Host "FAILED to trigger inventory on $node : $($_.Exception.Message)" -ForegroundColor Red
    }
}

Write-Host "`nRemote triggering complete." -ForegroundColor Green
