# scripts/governance/Send-SealedPacket.ps1
param(
    [Parameter(Mandatory=$true)]
    [string]$Payload,
    [string]$Type = "HEARTBEAT",
    [string]$Recipient = "Manus"
)

$ErrorActionPreference = "Stop"
$ScriptBase = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Resolve-Path (Join-Path $ScriptBase "../..")

# Load Sovereign Crypto
. (Join-Path $ScriptBase "../sovereign/SovereignCrypto.ps1")

$keyPath = Join-Path $ProjectRoot "keys/sovereign.key"
if (-not (Test-Path $keyPath)) {
    Write-Error "Private key not found at $keyPath"
    exit 1
}

$privateKey = Get-Content $keyPath -Raw

$packet = @{
    metadata = @{
        type = $Type
        sender = "LocalNode"
        recipient = $Recipient
        timestamp = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
        packet_id = [Guid]::NewGuid().ToString()
    }
    payload = $Payload
}

# Generate canonical representation for signing
$canonical = $packet | ConvertTo-Json -Compress
$signature = [SovereignCrypto]::SignMessage($privateKey, $canonical)

$sealedPacket = @{
    data = $packet
    signature = $signature
    signer = "LocalNode_RSA_2048"
}

$json = $sealedPacket | ConvertTo-Json -Depth 10
$filename = "PACKET_$($packet.metadata.packet_id).json"
$outPath = Join-Path $ProjectRoot "transport/outbound/$filename"

$json | Out-File $outPath -Encoding utf8

Write-Host "Sealed packet created: $outPath" -ForegroundColor Green
Write-Host "Signature: $signature" -ForegroundColor Gray

# Log to ledger
$logScript = Join-Path $ScriptBase "log_decision.py"
$packetId = $packet.metadata.packet_id
$decisionText = '{"event": "sealed_packet_sent", "packet_id": "' + $packetId + '", "type": "' + $Type + '", "recipient": "' + $Recipient + '"}'
python $logScript $decisionText
