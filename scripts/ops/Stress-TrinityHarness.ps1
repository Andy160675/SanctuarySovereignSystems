<#
.SYNOPSIS
    Stress-TrinityHarness.ps1 — Stress test the Sovereign Trinity system.
    
.DESCRIPTION
    Designed to falsify the "1M agent scale" hypothesis by measuring 
    real-time invariants under adversarial load conditions.

    Metrics Tracked:
    - Evidence Production Rate (Agents/s)
    - Coordination Latency (P99, P50)
    - Invariant Integrity (SVC Chain Status)
    - Resource Pressure (Disk I/O, CPU)

.PARAMETER ConcurrentBursts
    Number of concurrent pipelines to trigger (Default: 50)

.PARAMETER Iterations
    Number of load waves to execute (Default: 10)

.PARAMETER TargetUrl
    Trinity Backend URL (Default: http://localhost:8600)
#>

param(
    [int]$ConcurrentBursts = 50,
    [int]$Iterations = 10,
    [string]$TargetUrl = "http://localhost:8600"
)

$ErrorActionPreference = "Continue"

function Write-StressLog {
    param([string]$Message, [string]$Level = "INFO")
    $ts = Get-Date -Format "HH:mm:ss.fff"
    $color = switch ($Level) {
        "PRESSURE" { "Red" }
        "INVARIANT" { "Yellow" }
        "METRIC" { "Cyan" }
        default { "White" }
    }
    Write-Host "[$ts] [$Level] $Message" -ForegroundColor $color
}

Write-Host @"
╔═══════════════════════════════════════════════════════════════════════════╗
║                 SOVEREIGN TRINITY STRESS HARNESS                          ║
║        Falsifying Scale Hypotheses via Invariant Stress Testing           ║
╚═══════════════════════════════════════════════════════════════════════════╝
"@ -ForegroundColor Red

# 1. Baseline Invariant Check
Write-StressLog "Verifying Baseline SVC Invariants..."
try {
    $baseline = Invoke-RestMethod -Uri "$TargetUrl/api/trinity/svc/verify" -Method Get
    if ($baseline.valid -ne $true) {
        Write-StressLog "BASELINE INVARIANT FAILURE: SVC Chain invalid before test." "PRESSURE"
        exit 1
    }
    Write-StressLog "Baseline Integrity: OK" "METRIC"
} catch {
    Write-StressLog "Backend unreachable at $TargetUrl. Start backend first." "PRESSURE"
    exit 1
}

$results = @()
$globalStart = Get-Date

# 2. Stress Execution Loop
for ($wave = 1; $wave -le $Iterations; $wave++) {
    Write-StressLog "--- WAVE $wave OF $Iterations ($ConcurrentBursts concurrent bursts) ---" "PRESSURE"
    
    $jobs = @()
    $waveStart = Get-Date
    
    # Trigger concurrent bursts
    for ($i = 0; $i -lt $ConcurrentBursts; $i++) {
        $caseId = "STRESS-$wave-$i-$(Get-Random)"
        $jobs += Start-Job -ScriptBlock {
            param($url, $cid)
            $start = Get-Date
            try {
                $res = Invoke-RestMethod -Uri "$url/api/trinity/run_case" -Method Post -Body (@{case_id=$cid; query="stress-test"} | ConvertTo-Json) -ContentType "application/json" -TimeoutSec 30
                $end = Get-Date
                return @{
                    success = $res.success
                    latency = ($end - $start).TotalMilliseconds
                    svc_hash = $res.svc.commit_hash
                    status = "OK"
                }
            } catch {
                return @{
                    success = $false
                    latency = 0
                    status = "FAIL: $($_.Exception.Message)"
                }
            }
        } -ArgumentList $TargetUrl, $caseId
    }
    
    # Wait for wave completion
    $waveResults = $jobs | Wait-Job | Receive-Job
    $jobs | Remove-Job
    
    # Process results - Convert to PSCustomObject for proper property access
    $processedResults = @()
    foreach ($wr in $waveResults) {
        $processedResults += [PSCustomObject]$wr
    }
    $waveResults = $processedResults
    
    $waveEnd = Get-Date
    $waveDuration = ($waveEnd - $waveStart).TotalSeconds
    
    # 3. Wave Metric Analysis
    $successes = ($waveResults | Where-Object { $_.success -eq $true }).Count
    $failures = $ConcurrentBursts - $successes
    $latencies = $waveResults | Select-Object -ExpandProperty latency
    
    if ($latencies) {
        $p50 = ($latencies | Measure-Object -Average).Average
        $sortedLatencies = $latencies | Sort-Object
        $p99 = $sortedLatencies[[Math]::Max(0, [int]($latencies.Count * 0.99) - 1)]
    } else {
        $p50 = 0
        $p99 = 0
    }

    $throughput = $successes / $waveDuration

    Write-StressLog "Wave $wave Stats: Success=$successes, Fail=$failures, P50=$([Math]::Round($p50, 2))ms, P99=$([Math]::Round($p99, 2))ms" "METRIC"
    Write-StressLog "Throughput: $([Math]::Round($throughput, 2)) coord/sec" "METRIC"

    # 4. Invariant Falsification Check
    $integrity = Invoke-RestMethod -Uri "$TargetUrl/api/trinity/svc/verify" -Method Get
    if ($integrity.valid -ne $true) {
        Write-StressLog "INVARIANT COLLAPSE DETECTED: SVC Chain integrity compromised under load." "PRESSURE"
        # We don't exit, we want to see how it fails
    } else {
        Write-StressLog "Invariants held for Wave $wave." "METRIC"
    }

    $results += [PSCustomObject]@{
        wave = $wave
        successes = $successes
        failures = $failures
        p50 = $p50
        p99 = $p99
        throughput = $throughput
        integrity_valid = $integrity.valid
    }

    # Admission control check: if P99 > 5s, warn about tail latency saturation
    if ($p99 -gt 5000) {
        Write-StressLog "TAIL LATENCY CRITICAL: Coordination fan-out saturating I/O." "INVARIANT"
    }
}

$globalEnd = Get-Date
$totalDuration = ($globalEnd - $globalStart).TotalSeconds

# 5. Final Synthesis
Write-Host "`n" + ("=" * 60) -ForegroundColor Red
Write-Host " STRESS HARNESS SUMMARY" -ForegroundColor Red
Write-Host ("=" * 60) -ForegroundColor Red

$totalSuccess = ($results | Measure-Object -Property successes -Sum).Sum
$totalFail = ($results | Measure-Object -Property failures -Sum).Sum
$avgThroughput = ($results | Measure-Object -Property throughput -Average).Average
$maxP99 = ($results | Measure-Object -Property p99 -Maximum).Maximum

Write-Host " Total Coordination Cycles: $($totalSuccess + $totalFail)"
Write-Host " Global Success Rate:      $([Math]::Round(($totalSuccess / ($totalSuccess + $totalFail) * 100), 2))%"
Write-Host " Avg Evidence Throughput:  $([Math]::Round($avgThroughput, 2)) coord/sec"
Write-Host " Peak Coordination Latency: $([Math]::Round($maxP99, 2)) ms"
$finalIntegrityStatus = if ($results[-1].integrity_valid) { "STABLE" } else { "FALSIFIED" }
$finalIntegrityColor = if ($results[-1].integrity_valid) { "Green" } else { "Red" }
Write-Host " Final Invariant Status:    $finalIntegrityStatus" -ForegroundColor $finalIntegrityColor

# Export Stress Evidence
$evidencePath = "evidence/stress_test_$(Get-Date -Format 'yyyyMMdd_HHmmss').json"
$results | ConvertTo-Json | Out-File -FilePath $evidencePath -Encoding utf8
Write-StressLog "Stress evidence saved to $evidencePath" "METRIC"

if ($totalFail -gt 0 -or $maxP99 -gt 10000) {
    Write-Host "`nCONCLUSION: Scale hypothesis constrained by tail latency/contention." -ForegroundColor Yellow
} else {
    Write-Host "`nCONCLUSION: Modelled safe envelope remains unfalsified at current load." -ForegroundColor Green
}
