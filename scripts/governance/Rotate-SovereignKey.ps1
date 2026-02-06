# scripts/governance/Rotate-SovereignKey.ps1
param([string]$KeyPath = "../../sovereign.key")
$ScriptBase = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Resolve-Path (Join-Path $ScriptBase "../..")
$AbsoluteKeyPath = Join-Path $ProjectRoot "sovereign.key"
. (Join-Path $ScriptBase "../sovereign/SovereignCrypto.ps1")
Write-Host "Sovereign Key Rotation Tool"
$newKey = [SovereignCrypto]::GenerateNewKey()
if (Test-Path $AbsoluteKeyPath) {
    Copy-Item $AbsoluteKeyPath (Join-Path $ProjectRoot "sovereign.key.old") -Force
}
$newKey | Out-File $AbsoluteKeyPath -Encoding utf8
Write-Host "SUCCESS: Sovereign Key Rotated."
