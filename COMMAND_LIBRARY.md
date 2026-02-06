# Sovereign Command Library

This library documents the primary operational commands for the Sovereign System.

## 1. Governance & Sovereignty

| Command | Description | Output |
|---------|-------------|--------|
| `powershell -File scripts/governance/validate_sovereignty.ps1 -All` | Runs the full sovereignty validation suite (Constitution, Config, Phase, Limits, Ledger). | `validation/<run_id>/` |
| `python scripts/governance/verify_decision_ledger.py` | Verifies the integrity and hash chain of the decision ledger. | `validation/ledger_verify_<ts>.json` |
| `powershell -File scripts/governance/generate_sitrep_pack.ps1` | Generates a full evidence-backed Situation Report (SITREP). | `validation/SITREP_PACK_<ts>/` |
| `powershell -File scripts/governance/Rotate-SovereignKey.ps1` | Rotates the sovereign RSA key pair. | `sovereign.key`, `sovereign.pub` |

## 2. Operations & Deployment

| Command | Description | Output |
|---------|-------------|--------|
| `powershell -File scripts/done_done_deploy.ps1 -AuthCode 0000` | Executes the "Done-Done" deployment sequence with authorization. | `evidence/deployment_seal.json` |
| `powershell -File scripts/ops/Verify-All.ps1 -RepoRoot .` | Performs comprehensive repository integrity verification against manifests. | `evidence/verification/` |
| `powershell -File scripts/ops/Invoke-SovereignElite.ps1` | Runs the Sovereign Elite PoC demonstration (Agentic multi-sphere coordination). | Console Output |
| `powershell -File scripts/ops/SelfHealAutomation.ps1 -Once -AuditOnly` | Runs system self-healing checks in audit-only mode. | `evidence/self_heal/` |
| `powershell -File scripts/ops/Invoke-TrinityLoop.ps1` | Starts the Trinity orchestration loop. | Console/Logs |

## 3. Security & Hacking Suite

| Command | Description | Output |
|---------|-------------|--------|
| `powershell -File scripts/hacking/Invoke-HackingOrchestrator.ps1` | Orchestrates hacking intel ingestion and security scanning. | `validation/security/` |
| `python scripts/hacking/sovereign_security_scanner.py` | Scans for vulnerabilities, misconfigurations, and missing seals. | `validation/security/scan_<ts>.json` |

## 4. Learning & Improvement

| Command | Description | Output |
|---------|-------------|--------|
| `powershell -File scripts/learning/Invoke-LearningSuite.ps1` | Executes the full learning and self-improvement suite. | Learning logs |
| `powershell -File scripts/learning/rapid_self_improvement.ps1` | Runs accelerated self-improvement cycles. | Improvement reports |

## 5. System Utilities

| Command | Description | Output |
|---------|-------------|--------|
| `powershell -File scripts/nightly-master.ps1` | Generates a nightly golden master backup with GPG signing. | `C:\SovereignArchives\` |
| `powershell -File scripts/Healthcheck.ps1` | Quick check of core service availability. | Console Output |
| `python tools/self_heal_monitor.py --write-sitrep` | Updates the live SITREP file with node status. | `evidence/SITREP.md` |

---
*Note: Most PowerShell scripts require elevated permissions or specific environment configurations. Always check the script's .SYNOPSIS for details.*
