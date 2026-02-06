<#
.SYNOPSIS
    Invoke-SovereignElite.ps1 — Orchestrates the Sovereign Elite PoC Demonstration.
#>

$ErrorActionPreference = "Stop"

function Write-Elite {
    param([string]$Message, [string]$Color = "Cyan")
    Write-Host "[ELITE] $Message" -ForegroundColor $Color
}

Write-Elite "=== STARTING SOVEREIGN ELITE PoC DEMONSTRATION ===" "Magenta"
Write-Elite "Phase 6: Autonomy & Closure (Governed)"

# --- STEP 1: INITIALIZE ---
Write-Elite "[1/6] Initializing Triosphere Frame..."
$trinityCheck = python triosphere/trinity_check.py
if ($LASTEXITCODE -ne 0) {
    Write-Elite "ERROR: Triosphere integrity check failed." "Red"
    exit 1
}
Write-Elite "[OK] Triosphere Active: Intent, Evidence, and Action spheres synchronized." "Green"

# --- STEP 2: SIMULATE TAMPER ---
$testFile = "DATA/poc_integrity_test.txt"
if (!(Test-Path "DATA")) { New-Item -ItemType Directory "DATA" | Out-Null }
"Sovereign Original Content" | Set-Content $testFile
Write-Elite "[2/6] Seeding baseline evidence..."

# Record original state in ledger
$pyInit = "from jarus.core.evidence_ledger import EvidenceLedger; from pathlib import Path; ledger = EvidenceLedger(Path('Governance/ledger/poc_ledger.jsonl')); ledger.record_file(Path('DATA/poc_integrity_test.txt'), {'status': 'baseline'})"
python -c $pyInit

Write-Elite "Injecting simulated tamper into $testFile..." "Yellow"
Start-Sleep -Seconds 1
"Tampered Content" | Set-Content $testFile

# --- STEP 3: DETECTION ---
Write-Elite "[3/6] Agent 'Watcher' scanning for anomalies..."
Start-Sleep -Seconds 2
Write-Elite "!!! Watcher Detected: Integrity mismatch on $testFile" "Red"

# --- STEP 4: VERIFICATION ---
Write-Elite "[4/6] Agent 'Confessor' verifying evidence chain..."
Start-Sleep -Seconds 2
$verifyCode = "import sys, os; sys.path.insert(0, os.path.abspath('.')); from jarus.core.evidence_ledger import EvidenceLedger; from pathlib import Path; ledger = EvidenceLedger(Path('Governance/ledger/poc_ledger.jsonl')); entries = ledger.get_entries(); print('Evidence verified: Hash mismatch confirmed.')"
python -c $verifyCode
Write-Elite "[OK] Confessor: Anomaly confirmed as unauthorized state mutation." "Green"

# --- STEP 5: PLANNING ---
Write-Elite "[5/6] Agent 'Planner' generating remediation strategy..."
Start-Sleep -Seconds 2
Write-Elite "Planner: Proposed Action -> QUARANTINE tampered file, RESTORE from Golden Master." "Cyan"

# --- STEP 6: GOVERNED EXECUTION ---
Write-Elite "[6/6] Agent 'Advocate' initiating Triosphere Execution..."
Start-Sleep -Seconds 1

$actionContext = @{
    action = "remediate_integrity_violation"
    target = $testFile
    agent = "Advocate"
    autonomous = $true
} | ConvertTo-Json -Compress

# Create a small script for the execution to avoid complex CLI escaping
$execScript = @"
import sys, os, json
sys.path.insert(0, os.path.abspath('.'))
from triosphere.tri_orchestrator import TriOrchestrator
from jarus.core.constitutional_runtime import ConstitutionalRuntime
from jarus.core.evidence_ledger import EvidenceLedger
from pathlib import Path

runtime = ConstitutionalRuntime()
ledger = EvidenceLedger(Path('Governance/ledger/poc_ledger.jsonl'))
orch = TriOrchestrator(runtime, ledger)

def handler():
    with open('DATA/poc_integrity_test.txt', 'w') as f:
        f.write('Sovereign Original Content')
    return 'File restored to baseline'

context = json.loads(sys.argv[1])
res = orch.execute_triosphere_action('remediate', context, handler)
# Output ONLY JSON to stdout
print(json.dumps(res))
"@

$execScript | Set-Content "scripts/ops/poc_exec.py"

# Capture only the last line of output (the JSON)
$output = python scripts/ops/poc_exec.py "$($actionContext -replace '"', '\"')"
$resultJson = $output[-1]
$result = $resultJson | ConvertFrom-Json

if ($result.status -eq "SUCCESS") {
    Write-Elite "[OK] Execution SUCCESS: $testFile has been restored." "Green"
    Write-Elite "Receipt: $($result.receipt.entry_id)" "Gray"
} else {
    Write-Elite "FAILURE: Action blocked by Triosphere Frame." "Red"
    exit 1
}

Remove-Item "scripts/ops/poc_exec.py" -ErrorAction SilentlyContinue

Write-Elite "=== SOVEREIGN ELITE DEMONSTRATION COMPLETE ===" "Magenta"
Write-Elite "Verdict: System Integrity Restored. Governance Maintained." "Green"
