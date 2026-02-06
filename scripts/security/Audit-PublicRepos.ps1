<#
.SYNOPSIS
    Audit-PublicRepos.ps1 — Native PowerShell secret scanner for public repos.
    
.DESCRIPTION
    Scans the local filesystem for common secret patterns using native tools.
    Focuses on the three identified public repositories.
#>

param(
    [string[]]$Repos = @("sovereign-monorepo", "sovereign-elite-infra", "master-1")
)

$Patterns = @(
    "ghp_[a-zA-Z0-9]{36}",         # GitHub PAT
    "AIza[0-9A-Za-z-_]{35}",       # Google API Key
    "sk-ant-api03-[a-zA-Z0-9-_]{93}ant-api03-", # Anthropic API Key
    "sk-[a-zA-Z0-9]{48}",          # OpenAI API Key
    "-----BEGIN RSA PRIVATE KEY-----",
    'password\s*[:=]\s*["' + "'].*['" + '"]',
    "client_secret"
)

Write-Host "═══ Sovereign Public Repo Audit ═══" -ForegroundColor Cyan

foreach ($repo in $Repos) {
    Write-Host "`n[Audit] Scanning $repo..." -ForegroundColor Yellow
    
    # In a real monorepo setup, these might be subdirectories or siblings
    $targetPath = Join-Path (Get-Location) $repo
    if (-not (Test-Path $targetPath)) {
        # Fallback to current directory if scanning the root of one of these
        if ($PSScriptRoot -match $repo -or (Get-Location).Path -match $repo) {
            $targetPath = Get-Location
        } else {
            Write-Host "  ! Path not found: $targetPath (Skipping)" -ForegroundColor Gray
            continue
        }
    }

    foreach ($pattern in $Patterns) {
        Write-Host "  Checking pattern: $pattern" -ForegroundColor Gray
        # Use git grep if it's a git repo, otherwise native Select-String
        try {
            if (Test-Path (Join-Path $targetPath ".git")) {
                git -C $targetPath grep -EI --line-number "$pattern"
            } else {
                Get-ChildItem -Path $targetPath -Recurse -File -Exclude "*.pyc", "*.git", "*.exe" | 
                    Select-String -Pattern $pattern | 
                    ForEach-Object { "  FIND: $($_.FileName):$($_.LineNumber): $($_.Line.Trim())" }
            }
        } catch {
            Write-Host "  Error scanning $repo with $pattern" -ForegroundColor Red
        }
    }
}

Write-Host "`nAudit complete." -ForegroundColor Cyan
