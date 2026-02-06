# Monitor-System.ps1
# Checks the health of The Blade of Truth system components

param(
    [int]$IntervalMinutes = 15,
    [switch]$Loop
)

function Get-Timestamp {
    return Get-Date -Format "yyyy-MM-dd HH:mm:ss"
}

function Check-Health {
    Write-Host "[$(Get-Timestamp)] Checking System Health..." -ForegroundColor Cyan
    
    $services = @(
        @{ Name = "Truth Engine"; Port = 8001; Endpoint = "/health" },
        @{ Name = "Truth Engine Complete"; Port = 8002; Endpoint = "/health" },
        @{ Name = "Boardroom Shell"; Port = 3000; Endpoint = "/" },
        @{ Name = "Sovereign Core"; Port = 8003; Endpoint = "/" },
        @{ Name = "Feedback Loop"; Path = "evidence/feedback_loop/feedback_state.json" }
    )

    foreach ($service in $services) {
        if ($service.Path) {
            if (Test-Path $service.Path) {
                $state = Get-Content $service.Path | ConvertFrom-Json
                Write-Host "  [OK] $($service.Name) is active (Status: $($state.status))" -ForegroundColor Green
            } else {
                Write-Host "  [FAIL] $($service.Name) state file missing at $($service.Path)" -ForegroundColor Red
            }
            continue
        }
        $url = "http://localhost:$($service.Port)$($service.Endpoint)"
        try {
            $response = Invoke-WebRequest -Uri $url -Method Get -TimeoutSec 5 -ErrorAction Stop -UseBasicParsing
            Write-Host "  [OK] $($service.Name) is active ($($response.StatusCode))" -ForegroundColor Green
        } catch {
            Write-Host "  [FAIL] $($service.Name) is unreachable at $url" -ForegroundColor Red
        }
    }

    # Check Docker containers if docker is available
    if (Get-Command docker -ErrorAction SilentlyContinue) {
        Write-Host "  [DOCKER] Container Status:"
        docker ps --format "table {{.Names}}\t{{.Status}}"
    }

    # Check Ledger Integrity
    if (Test-Path "scripts\governance\verify_decision_ledger.py") {
        Write-Host "  [LEDGER] Verifying Decision Ledger..."
        python scripts\governance\verify_decision_ledger.py
    }
}

if ($Loop) {
    Write-Host "Starting monitoring loop (Interval: $IntervalMinutes mins). Press Ctrl+C to stop." -ForegroundColor Yellow
    while ($true) {
        Check-Health
        Start-Sleep -Seconds ($IntervalMinutes * 60)
    }
} else {
    Check-Health
}
