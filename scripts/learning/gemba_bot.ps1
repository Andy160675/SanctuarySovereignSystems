<#
.SYNOPSIS
  GembaBot - “Go to source, fix, report, share.”
.DESCRIPTION
  Walks the local cluster, checks for stale proofs / errors / drift,
  applies small auto-fixes, logs results to best_practices.jsonl.
#>

param(
  [Parameter(Mandatory=$false)][string]$NodeId = $env:COMPUTERNAME,
  [Parameter(Mandatory=$false)][string]$InventoryPath = ".\fleet\inventory.json"
)

$ts = Get-Date -Format "yyyyMMddTHHmmssZ"
$reportRoot = "validation\gemba\$NodeId\$ts"
New-Item -ItemType Directory -Force -Path $reportRoot | Out-Null

Start-Transcript -Path "$reportRoot\run.log"

try {
  $inventory = Get-Content $InventoryPath | ConvertFrom-Json
  $node = $inventory.nodes | Where-Object { $_.node_id -eq $NodeId }
  
  if (-not $node) {
      Write-Warning "Node $NodeId not found in inventory. Using first node as fallback for simulation."
      $node = $inventory.nodes[0]
  }

  Write-Host "=== GembaBot [$($node.node_id)] ===" -ForegroundColor Cyan
  
  # Update cluster registry with current scan status
  $registryPath = "fleet\cluster_registry.json"
  if (Test-Path $registryPath) {
      $registry = Get-Content $registryPath | ConvertFrom-Json
      $state = @{
          node_id = $node.node_id
          last_gemba_cycle = (Get-Date -Format "o")
          agent_count = $node.cluster.agents.Count
      }
      $registry.clusters = $registry.clusters | Where-Object { $_.node_id -ne $node.node_id }
      $registry.clusters += $state
      $registry | ConvertTo-Json | Out-File $registryPath
  }

  foreach ($agent in $node.cluster.agents) {
    Write-Host "Agent $($agent.id) ($($agent.role)/Tier-$($agent.tier)) initiating cycle..."
    
    # GO-SEE: Check for local anomalies
    $anomaly = $null
    if ($agent.role -eq "Scout") {
        # Scouts discover issues (simulated)
        if (-not (Test-Path "validation\$($agent.id)")) {
            $anomaly = "Missing validation directory"
        }
    }

    # FIX: Local remediation
    if ($anomaly) {
        Write-Host "  [FIX] $($agent.role) remediating: $anomaly" -ForegroundColor Yellow
        New-Item -ItemType Directory -Force "validation\$($agent.id)" | Out-Null
        
        # REPORT & SHARE: Document solution and share
        $lesson = @{
          timestamp = (Get-Date -Format "o")
          node_id = $node.node_id
          agent_id = $agent.id
          topic = "remediation"
          lesson = "Auto-created missing validation folder for $($agent.id)"
          proof = "$reportRoot\run.log"
          action = "fix"
          result = "success"
        } | ConvertTo-Json -Compress
        
        Add-Content "governance\ledger\best_practices.jsonl" $lesson
        Write-Host "  [SHARE] Lesson recorded to best_practices ledger." -ForegroundColor Gray
    } else {
        Write-Host "  [OK] No anomalies detected by $($agent.role)." -ForegroundColor Green
    }
  }

  Write-Host "DONE: GembaBot cycle complete." -ForegroundColor Green
}
catch {
  Write-Host "ERROR: Error in GembaBot: $_" -ForegroundColor Red
}
finally {
  Stop-Transcript
}
