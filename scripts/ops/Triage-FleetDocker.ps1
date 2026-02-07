<#
.SYNOPSIS
    Sovereign Fleet Docker Triage & Restart Script.
    Captures logs and diagnostic state before performing service restarts.

.DESCRIPTION
    1. Resolves targets from CONFIG\pentad\BINDING_TABLE.md or explicit params.
    2. Performs remote diagnostic (docker ps, docker logs) via WinRM or SSH.
    3. If -Gate is set, requires manual confirmation before restart.
    4. Logs all actions to validation\fleet_triage.jsonl.

.PARAMETER Targets
    Explicit list of hostnames or IPs. If omitted, uses BINDING_TABLE.md.

.PARAMETER Gate
    Enables safety gate (confirmation prompt).

.PARAMETER ServiceName
    Specific docker service/container name to target. Defaults to all.
#>

param(
    [string[]]$Targets,
    [switch]$Gate,
    [string]$ServiceName = "*",
    [string]$LogFile = "validation\fleet_triage.jsonl"
)

$ErrorActionPreference = "Continue"

function Write-TriageLog {
    param($HostName, $Action, $Status, $Details)
    $entry = @{
        Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
        Host = $HostName
        Action = $Action
        Status = $Status
        Details = $Details
    }
    $entry | ConvertTo-Json -Compress | Out-File $LogFile -Append -Encoding UTF8
}

function Invoke-RemoteDocker {
    param($ComputerName, $Command)
    
    # Heuristic: If it looks like a Linux NAS or has a specific hostname pattern, use SSH.
    # Otherwise, attempt Invoke-Command (WinRM).
    
    if ($ComputerName -match "192.168.4.78" -or $ComputerName -match "DXP4800PLUS") {
        # Linux/SSH Path (Assuming key-based auth or local relay)
        $sshCmd = "ssh -o ConnectTimeout=5 -o BatchMode=yes root@$ComputerName `"$Command`""
        try {
            $output = iex $sshCmd 2>&1
            return $output
        } catch {
            return "SSH_FAILED: $($_.Exception.Message)"
        }
    } else {
        # Windows/WinRM Path
        try {
            $output = Invoke-Command -ComputerName $ComputerName -ScriptBlock { 
                param($cmd) 
                iex $cmd 
            } -ArgumentList $Command -ErrorAction Stop 2>&1
            return $output
        } catch {
            return "WINRM_FAILED: $($_.Exception.Message)"
        }
    }
}

# 1. Resolve Targets
if (-not $Targets) {
    Write-Host "Resolving targets from BINDING_TABLE.md..." -ForegroundColor Cyan
    $table = Get-Content "CONFIG\pentad\BINDING_TABLE.md"
    $Targets = $table | Where-Object { $_ -match "\| \*\*" } | ForEach-Object {
        $parts = $_ -split "\|"
        $ip = $parts[2].Trim()
        if ($ip -match "\d+\.\d+\.\d+\.\d+") { $ip }
    }
}

Write-Host "Found $($Targets.Count) targets: $($Targets -join ', ')" -ForegroundColor Gray

foreach ($t in $Targets) {
    Write-Host "`n[TRIAGE] Target: $t" -ForegroundColor White -BackgroundColor Blue
    
    # 2. Capture Evidence (ps + logs)
    Write-Host "  - Capturing container state..."
    $psOutput = Invoke-RemoteDocker -ComputerName $t -Command "docker ps --filter name=$ServiceName --format '{{.ID}} {{.Names}} {{.Status}}'"
    
    if ($psOutput -match "FAILED") {
        Write-Host "  [!] Connectivity/Access failure on $t" -ForegroundColor Red
        Write-TriageLog -HostName $t -Action "diagnose" -Status "failed" -Details $psOutput
        continue
    }

    Write-Host "  - Containers found:`n$psOutput" -ForegroundColor Gray
    Write-TriageLog -HostName $t -Action "diagnose" -Status "success" -Details $psOutput

    # 3. Handle Gate
    if ($Gate) {
        $choice = Read-Host "Proceed with RESTART on $t? (y/N)"
        if ($choice -notmatch "y") {
            Write-Host "  - Skipping restart as requested." -ForegroundColor Yellow
            continue
        }
    }

    # 4. Perform Restart
    Write-Host "  - Executing restart command..." -ForegroundColor Yellow
    $restartCmd = "docker restart \$(docker ps -q --filter name=$ServiceName)"
    if ($t -match "192.168.4.78") {
         # Linux needs slightly different quoting for the subshell expansion in SSH
         $restartCmd = "docker restart \$(docker ps -q --filter name=$ServiceName)"
    }

    $res = Invoke-RemoteDocker -ComputerName $t -Command $restartCmd
    Write-Host "  - Result: $res"
    Write-TriageLog -HostName $t -Action "restart" -Status "completed" -Details $res
}

Write-Host "`nTriage session complete. Logs: $LogFile" -ForegroundColor Green
