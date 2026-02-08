Write-Host "Deploying Sovereign Engine Bolt-Ons..."
Write-Host "======================================"

# 1. Create directories
$dirs = @(
    "sovereign_engine\extensions\observatory",
    "sovereign_engine\extensions\evidence_vault",
    "sovereign_engine\extensions\merge_gate",
    "sovereign_engine\extensions\compliance",
    "sovereign_engine\extensions\board_packs",
    "sovereign_engine\extensions\connectors",
    "scripts",
    "docs\bolt_ons"
)

foreach ($dir in $dirs) {
    if (!(Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
    }
}

# 2. Install dependencies
Write-Host "Checking dependencies..."
python -c "import psutil; import requests"
if ($LASTEXITCODE -ne 0) {
    Write-Host "Installing missing dependencies..."
    pip install psutil requests
}

# 3. Run kernel tests
Write-Host "Running kernel tests..."
$env:PYTHONPATH="."
python -m sovereign_engine.tests.run_all
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Kernel tests failed. Aborting deployment."
    exit 1
}

# 4. Generate documentation (already done, but ensuring it's there)
Write-Host "Documentation available at: docs\bolt_ons\QUICK_START.md"

Write-Host "✅ Deployment complete!"
Write-Host "🚀 Run demo: python scripts\demo_bolt_ons.py"
