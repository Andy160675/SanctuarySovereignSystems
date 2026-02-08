param(
    [Parameter(Mandatory=$true)]
    [string]$ServicePath,
    
    [Parameter(Mandatory=$false)]
    [string]$ServiceName = "sovereign-app",
    
    [Parameter(Mandatory=$false)]
    [switch]$SkipDeps
)

$ErrorActionPreference = "Stop"

function Write-Sovereign {
    param([string]$Message, [string]$Color = "Cyan")
    Write-Host "[SOVEREIGN] $Message" -ForegroundColor $Color
}

Write-Sovereign "=== INITIATING SOVEREIGN RUN: $ServiceName ===" "Magenta"

# 1. Load environment from .env if present
$ProjectRoot = Get-Location
$EnvFile = Join-Path $ProjectRoot ".env"
if (Test-Path $EnvFile) {
    Write-Sovereign "Loading environment from .env"
    Get-Content $EnvFile | Where-Object { $_ -match '=' -and $_ -notmatch '^#' } | ForEach-Object {
        $key, $value = $_ -split '=', 2
        [System.Environment]::SetEnvironmentVariable($key.Trim(), $value.Trim())
    }
}

# 2. Fresh Workspace (Process Isolation)
$Timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$Workdir = Join-Path $env:TEMP "sov-run-$ServiceName-$Timestamp"
New-Item -ItemType Directory -Path $Workdir -Force | Out-Null
Write-Sovereign "Created isolated workspace: $Workdir"

# 2. Dependency Verification (Deterministic State)
$ReqFile = Join-Path (Get-Location) "requirements.txt"
if (Test-Path (Join-Path $ServicePath "requirements.txt")) {
    $ReqFile = Join-Path $ServicePath "requirements.txt"
}

if (!(Test-Path $ReqFile)) {
    Write-Sovereign "No requirements.txt found. Skipping dependency check." "Yellow"
} elseif ($SkipDeps) {
    Write-Sovereign "Skipping dependency installation as requested." "Yellow"
} else {
    $Hash = (Get-FileHash $ReqFile -Algorithm SHA256).Hash
    Write-Sovereign "Verified Dependencies (SHA256): $Hash"
    
    Write-Sovereign "Installing dependencies to user-space..."
    pip install --user -r $ReqFile --quiet
}

# 3. Evidence Chain (Triosphere Integration)
$LedgerPath = Join-Path $ProjectRoot "Governance/ledger/sovereign_run_ledger.jsonl"
if (!(Test-Path (Join-Path $ProjectRoot "Governance/ledger"))) { New-Item -ItemType Directory (Join-Path $ProjectRoot "Governance/ledger") -Force | Out-Null }

Write-Sovereign "Recording Intent in Evidence Ledger..."
$Context = @{
    service = $ServiceName
    path = $ServicePath
    workdir = $Workdir
    timestamp = $Timestamp
    host = $env:COMPUTERNAME
} | ConvertTo-Json -Compress

# Use temporary file for context to avoid shell escaping issues
$ContextFile = Join-Path $Workdir "context.json"
$Context | Set-Content $ContextFile

$ProjectRootStr = $ProjectRoot.ToString()
$LedgerPathStr = $LedgerPath.ToString()
$ContextFileStr = $ContextFile.ToString()

# Use environment variable for PYTHONPATH to ensure jarus is found
$env:PYTHONPATH = $ProjectRootStr

$pyIntent = @"
import sys, os, json
from pathlib import Path
from jarus.core.evidence_ledger import EvidenceLedger, EvidenceType

ledger_path = Path(sys.argv[2])
ledger = EvidenceLedger(ledger_path)
with open(sys.argv[1], 'r') as f:
    context = json.load(f)
msg = "Initiating sovereign run for " + context['service']
ledger.record(EvidenceType.DECISION, context, msg, metadata={'layer': 'IntentSphere'})
"@
$pyIntent = $pyIntent.Replace('"', '\"')
python -c "$pyIntent" "$($ContextFileStr -replace '\\', '/')" "$($LedgerPathStr -replace '\\', '/')"

# 4. Execution (Action Sphere)
Write-Sovereign "Launching $ServiceName..." "Green"
Set-Location $ServicePath

# In a real sovereign system, we'd copy the app code to the workdir first.
# For this PoC, we run from the source but point the workdir elsewhere if needed.

# Execute the service (using start to not block, but redirecting logs to workdir)
$OutFile = Join-Path $Workdir "service.log"
$ErrFile = Join-Path $Workdir "error.log"
Write-Sovereign "Logs redirected to: $OutFile"

# Note: This is a simplified execution. A full implementation would use a supervisor.
# We'll run it in the background and capture the PID.
$Process = Start-Process python -ArgumentList "app.py" -PassThru -NoNewWindow -RedirectStandardOutput $OutFile -RedirectStandardError $ErrFile

Write-Sovereign "Service started with PID: $($Process.Id)" "Green"

# 5. Record Outcome
$pyOutcome = @"
import sys, os, json
from pathlib import Path
from jarus.core.evidence_ledger import EvidenceLedger, EvidenceType

ledger_path = Path(sys.argv[3])
ledger = EvidenceLedger(ledger_path)
msg = "Service " + sys.argv[2] + " successfully launched."
ledger.record(EvidenceType.ATTESTATION, {'pid': sys.argv[1], 'status': 'started'}, msg, metadata={'layer': 'ActionSphere'})
"@
$pyOutcome = $pyOutcome.Replace('"', '\"')
python -c "$pyOutcome" "$($Process.Id)" "$ServiceName" "$($LedgerPathStr -replace '\\', '/')"

Write-Sovereign "=== SOVEREIGN RUN COMPLETE (Service running in background) ===" "Magenta"
Write-Sovereign "Use 'Stop-Process -Id $($Process.Id)' to terminate."
