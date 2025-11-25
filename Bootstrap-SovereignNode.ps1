# =============================================================================
# Bootstrap-SovereignNode.ps1
# Sovereign Away Kit - Node Bootstrap Script
# =============================================================================
#
# PURPOSE: Create C:\Sovereign directory structure and unpack repos from USB
# LOCATION: F:\Bootstrap-SovereignNode.ps1 (SOV_BOOT USB)
#
# Expected folder structure on USB:
#   F:\repos\
#       sovereign-system.zip
#       Blade2AI.zip (optional)
#   F:\SovereignNode.code-workspace (template)
#
# =============================================================================

param(
    [string]$TargetRoot = "C:\Sovereign"
)

$ErrorActionPreference = "Stop"

function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $color = switch ($Level) {
        "INFO"  { "White" }
        "WARN"  { "Yellow" }
        "ERROR" { "Red" }
        "OK"    { "Green" }
        default { "White" }
    }
    Write-Host "[$ts] [$Level] $Message" -ForegroundColor $color
}

Write-Host ""
Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host "  SOVEREIGN NODE BOOTSTRAP" -ForegroundColor Cyan
Write-Host "  Creating Local Node Structure" -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host ""

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$reposZipDir = Join-Path $scriptDir "repos"

Write-Log "Script directory: $scriptDir"
Write-Log "Target root: $TargetRoot"
Write-Log "Repos ZIP directory: $reposZipDir"
Write-Host ""

# =============================================================================
# Create Directory Structure
# =============================================================================

Write-Log "Creating directory structure..."

$directories = @(
    $TargetRoot,
    "$TargetRoot\Repos",
    "$TargetRoot\Workspace",
    "$TargetRoot\Evidence",
    "$TargetRoot\Logs",
    "$TargetRoot\Sandbox"
)

foreach ($dir in $directories) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
        Write-Log "Created: $dir" "OK"
    } else {
        Write-Log "Exists: $dir" "INFO"
    }
}

# =============================================================================
# Unpack Repos from ZIP (if available)
# =============================================================================

Write-Host ""
Write-Log "Checking for repo archives..."

if (Test-Path $reposZipDir) {
    $zipFiles = Get-ChildItem "$reposZipDir\*.zip" -ErrorAction SilentlyContinue

    foreach ($zip in $zipFiles) {
        $repoName = [System.IO.Path]::GetFileNameWithoutExtension($zip.Name)
        $targetPath = "$TargetRoot\Repos\$repoName"

        if (Test-Path $targetPath) {
            Write-Log "Repo already exists, skipping: $repoName" "INFO"
        } else {
            Write-Log "Extracting: $($zip.Name) -> $targetPath"
            try {
                Expand-Archive -Path $zip.FullName -DestinationPath "$TargetRoot\Repos" -Force
                Write-Log "Extracted: $repoName" "OK"
            } catch {
                Write-Log "Failed to extract $repoName : $_" "ERROR"
            }
        }
    }
} else {
    Write-Log "No repos directory found on USB" "WARN"
    Write-Log "You can manually clone repos into $TargetRoot\Repos" "INFO"
}

# =============================================================================
# Copy or Create VS Code Workspace
# =============================================================================

Write-Host ""
Write-Log "Setting up VS Code workspace..."

$workspaceTemplate = Join-Path $scriptDir "SovereignNode.code-workspace"
$workspaceTarget = "$TargetRoot\SovereignNode.code-workspace"

if (Test-Path $workspaceTemplate) {
    Copy-Item $workspaceTemplate $workspaceTarget -Force
    Write-Log "Copied workspace file from USB" "OK"
} else {
    # Create a default workspace
    $workspaceContent = @{
        folders = @(
            @{ path = "Repos\\sovereign-system" }
            @{ path = "Repos\\Blade2AI" }
            @{ path = "Workspace" }
        )
        settings = @{
            "files.autoSave" = "afterDelay"
            "editor.formatOnSave" = $true
        }
    }

    $workspaceContent | ConvertTo-Json -Depth 4 | Out-File $workspaceTarget -Encoding utf8
    Write-Log "Created default workspace file" "OK"
}

# =============================================================================
# Copy Away Kit README
# =============================================================================

$readmeSource = Join-Path $scriptDir "AWAY_KIT_README.md"
$readmeAlt = Join-Path $scriptDir "README_AWAY_KIT_v1.md"
$readmeTarget = "$TargetRoot\AWAY_KIT_README.md"

if (Test-Path $readmeSource) {
    Copy-Item $readmeSource $readmeTarget -Force
    Write-Log "Copied Away Kit README" "OK"
} elseif (Test-Path $readmeAlt) {
    Copy-Item $readmeAlt $readmeTarget -Force
    Write-Log "Copied Away Kit README (alt)" "OK"
}

# =============================================================================
# Create Quick-Start Scripts
# =============================================================================

Write-Host ""
Write-Log "Creating quick-start scripts..."

# START-SOVEREIGN.bat
$startBat = @"
@echo off
cd /d "$TargetRoot\Repos\sovereign-system"
echo Starting Sovereign System...
python mock_services.py
"@
$startBat | Out-File "$TargetRoot\START-SOVEREIGN.bat" -Encoding ascii
Write-Log "Created START-SOVEREIGN.bat" "OK"

# OPEN-WORKSPACE.bat
$openWs = @"
@echo off
code "$TargetRoot\SovereignNode.code-workspace"
"@
$openWs | Out-File "$TargetRoot\OPEN-WORKSPACE.bat" -Encoding ascii
Write-Log "Created OPEN-WORKSPACE.bat" "OK"

# =============================================================================
# Summary
# =============================================================================

Write-Host ""
Write-Host "=" * 60 -ForegroundColor Green
Write-Host "  NODE BOOTSTRAP COMPLETE" -ForegroundColor Green
Write-Host "=" * 60 -ForegroundColor Green
Write-Host ""
Write-Host "  Target Root:     $TargetRoot"
Write-Host "  Repos:           $TargetRoot\Repos\"
Write-Host "  Workspace:       $TargetRoot\SovereignNode.code-workspace"
Write-Host ""
Write-Host "  Quick Start:"
Write-Host "    1. Open VS Code:  $TargetRoot\OPEN-WORKSPACE.bat"
Write-Host "    2. Start System:  $TargetRoot\START-SOVEREIGN.bat"
Write-Host "    3. Open Browser:  http://localhost:8502/health"
Write-Host ""

# Check if repos were actually unpacked
$repoCount = (Get-ChildItem "$TargetRoot\Repos" -Directory -ErrorAction SilentlyContinue).Count
if ($repoCount -eq 0) {
    Write-Log "No repos unpacked. Clone manually or provide ZIP archives." "WARN"
} else {
    Write-Log "Found $repoCount repo(s) in $TargetRoot\Repos" "OK"
}

Write-Host ""
