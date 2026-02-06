# Pentad Health & Activation Verification
# This script performs cluster-wide validation of the Pentad system

param([switch]$Watch)

$HEADS = @("pc-a", "pc-b", "pc-c", "pc-d", "pc-e")
$EVIDENCE_DIR = "evidence\deployment"

function Log-Message {
    param($Level, $Message)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $color = "White"
    switch ($Level) {
        "INFO" { $color = "Green" }
        "WARN" { $color = "Yellow" }
        "ERROR" { $color = "Red" }
        "STEP" { $color = "Cyan" }
    }
    Write-Host "[$Level] $timestamp`: $Message" -ForegroundColor $color
}

function Log-Result {
    param($Test, $Status, $Message)
    $color = "Green"
    if ($Status -eq "FAIL") { $color = "Red" }
    Write-Host "[$Status] $Test`: $Message" -ForegroundColor $color
}

function Main {
    param([switch]$Watch)
    Log-Message "STEP" "Starting Pentad Health Check..."

    if ($Watch) {
        Log-Message "INFO" "Starting Health Monitoring Loop (Ctrl+C to stop)..."
        while ($true) {
            # Run the checks without the final message
            Verify-PKI
            Verify-Connection
            Verify-RD
            Verify-Evidence
            Log-Message "STEP" "--- Monitoring Cycle Complete (Wait 30s) ---"
            Start-Sleep -Seconds 30
        }
    } else {
        Verify-PKI
        Verify-Connection
        Verify-RD
        Verify-Evidence
        Log-Message "INFO" "Health check complete."
    }
}

function Verify-PKI {
    foreach ($h in $HEADS) {
        if (Test-Path "evidence_store\pki\$h.pem") {
            Log-Result "PKI-$h" "PASS" "Certificate bundle present"
        } else {
            Log-Result "PKI-$h" "FAIL" "Certificate bundle missing"
        }
    }
}

function Verify-Connection {
    if (Test-Path "evidence_store\connection\delivery_pc-a.jsonl") {
        Log-Result "Connection-A" "PASS" "Handshake delivery evidence found"
    } else {
        Log-Result "Connection-A" "FAIL" "Handshake delivery evidence missing"
    }
}

function Verify-RD {
    if (Test-Path "evidence_store\rnd_registry.json") {
        Log-Result "R&D-Registry" "PASS" "Registry initialized"
    } else {
        Log-Result "R&D-Registry" "FAIL" "Registry missing"
    }
}

function Verify-Evidence {
    $latest = Get-ChildItem "$EVIDENCE_DIR\deployment-*.jsonl" | Sort-Object LastWriteTime -Descending | Select-Object -First 1
    if ($latest) {
        $lines = Get-Content $latest.FullName
        if ($lines.Count -ge 5) {
            Log-Result "EvidenceChain" "PASS" "Chain complete ($($lines.Count) entries)"
        } else {
            Log-Result "EvidenceChain" "FAIL" "Chain incomplete ($($lines.Count) entries)"
        }
    } else {
        Log-Result "EvidenceChain" "FAIL" "No deployment evidence found"
    }
}

# Main Execution
Main -Watch:$Watch
