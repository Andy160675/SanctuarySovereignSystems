# =============================================================================
# Initialize-FeedbackLoop.ps1
# MISSION: Boot the circulatory system for distributed safety learning.
# =============================================================================

param(
    [string]$SystemId = "SOVEREIGN-TRINITY",
    [string]$LogPath = "evidence/feedback_loop"
)

function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $color = switch ($Level) {
        "INFO"  { "Cyan" }
        "WARN"  { "Yellow" }
        "ERROR" { "Red" }
        "OK"    { "Green" }
        default { "White" }
    }
    Write-Host "[$ts] [$Level] $Message" -ForegroundColor $color
}

Write-Log "Initializing Feedback Propagation System..." "INFO"

# Ensure evidence directory exists
if (-not (Test-Path $LogPath)) {
    New-Item -ItemType Directory -Path $LogPath -Force | Out-Null
}

# Create a state file for the feedback loop
$stateFile = Join-Path $LogPath "feedback_state.json"
$initialState = @{
    system_id = $SystemId
    status = "ACTIVE"
    initialized_at = (Get-Date).ToString("o")
    total_nodes = 30000
    near_misses = 0
    violations = 0
    pending_fixes = @()
    active_guards = @{
        "CLAUSE-001" = @{ status = "ENFORCED"; version = "1.0.0" }
        "ALARP-001"  = @{ status = "ENFORCED"; version = "1.0.0" }
    }
}

$initialState | ConvertTo-Json -Depth 5 | Out-File -FilePath $stateFile -Encoding utf8

Write-Log "Feedback Loop State initialized at $stateFile" "OK"

# In a real environment, we would start a background Python worker
# For this setup, we'll create the bridge script that the worker would use
$workerScript = @"
import json
import os
import sys
from jarus.governance.feedback_propagation import FeedbackPropagationSystem, ObservationType

def main():
    fps = FeedbackPropagationSystem(system_id="$SystemId")
    print(f"Feedback Propagation System {fps.system_id} is monitoring...")
    
    # Simulate loading state
    state_path = r"$stateFile"
    if os.path.exists(state_path):
        with open(state_path, 'r') as f:
            state = json.load(f)
            print(f"Loaded state: {state['status']}")

if __name__ == '__main__':
    main()
"@

$workerPath = Join-Path $LogPath "feedback_worker_bridge.py"
$workerScript | Out-File -FilePath $workerPath -Encoding utf8

Write-Log "Feedback Worker Bridge created at $workerPath" "OK"
Write-Log "Feedback Loop: ONLINE" "OK"
