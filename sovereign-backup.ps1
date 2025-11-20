# SOVEREIGN MIRROR PROTOCOL
$Source = "C:\Users\andyj\AI_Agent_Research"
$DestPC3 = "D:\Sovereign_Mirror_PC3" 
$DestPC4 = "E:\Sovereign_Mirror_PC4"

# Robocopy Flags: /MIR (Mirror) /FFT (Fat File Time) /R:3 (Retries) /W:5 (Wait)
# Excludes: .git folder (optional, usually keep it), venv, temp data
$Options = @("/MIR", "/FFT", "/R:3", "/W:5", "/XD", ".venv", "__pycache__", ".git")

Write-Host "🚀 MIRRORING TO PC3..." -ForegroundColor Cyan
# robocopy $Source $DestPC3 @Options

Write-Host "🚀 MIRRORING TO PC4..." -ForegroundColor Cyan
# robocopy $Source $DestPC4 @Options

Write-Host "✅ SOVEREIGNTY SECURED." -ForegroundColor Green
