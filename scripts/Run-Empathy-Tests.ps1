param(
  [int]$MonteCarloN = 1000
)
$ErrorActionPreference = 'Stop'

function New-Dir($p){ if (-not [string]::IsNullOrWhiteSpace($p)) { New-Item -ItemType Directory -Force -Path $p | Out-Null } }

function Resolve-PythonExe($workspaceRoot){
  $venvPy = Join-Path $workspaceRoot 'env/Scripts/python.exe'
  if (Test-Path -LiteralPath $venvPy) { return $venvPy }
  return 'python'
}

function Invoke-PythonLogged(
  [string]$PythonExe,
  [string]$ScriptPath,
  [string]$LogPath,
  [hashtable]$Env = $null,
  [string]$WorkingDirectory = $null
){
  if (-not (Test-Path -LiteralPath $ScriptPath)) {
    throw "Python script not found: $ScriptPath"
  }
  New-Dir (Split-Path -Parent $LogPath)

  $oldEnv = @{}
  if ($Env) {
    foreach ($k in $Env.Keys) {
      $oldEnv[$k] = (Get-Item -Path "Env:$k" -ErrorAction SilentlyContinue).Value
      Set-Item -Path "Env:$k" -Value ([string]$Env[$k])
    }
  }

  try {
    $prefix = ''
    if (-not [string]::IsNullOrWhiteSpace($WorkingDirectory)) {
      $prefix = 'cd /d "{0}" && ' -f $WorkingDirectory
    }
    $cmd = '{0}"{1}" "{2}" 1>"{3}" 2>&1' -f $prefix, $PythonExe, $ScriptPath, $LogPath
    cmd /c $cmd | Out-Null
    return $LASTEXITCODE
  } finally {
    if ($Env) {
      foreach ($k in $Env.Keys) {
        if ($null -eq $oldEnv[$k]) {
          Remove-Item -Path "Env:$k" -ErrorAction SilentlyContinue
        } else {
          Set-Item -Path "Env:$k" -Value $oldEnv[$k]
        }
      }
    }
  }
}

$ws = Split-Path -Parent $PSScriptRoot
$runRoot = Join-Path $ws 'Data/test_runs'
New-Dir $runRoot
$stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$runDir = Join-Path $runRoot $stamp
New-Dir $runDir

$pythonExe = Resolve-PythonExe $ws
$pyPath = if ($env:PYTHONPATH) { "$ws;$($env:PYTHONPATH)" } else { "$ws" }

$deterministic = Join-Path $ws 'agi/tests/deterministic/test_cases.py'
$monte = Join-Path $ws 'agi/tests/monte_carlo/run_redteam.py'
$fuzz = Join-Path $ws 'agi/tests/fuzz/run_dep_fuzz.py'

Write-Host "[RUN] Deterministic" -ForegroundColor Cyan
$detLog = Join-Path $runDir 'deterministic.out'
$detExit = Invoke-PythonLogged -PythonExe $pythonExe -ScriptPath $deterministic -LogPath $detLog -Env @{ PYTHONPATH = $pyPath } -WorkingDirectory $ws
if ($detExit -ne 0) {
  Write-Host "[FAIL] Deterministic tests (exit $detExit)" -ForegroundColor Red
  Get-Content -Path $detLog -Tail 200
  exit $detExit
}

Write-Host "[RUN] Monte Carlo ($MonteCarloN)" -ForegroundColor Cyan
$mcLog = Join-Path $runDir 'monte_carlo.out'
$mcExit = Invoke-PythonLogged -PythonExe $pythonExe -ScriptPath $monte -LogPath $mcLog -Env @{ MC_N = "${MonteCarloN}"; PYTHONPATH = $pyPath } -WorkingDirectory $ws
if ($mcExit -ne 0) {
  Write-Host "[WARN] Redteam script exited non-zero (exit $mcExit)" -ForegroundColor Yellow
}

Write-Host "[RUN] Fuzz" -ForegroundColor Cyan
$fzLog = Join-Path $runDir 'fuzz.out'
$fzExit = Invoke-PythonLogged -PythonExe $pythonExe -ScriptPath $fuzz -LogPath $fzLog -Env @{ PYTHONPATH = $pyPath } -WorkingDirectory $ws
if ($fzExit -ne 0) {
  Write-Host "[WARN] Fuzz script exited non-zero (exit $fzExit)" -ForegroundColor Yellow
}

Write-Host "[DONE] Logs -> $runDir" -ForegroundColor Green
