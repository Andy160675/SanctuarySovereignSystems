param(
  [int]$ConstitutionDownMinutes = 15,
  [int]$SafetyDownMinutes = 5,
  [int]$NasUnreachableMinutes = 10,
  [string[]]$Heads = @("PC-A","PC-B","PC-C","PC-D","PC-E"),
  [string]$NasHost = "NAS-01"
)

# Simple in-memory heartbeat table (replace with real probes later)
$global:Heartbeat = @{}
$now = Get-Date
foreach ($h in $Heads) { if (-not $Heartbeat.ContainsKey($h)) { $Heartbeat[$h] = $now } }
if (-not $Heartbeat.ContainsKey($NasHost)) { $Heartbeat[$NasHost] = $now }

function Test-HeadHealthy($host) {
  try {
    $ping = Test-Connection -Count 1 -ComputerName $host -Quiet -ErrorAction SilentlyContinue
    if ($ping) { $global:Heartbeat[$host] = Get-Date }
    return [bool]$ping
  } catch { return $false }
}

function Get-MinutesSince($host) {
  $last = $global:Heartbeat[$host]
  if (-not $last) { return [int]::MaxValue }
  return [int]((Get-Date) - $last).TotalMinutes
}

# Probe all heads
$health = @{}
foreach ($h in $Heads) { $health[$h] = Test-HeadHealthy $h }
$nasOk = Test-HeadHealthy $NasHost

$down = ($health.GetEnumerator() | Where-Object { -not $_.Value } | ForEach-Object { $_.Name })
$downCount = $down.Count

$state = "OPERATIONAL"
$actions = @()

# Forcing functions
if (-not $nasOk -and (Get-MinutesSince $NasHost) -ge $NasUnreachableMinutes) {
  $state = "HALT_NEW_WORK"
  $actions += "NAS unreachable > $NasUnreachableMinutes min → Halt new workflows; queue evidence locally"
}

if (-not $health['PC-A'] -and (Get-MinutesSince 'PC-A') -ge $ConstitutionDownMinutes) {
  $state = "READ_ONLY"
  $actions += "PC A down > $ConstitutionDownMinutes min → All heads enter READ-ONLY"
}

if (-not $health['PC-E'] -and (Get-MinutesSince 'PC-E') -ge $SafetyDownMinutes) {
  $actions += "PC E down > $SafetyDownMinutes min → Sever external network (ISOLATE)"
}

if ($downCount -ge 2) {
  $actions += "Any 2 heads unresponsive → DEGRADED"
}
if ($downCount -ge 3) {
  $state = "HUMAN_REQUIRED"
  $actions += "Any 3 heads unresponsive → Suspend autonomy; human operator required"
}

# Output structured health
$result = [pscustomobject]@{
  timestamp = (Get-Date).ToString("o")
  state = $state
  heads = $health
  nas_ok = $nasOk
  down = $down
  actions = $actions
}

$result | ConvertTo-Json -Depth 5
