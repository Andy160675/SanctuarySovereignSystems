[CmdletBinding()]
param(
    [string]$RepoRoot = "",
    [string]$OutFile = "evidence/trace/TRACE_MATRIX.csv"
)

$ErrorActionPreference = 'Stop'

if ([string]::IsNullOrWhiteSpace($RepoRoot)) {
    $RepoRoot = (Resolve-Path $PSScriptRoot\..\..).Path
}

Write-Host "--- AGENT 3: CLAIM TRACER ---" -ForegroundColor Cyan
Write-Host "Mapping doctrinal claims to artefacts..." -ForegroundColor Gray

# Define core claims and their evidence sources
$Claims = @(
    @{ 
        Claim = "Cross-Validation Architecture (CVA)"; 
        Evidence = "scripts/ops/Verify-EvidenceAgreement.ps1"; 
        Requirement = "Components must fail differently and execute independently."
    }
    @{ 
        Claim = "Disagreement = Signal"; 
        Evidence = "scripts/ops/Verify-EvidenceAgreement.ps1, SOP_DAILY.md"; 
        Requirement = "Never suppress divergence. Log, escalate, investigate."
    }
    @{ 
        Claim = "Explicit Accountability"; 
        Evidence = "SOP_DAILY.md, docs/governance/OPERATOR_CONTRACT.md"; 
        Requirement = "Human remains final decision authority."
    }
    @{ 
        Claim = "Immutable Ledger (Intent)"; 
        Evidence = "evidence/verification/, evidence/baselines/"; 
        Requirement = "Verifiable state through SHA-256 receipts."
    }
    @{ 
        Claim = "Retroactive Closed Loop"; 
        Evidence = "scripts/audit/Forensic-Scanner.ps1, evidence/manifests/"; 
        Requirement = "Audit method to freeze state, instrument evidence, link claims."
    }
)

$CsvHeader = "claim,requirement,evidence_path,hash,revision"
$CsvRows = @($CsvHeader)

foreach ($c in $Claims) {
    $evidencePaths = $c.Evidence -split ', '
    foreach ($ep in $evidencePaths) {
        $absPath = Join-Path $RepoRoot $ep
        $hash = "N/A"
        if (Test-Path $absPath) {
            if (-not (Test-Path $absPath -PathType Container)) {
                $hash = (Get-FileHash -Algorithm SHA256 -Path $absPath).Hash.ToLower()
            } else {
                $hash = "[DIRECTORY]"
            }
        } else {
            $hash = "GAP"
        }
        
        $CsvRows += "$($c.Claim),""$($c.Requirement)"",$ep,$hash,v1.0"
    }
}

$CsvRows | Set-Content -Path (Join-Path $RepoRoot $OutFile) -Encoding UTF8

Write-Host "Trace Matrix written to: $OutFile" -ForegroundColor Green
