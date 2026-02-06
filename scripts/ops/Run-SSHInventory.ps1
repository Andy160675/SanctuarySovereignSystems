param(
  [Parameter(Mandatory=$true)][string[]]$LinuxNodes,
  [string]$User = "admin",
  [string]$RemoteScript = "~/SovereignInventory/run_node_inventory.sh",
  [string]$LocalInventory = "C:\\FleetInventory"
)

New-Item -ItemType Directory -Force -Path $LocalInventory | Out-Null

foreach ($n in $LinuxNodes) {
  Write-Host "`n=== Triggering SSH inventory on $n ==="
  try {
    ssh "$User@$n" "bash -lc '$RemoteScript'" | Write-Host
  } catch {
    Write-Warning "Trigger failed on $n: $($_.Exception.Message)"
  }

  try {
    $list = ssh "$User@$n" "bash -lc 'ls -1t ~/SovereignInventory/*_*.tar.gz | head -n 1'"
    if ($list) {
      $dest = Join-Path $LocalInventory ([IO.Path]::GetFileName($list))
      scp "$User@$n:$list" "$dest"
      Write-Host "Collected: $dest"
    } else {
      Write-Warning "No archive found on $n"
    }
  } catch {
    Write-Warning "Collection failed on $n: $($_.Exception.Message)"
  }
}
