# scripts/governance/Receive-SealedPacket.ps1
param(
    [Parameter(Mandatory=$true)]
    [string]$Path
)

$ErrorActionPreference = "Stop"
$ScriptBase = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Resolve-Path (Join-Path $ScriptBase "../..")

# Load Sovereign Crypto
. (Join-Path $ScriptBase "../sovereign/SovereignCrypto.ps1")

# Use specific public key for the sender (here we assume same for demo)
$pubKeyPath = Join-Path $ProjectRoot "keys/sovereign.pub"
if (-not (Test-Path $pubKeyPath)) {
    Write-Error "Public key not found at $pubKeyPath"
    exit 1
}

$publicKey = Get-Content $pubKeyPath -Raw

if (-not (Test-Path $Path)) {
    Write-Error "Packet not found at $Path"
    exit 1
}

$sealedPacket = Get-Content $Path | ConvertFrom-Json
$canonical = $sealedPacket.data | ConvertTo-Json -Compress
$signature = $sealedPacket.signature

$isValid = [SovereignCrypto]::VerifySignature($publicKey, $canonical, $signature)

if ($isValid) {
    Write-Host "[VALID] Packet signature verified." -ForegroundColor Green
    $packet = $sealedPacket.data
    Write-Host "Type: $($packet.metadata.type)" -ForegroundColor Cyan
    Write-Host "From: $($packet.metadata.sender)" -ForegroundColor Cyan
    Write-Host "Payload: $($packet.payload)" -ForegroundColor White
    
    # Archive packet
    $archiveDir = Join-Path $ProjectRoot "transport/archive"
    if (-not (Test-Path $archiveDir)) { New-Item -ItemType Directory $archiveDir | Out-Null }
    
    $archivePath = Join-Path $archiveDir (Split-Path $Path -Leaf)
    Move-Item $Path $archivePath -Force
    Write-Host "Packet archived to: $archivePath" -ForegroundColor Gray
    
    # Log to ledger
    $logScript = Join-Path $ScriptBase "log_decision.py"
    $packetId = $packet.metadata.packet_id
    $type = $packet.metadata.type
    $decisionText = '{"event": "sealed_packet_received", "packet_id": "' + $packetId + '", "type": "' + $type + '", "status": "verified"}'
    python $logScript $decisionText
} else {
    Write-Host "[INVALID] Packet signature verification failed!" -ForegroundColor Red
    # Log failure
    $logScript = Join-Path $ScriptBase "log_decision.py"
    $decisionText = '{"event": "sealed_packet_received", "status": "failed", "path": "' + $Path.Replace('\','\\') + '"}'
    python $logScript $decisionText
    exit 1
}
