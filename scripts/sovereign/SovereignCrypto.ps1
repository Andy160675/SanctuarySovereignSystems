# scripts/sovereign/SovereignCrypto.ps1
# Core cryptographic utilities for the Sovereign System.
# Provides RSA key generation, signing, and verification.

class SovereignCrypto {
    static [string] GenerateNewKey() {
        $rsa = [System.Security.Cryptography.RSACryptoServiceProvider]::new(2048)
        try {
            # Export private key in XML format (standard for .NET RSA)
            return $rsa.ToXmlString($true)
        }
        finally {
            $rsa.Dispose()
        }
    }

    static [string] GetPublicKey([string]$privateKeyXml) {
        $rsa = [System.Security.Cryptography.RSACryptoServiceProvider]::new()
        try {
            $rsa.FromXmlString($privateKeyXml)
            return $rsa.ToXmlString($false)
        }
        finally {
            $rsa.Dispose()
        }
    }

    static [string] SignMessage([string]$privateKeyXml, [string]$message) {
        $rsa = [System.Security.Cryptography.RSACryptoServiceProvider]::new()
        try {
            $rsa.FromXmlString($privateKeyXml)
            $data = [System.Text.Encoding]::UTF8.GetBytes($message)
            $signature = $rsa.SignData($data, [System.Security.Cryptography.CryptoConfig]::MapNameToOID("SHA256"))
            return [Convert]::ToBase64String($signature)
        }
        finally {
            $rsa.Dispose()
        }
    }

    static [bool] VerifySignature([string]$publicKeyXml, [string]$message, [string]$signatureBase64) {
        $rsa = [System.Security.Cryptography.RSACryptoServiceProvider]::new()
        try {
            $rsa.FromXmlString($publicKeyXml)
            $data = [System.Text.Encoding]::UTF8.GetBytes($message)
            $signature = [Convert]::FromBase64String($signatureBase64)
            return $rsa.VerifyData($data, [System.Security.Cryptography.CryptoConfig]::MapNameToOID("SHA256"), $signature)
        }
        catch {
            return $false
        }
        finally {
            $rsa.Dispose()
        }
    }
}
