# Creates a desktop shortcut for the Sovereign System Demo

$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("$env:USERPROFILE\Desktop\Sovereign System V3.lnk")
$Shortcut.TargetPath = "$PSScriptRoot\DEMO.bat"
$Shortcut.WorkingDirectory = $PSScriptRoot
$Shortcut.Description = "Sovereign System V3 - Governance Cockpit"
$Shortcut.Save()

Write-Host ""
Write-Host "  Desktop shortcut created: Sovereign System V3" -ForegroundColor Green
Write-Host "  Double-click the icon to launch the demo." -ForegroundColor Cyan
Write-Host ""
