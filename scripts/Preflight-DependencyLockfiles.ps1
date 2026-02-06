param(
    [Parameter(Mandatory = $false)]
    [string]$Root = "$PSScriptRoot/.."
)

$ErrorActionPreference = "Stop"

Write-Host "=== Preflight: Checking dependency lockfiles ===" -ForegroundColor Cyan
$rootPath = (Resolve-Path $Root).Path

if (-not (Test-Path $rootPath)) {
    Write-Error "Root path not found: $rootPath"
    exit 1
}

# Patterns that *must* exist somewhere in the tree
$lockPatterns = @(
    "package-lock.json",
    "yarn.lock",
    "pnpm-lock.yaml",
    "poetry.lock",
    "Pipfile.lock"
)

$found = @{}

foreach ($pattern in $lockPatterns) {
    $matches = Get-ChildItem -Path $rootPath -Recurse -File -Filter $pattern -ErrorAction SilentlyContinue
    if ($matches) {
        $found[$pattern] = $matches | ForEach-Object { $_.FullName }
    }
}

if ($found.Keys.Count -eq 0) {
    Write-Host ""
    Write-Host "? Preflight FAILED: No recognised dependency lockfiles found." -ForegroundColor Red
    Write-Host "Expected at least one of:" -ForegroundColor Yellow
    $lockPatterns | ForEach-Object { Write-Host "  - $_" }
    Write-Host ""
    Write-Host "Add the appropriate lockfile(s) and re-run." -ForegroundColor Yellow
    exit 1
}

Write-Host "? Lockfiles detected:" -ForegroundColor Green
foreach ($k in $found.Keys) {
    Write-Host "  $k"
    $found[$k] | ForEach-Object { Write-Host "    $_" }
}

Write-Host "=== Preflight: OK ===" -ForegroundColor Green
exit 0
