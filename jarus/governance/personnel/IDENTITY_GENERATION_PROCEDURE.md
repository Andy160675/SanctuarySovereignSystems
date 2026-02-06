# IDENTITY GENERATION PROCEDURE (IDG_PROC_01)

## Purpose
To establish a cryptographic identity for each member of the Aegis Governance leadership team. This identity is used for signing role assignments, governing decisions, and authorizing system actions.

## Procedure Overview
The procedure involves creating a SHA-256 keypair (Public/Private) and verifying the public key against the team member's role assignment.

### Step 1: Keypair Generation
Use the `SovereignCrypto.ps1` script (or OpenSSL/Python equivalent) to generate a local keypair.

**PowerShell Example:**
```powershell
.\scripts\sovereign\SovereignCrypto.ps1 -GenerateKey -Name "STEVEN_CEO"
```

### Step 2: Public Key Export
Export the public key for inclusion in the `GOVERNANCE_ROSTER.json`.

### Step 3: Role Assignment Signing
Sign the respective `ROLE_ASSIGNMENT_*.md` file using the private key.

```powershell
.\scripts\sovereign\SovereignCrypto.ps1 -SignFile "Governance\personnel\ROLE_ASSIGNMENT_CEO.md" -Key "STEVEN_CEO.key"
```

### Step 4: Verification
The Auditor (Chris Bevan) or Architect (Andy Jones) will verify the signature against the public key stored in the roster.

## Requirements
- **Storage:** Private keys MUST NOT be committed to the repository. They must be stored in a secure, off-site vault (e.g., Physical SSD).
- **Format:** Trinity-compliant SHA-256 signatures.
- **Verification:** Machine-verifiable via the Evidence Ledger.

## Team Status
- **Steven:** Pending
- **Chris Bevan:** Pending
- **Phil Segal:** Pending
- **Tom Maher:** Pending
- **Andy Jones:** ACTIVE (Manual Verification)
