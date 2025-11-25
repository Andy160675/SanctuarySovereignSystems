# Sovereign System - Quick Start
# One-command deployment

Write-Host "🔥 SOVEREIGN SYSTEM - PHASE 4 DEPLOYMENT" -ForegroundColor Red
Write-Host "=======================================" -ForegroundColor Red
Write-Host ""

Write-Host "📦 Starting Docker containers..." -ForegroundColor Cyan
docker compose up -d

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "✅ SOVEREIGN SYSTEM DEPLOYED" -ForegroundColor Green
    Write-Host ""
    Write-Host "🌐 Services:" -ForegroundColor Yellow
    Write-Host "   Truth Engine: http://localhost:5050" -ForegroundColor Cyan
    Write-Host "   Ollama:       http://localhost:11434" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "📁 Next steps:" -ForegroundColor Yellow
    Write-Host "   1. Open sovereign.code-workspace in VS Code" -ForegroundColor White
    Write-Host "   2. Run 'Truth: Rebuild Index' task" -ForegroundColor White
    Write-Host "   3. Test search: http://localhost:5050/search?q=sovereign" -ForegroundColor White
    Write-Host ""
    Write-Host "🚀 System is SOVEREIGN and OPERATIONAL" -ForegroundColor Green
} else {
    Write-Host "❌ Deployment failed. Check Docker installation." -ForegroundColor Red
    exit 1
}