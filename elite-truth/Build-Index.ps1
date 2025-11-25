# Elite Truth Engine - Build Sovereign Index
# This script builds the AI-powered search index for sovereign corpus

[CmdletBinding()]
param(
    [string]$CorpusPath = ".\SovereignTruth",
    [string]$IndexPath = ".\index"
)

Write-Host "🔥 ELITE TRUTH ENGINE - BUILDING SOVEREIGN INDEX" -ForegroundColor Red
Write-Host "===========================================" -ForegroundColor Red
Write-Host "Target: $CorpusPath" -ForegroundColor Cyan
Write-Host "Output: $IndexPath" -ForegroundColor Cyan
Write-Host ""

# Verify corpus exists
if (!(Test-Path $CorpusPath)) {
    Write-Host "❌ ERROR: Corpus path not found: $CorpusPath" -ForegroundColor Red
    exit 1
}

# Count files in corpus
$corpusFiles = Get-ChildItem -Path $CorpusPath -Recurse -File | Where-Object { $_.Extension -in @('.md', '.txt', '.py', '.ps1', '.yaml', '.yml', '.json') }
Write-Host "📊 Found $($corpusFiles.Count) files in corpus" -ForegroundColor Green

Write-Host ""
Write-Host "🔨 Building index with txtai..." -ForegroundColor Yellow

try {
    # Run Python script
    python ".\build_index.py" $CorpusPath $IndexPath
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "✅ SOVEREIGN INDEX BUILT SUCCESSFULLY!" -ForegroundColor Green
        Write-Host "💡 Use Ask-Truth function to query the index" -ForegroundColor Cyan
    } else {
        Write-Host "❌ Index build failed!" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "❌ Error running Python script: $_" -ForegroundColor Red
    exit 1
}