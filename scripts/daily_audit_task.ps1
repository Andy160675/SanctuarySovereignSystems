# Sovereign Governance Schedule - Windows Task Wrapper

$LogDir = "C:\sovereign-system\Governance\Logs"
$ScriptDir = "C:\sovereign-system\scripts"

# Ensure log directory exists
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

# 1. Daily Audit
$AuditLog = "$LogDir\cron_audit.log"
Add-Content -Path $AuditLog -Value "--- Audit Run: $(Get-Date) ---"
python "$ScriptDir\verify_ledger.py" >> $AuditLog 2>&1

# 2. Readiness Check
$ReadinessLog = "$LogDir\cron_readiness.log"
Add-Content -Path $ReadinessLog -Value "--- Readiness Run: $(Get-Date) ---"
python "$ScriptDir\calculate_readiness.py" >> $ReadinessLog 2>&1

Write-Host "Governance tasks completed."
