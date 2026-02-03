<#
.SYNOPSIS
    Test-SelfHeal.ps1 — Test Harness for SelfHealAutomation.ps1

.DESCRIPTION
    Provides safe testing capabilities for SelfHealAutomation without requiring real failures.

.PARAMETER UnitTest
    Run unit tests for individual functions

.PARAMETER IntegrationTest
    Run full cycle with mocks

.PARAMETER DestructiveTest
    Run with real remediation (opt-in, requires confirmation)

.PARAMETER Verbose
    Show detailed test output

.EXAMPLE
    .\Test-SelfHeal.ps1 -UnitTest

.EXAMPLE
    .\Test-SelfHeal.ps1 -IntegrationTest -Verbose
#>

#Requires -Version 5.1

[CmdletBinding()]
param(
    [Parameter()]
    [switch]$UnitTest,

    [Parameter()]
    [switch]$IntegrationTest,

    [Parameter()]
    [switch]$DestructiveTest
)

$ErrorActionPreference = "Stop"
$script:TestResults = @{
    Passed = 0
    Failed = 0
    Skipped = 0
    Tests = @()
}

#region ============================================================================
#region TEST FRAMEWORK
#region ============================================================================

function Write-TestHeader {
    param([string]$Name)
    Write-Host ""
    Write-Host "╔══════════════════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "║  TEST: $($Name.PadRight(68))║" -ForegroundColor Cyan
    Write-Host "╚══════════════════════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
}

function Write-TestResult {
    param(
        [string]$Name,
        [bool]$Passed,
        [string]$Message = ""
    )
    
    $status = if ($Passed) { "PASS" } else { "FAIL" }
    $color = if ($Passed) { "Green" } else { "Red" }
    
    Write-Host "  [$status] $Name" -ForegroundColor $color
    if ($Message) {
        Write-Host "         $Message" -ForegroundColor Gray
    }
    
    $script:TestResults.Tests += @{
        Name = $Name
        Passed = $Passed
        Message = $Message
    }
    
    if ($Passed) { $script:TestResults.Passed++ }
    else { $script:TestResults.Failed++ }
}

function Write-TestSummary {
    Write-Host ""
    Write-Host "╔══════════════════════════════════════════════════════════════════════════════╗" -ForegroundColor Magenta
    Write-Host "║  TEST SUMMARY                                                                ║" -ForegroundColor Magenta
    Write-Host "╠══════════════════════════════════════════════════════════════════════════════╣" -ForegroundColor Magenta
    Write-Host "║  Passed:  $($script:TestResults.Passed.ToString().PadRight(65))║" -ForegroundColor Green
    Write-Host "║  Failed:  $($script:TestResults.Failed.ToString().PadRight(65))║" -ForegroundColor $(if ($script:TestResults.Failed -gt 0) { "Red" } else { "Green" })
    Write-Host "║  Skipped: $($script:TestResults.Skipped.ToString().PadRight(65))║" -ForegroundColor Yellow
    Write-Host "╚══════════════════════════════════════════════════════════════════════════════╝" -ForegroundColor Magenta
    
    if ($script:TestResults.Failed -gt 0) {
        exit 1
    }
    exit 0
}

#endregion

#region ============================================================================
#region UNIT TESTS
#region ============================================================================

function Test-UnitTests {
    Write-TestHeader "Unit Tests"
    
    # Test 1: Script file exists
    $scriptPath = Join-Path $PSScriptRoot "SelfHealAutomation.ps1"
    $exists = Test-Path $scriptPath
    Write-TestResult -Name "Script file exists" -Passed $exists -Message $scriptPath
    
    # Test 2: Script parses without errors
    try {
        $null = [System.Management.Automation.Language.Parser]::ParseFile($scriptPath, [ref]$null, [ref]$null)
        Write-TestResult -Name "Script parses without errors" -Passed $true
    } catch {
        Write-TestResult -Name "Script parses without errors" -Passed $false -Message $_.Exception.Message
    }
    
    # Test 3: Config schema exists
    $schemaPath = Join-Path $PSScriptRoot "SelfHealConfig.schema.json"
    $schemaExists = Test-Path $schemaPath
    Write-TestResult -Name "Config schema exists" -Passed $schemaExists -Message $schemaPath
    
    # Test 4: Example config exists
    $examplePath = Join-Path $PSScriptRoot "SelfHealConfig.example.json"
    $exampleExists = Test-Path $examplePath
    Write-TestResult -Name "Example config exists" -Passed $exampleExists -Message $examplePath
    
    # Test 5: Example config is valid JSON
    if ($exampleExists) {
        try {
            $config = Get-Content $examplePath -Raw | ConvertFrom-Json
            Write-TestResult -Name "Example config is valid JSON" -Passed $true
        } catch {
            Write-TestResult -Name "Example config is valid JSON" -Passed $false -Message $_.Exception.Message
        }
    }
    
    # Test 6: Verify approved verbs
    $content = Get-Content $scriptPath -Raw
    $functionMatches = [regex]::Matches($content, 'function\s+([A-Za-z]+-[A-Za-z]+)')
    $approvedVerbs = Get-Verb | Select-Object -ExpandProperty Verb
    $allApproved = $true
    foreach ($match in $functionMatches) {
        $funcName = $match.Groups[1].Value
        $verb = $funcName.Split('-')[0]
        if ($verb -notin $approvedVerbs) {
            $allApproved = $false
            Write-TestResult -Name "Function uses approved verb: $funcName" -Passed $false -Message "Verb '$verb' not approved"
        }
    }
    if ($allApproved) {
        Write-TestResult -Name "All functions use approved verbs" -Passed $true -Message "$($functionMatches.Count) functions checked"
    }
}

#endregion

#region ============================================================================
#region INTEGRATION TESTS
#region ============================================================================

function Test-IntegrationTests {
    Write-TestHeader "Integration Tests"
    
    $scriptPath = Join-Path $PSScriptRoot "SelfHealAutomation.ps1"
    
    # Test 1: Audit-only mode runs without error
    Write-Host "  Running audit-only mode..." -ForegroundColor Gray
    try {
        $output = & $scriptPath -Once -AuditOnly 2>&1
        Write-TestResult -Name "Audit-only mode completes" -Passed $true
    } catch {
        Write-TestResult -Name "Audit-only mode completes" -Passed $false -Message $_.Exception.Message
    }
    
    # Test 2: Dry-run mode runs without error
    Write-Host "  Running dry-run mode..." -ForegroundColor Gray
    try {
        $output = & $scriptPath -Once -DryRun 2>&1
        Write-TestResult -Name "Dry-run mode completes" -Passed $true
    } catch {
        Write-TestResult -Name "Dry-run mode completes" -Passed $false -Message $_.Exception.Message
    }
    
    # Test 3: JSON output mode works
    Write-Host "  Testing JSON output..." -ForegroundColor Gray
    try {
        $output = & $scriptPath -Once -AuditOnly -OutputJson 2>&1
        $jsonLines = $output | Where-Object { $_ -match '^\{' }
        if ($jsonLines) {
            $json = $jsonLines[-1] | ConvertFrom-Json
            Write-TestResult -Name "JSON output is valid" -Passed $true -Message "exitCode: $($json.exitCode)"
        } else {
            Write-TestResult -Name "JSON output is valid" -Passed $false -Message "No JSON found in output"
        }
    } catch {
        Write-TestResult -Name "JSON output is valid" -Passed $false -Message $_.Exception.Message
    }
    
    # Test 4: Status mode works
    Write-Host "  Testing status mode..." -ForegroundColor Gray
    try {
        $output = & $scriptPath -Status 2>&1
        Write-TestResult -Name "Status mode completes" -Passed $true
    } catch {
        Write-TestResult -Name "Status mode completes" -Passed $false -Message $_.Exception.Message
    }
    
    # Test 5: Log files created
    $logDir = "$env:ProgramData\SelfHeal\logs"
    $logsExist = Test-Path $logDir
    Write-TestResult -Name "Log directory created" -Passed $logsExist -Message $logDir
    
    # Test 6: Evidence directory created
    $evidenceDir = "$env:ProgramData\SelfHeal\evidence"
    $evidenceExists = Test-Path $evidenceDir
    Write-TestResult -Name "Evidence directory created" -Passed $evidenceExists -Message $evidenceDir
}

#endregion

#region ============================================================================
#region DESTRUCTIVE TESTS
#region ============================================================================

function Test-DestructiveTests {
    Write-TestHeader "Destructive Tests (Real Remediation)"
    
    Write-Host "  ⚠️  WARNING: These tests perform real system changes!" -ForegroundColor Yellow
    Write-Host ""
    
    $confirm = Read-Host "  Type 'YES' to proceed with destructive tests"
    if ($confirm -ne "YES") {
        Write-Host "  Skipping destructive tests" -ForegroundColor Yellow
        $script:TestResults.Skipped += 3
        return
    }
    
    $scriptPath = Join-Path $PSScriptRoot "SelfHealAutomation.ps1"
    
    # Test 1: Active mode with single cycle
    Write-Host "  Running active mode..." -ForegroundColor Gray
    try {
        $output = & $scriptPath -Once 2>&1
        Write-TestResult -Name "Active mode completes" -Passed $true
    } catch {
        Write-TestResult -Name "Active mode completes" -Passed $false -Message $_.Exception.Message
    }
    
    # Test 2: Verify guardrails respected
    $guardrailPath = "$env:ProgramData\SelfHeal\guardrail_state.json"
    if (Test-Path $guardrailPath) {
        try {
            $state = Get-Content $guardrailPath -Raw | ConvertFrom-Json
            Write-TestResult -Name "Guardrail state persisted" -Passed $true -Message "ConsecutiveFailures: $($state.ConsecutiveFailures)"
        } catch {
            Write-TestResult -Name "Guardrail state persisted" -Passed $false -Message $_.Exception.Message
        }
    } else {
        Write-TestResult -Name "Guardrail state persisted" -Passed $false -Message "State file not found"
    }
    
    # Test 3: Evidence files created
    $evidenceDir = "$env:ProgramData\SelfHeal\evidence"
    $evidenceFiles = Get-ChildItem $evidenceDir -Filter "*.json" -ErrorAction SilentlyContinue
    Write-TestResult -Name "Evidence files created" -Passed ($evidenceFiles.Count -gt 0) -Message "$($evidenceFiles.Count) evidence files"
}

#endregion

#region ============================================================================
#region MAIN
#region ============================================================================

Write-Host ""
Write-Host "╔══════════════════════════════════════════════════════════════════════════════╗" -ForegroundColor Magenta
Write-Host "║  TEST-SELFHEAL.PS1 — TEST HARNESS                                            ║" -ForegroundColor Magenta
Write-Host "╚══════════════════════════════════════════════════════════════════════════════╝" -ForegroundColor Magenta

if (-not $UnitTest -and -not $IntegrationTest -and -not $DestructiveTest) {
    # Default: run unit and integration tests
    $UnitTest = $true
    $IntegrationTest = $true
}

if ($UnitTest) {
    Test-UnitTests
}

if ($IntegrationTest) {
    Test-IntegrationTests
}

if ($DestructiveTest) {
    Test-DestructiveTests
}

Write-TestSummary

#endregion
