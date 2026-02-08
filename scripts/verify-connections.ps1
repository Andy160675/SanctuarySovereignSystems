# Sovereign Connection Verifier
# Pings all configured endpoints to ensure connectivity

function Test-Endpoint {
    param($Name, $Url)
    Write-Host "Testing $Name at $Url ... " -NoNewline
    try {
        $response = Invoke-WebRequest -Uri $Url -Method Get -TimeoutSec 5 -ErrorAction Stop
        Write-Host "✅ OK ($($response.StatusCode))" -ForegroundColor Green
        return $true
    } catch {
        Write-Host "❌ FAILED: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

$ProjectRoot = Get-Location
$EnvFile = Join-Path $ProjectRoot ".env"
if (Test-Path $EnvFile) {
    Write-Host "Loading environment from .env" -ForegroundColor Gray
    Get-Content $EnvFile | Where-Object { $_ -match '=' -and $_ -notmatch '^#' } | ForEach-Object {
        $key, $value = $_ -split '=', 2
        $key = $key.Trim()
        $value = $value.Trim()
        if (-not [System.Environment]::GetEnvironmentVariable($key)) {
            [System.Environment]::SetEnvironmentVariable($key, $value)
        }
    }
}

$TruthUrl = $env:TRUTH_ENGINE_URL
if (-not $TruthUrl) { $TruthUrl = "http://localhost:5050" }

$OllamaUrl = $env:OLLAMA_HOST
if (-not $OllamaUrl) { $OllamaUrl = "http://localhost:11434" }

Write-Host "`n--- Sovereign Connection Verification ---" -ForegroundColor Cyan
$TruthOk = Test-Endpoint "Truth Engine" "$TruthUrl/health"
$OllamaOk = Test-Endpoint "Ollama" "$OllamaUrl/"

Write-Host "`n--- Summary ---" -ForegroundColor Cyan
if ($TruthOk -and $OllamaOk) {
    Write-Host "All connections verified. Sovereign Node is healthy." -ForegroundColor Green
} else {
    Write-Host "Some connections failed. Check service status and .env configuration." -ForegroundColor Yellow
}
