<#
.SYNOPSIS
    Cleans the network "noise floor" by disabling non-sovereign telemetry-heavy services.
    Targets: OneDrive, Microsoft Edge Update, GetHelp.

.DESCRIPTION
    1. Stops active processes.
    2. Disables startup tasks and services.
    3. Aligns with THE_DIAMOND_DOCTRINE.md (Signal > Noise).
#>

Write-Host "Cleaning Sovereignty Noise Floor..." -ForegroundColor Cyan

# 1. OneDrive
Write-Host "Handling OneDrive..."
Get-Process -Name "OneDrive" -ErrorAction SilentlyContinue | Stop-Process -Force
$OneDrivePath = "$env:LOCALAPPDATA\Microsoft\OneDrive\OneDrive.exe"
if (Test-Path $OneDrivePath) {
    # We don't want to uninstall, just prevent auto-start
    Write-Host "  - Disabling OneDrive startup via Registry..."
    Remove-ItemProperty -Path "HKCU:\Software\Microsoft\Windows\CurrentVersion\Run" -Name "OneDrive" -ErrorAction SilentlyContinue
}

# 2. Microsoft Edge (Processes and Updates)
Write-Host "Handling Microsoft Edge..."
Get-Process -Name "msedge", "msedgewebview2" -ErrorAction SilentlyContinue | Stop-Process -Force
$EdgeServices = @("edgeupdate", "edgeupdatem")
foreach ($svc in $EdgeServices) {
    if (Get-Service -Name $svc -ErrorAction SilentlyContinue) {
        Write-Host "  - Disabling service: $svc"
        Set-Service -Name $svc -StartupType Disabled
        Stop-Service -Name $svc -Force -ErrorAction SilentlyContinue
    }
}

# Edge Scheduled Tasks
$EdgeTasks = Get-ScheduledTask -TaskName "*Edge*" -ErrorAction SilentlyContinue
foreach ($task in $EdgeTasks) {
    Write-Host "  - Disabling task: $($task.TaskName)"
    Disable-ScheduledTask -TaskName $task.TaskName -ErrorAction SilentlyContinue
}

# 3. GetHelp and SearchHost
Write-Host "Handling SearchHost and GetHelp..."
Get-Process -Name "GetHelp", "SearchHost" -ErrorAction SilentlyContinue | Stop-Process -Force

# SearchHost is persistent, we may need to disable it more aggressively if it returns
# For now, we just stop it to clear the immediate noise floor.

# 4. Office / M365 Copilot Telemetry
Write-Host "Handling Office/M365 Telemetry..."
Get-Process -Name "OfficeClickToRun", "CefSharp.BrowserSubprocess" -ErrorAction SilentlyContinue | Stop-Process -Force

Write-Host "Noise floor cleaned. Signal should now be visible." -ForegroundColor Green
