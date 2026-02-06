param(
    [string]$Root = "C:\SovereignInventory",
    [switch]$IncludeSecrets = $false # Never default to true
)

$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$out = Join-Path $Root "$env:COMPUTERNAME`_$stamp"

if (-not (Test-Path $Root)) {
    New-Item -ItemType Directory -Force -Path $Root | Out-Null
}

New-Item -ItemType Directory -Force -Path $out | Out-Null

Write-Host "Gathering system info..."
Get-ComputerInfo | Out-File "$out\system.txt"

Write-Host "Gathering CPU info..."
Get-CimInstance Win32_Processor | Format-List * | Out-File "$out\cpu.txt"

Write-Host "Gathering RAM info..."
Get-CimInstance Win32_PhysicalMemory | Format-Table * | Out-File "$out\ram.txt"

Write-Host "Gathering disk info..."
Get-PhysicalDisk | Format-Table * | Out-File "$out\disks.txt"

Write-Host "Gathering volume info..."
Get-Volume | Format-Table * | Out-File "$out\volumes.txt"

Write-Host "Gathering network info..."
Get-NetAdapter | Format-Table * | Out-File "$out\network.txt"

Write-Host "Gathering IP config..."
ipconfig /all | Out-File "$out\ipconfig.txt"

Write-Host "Gathering active connections..."
Get-NetTCPConnection -State Established | Out-File "$out\connections.txt"

Write-Host "Gathering services..."
Get-Service | Out-File "$out\services.txt"

Write-Host "Gathering processes..."
Get-Process | Out-File "$out\processes.txt"

Write-Host "Finalizing identity..."
$hostname = hostname
$date = Get-Date
"$hostname`n$date" | Out-File "$out\identity.txt"

$zip = "$out.zip"
Write-Host "Compressing archive..."
Compress-Archive -Path $out -DestinationPath $zip -Force

Write-Host "Inventory complete -> $zip"
