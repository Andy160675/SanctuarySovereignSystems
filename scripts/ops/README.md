# SelfHealAutomation — The Blade of Truth

> **Bounded, repeatable self-healing for sovereign infrastructure.**

```
╔══════════════════════════════════════════════════════════════════════════════╗
║  VERSION:    2.0.0                                                           ║
║  TRUST:      T2 (PRE-APPROVED within bounds)                                 ║
║  ALARP:      100% — All hazards documented and controlled                    ║
║  STATUS:     DONE-DONE                                                       ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

## Purpose

SelfHealAutomation performs **safe, bounded self-healing checks and remediations** on a single host. It observes a small set of known operational conditions, attempts predefined corrective actions when those conditions fail, and records what happened with **court-grade audit trails**.

**Design Principles:**
- Safety over completeness
- Explicit scope and guardrails
- Predictable behaviour under failure
- Clear logs for audit and incident review

**This script is NOT:**
- An orchestrator
- A policy engine
- A general-purpose automation framework

---

## Quick Start

### Audit-Only Mode (Observe, No Action)
```powershell
.\SelfHealAutomation.ps1 -Once -AuditOnly
```

### Dry-Run Mode (Show What Would Change)
```powershell
.\SelfHealAutomation.ps1 -Once -DryRun
```

### Single Active Cycle
```powershell
.\SelfHealAutomation.ps1 -Once
```

### Continuous Mode
```powershell
.\SelfHealAutomation.ps1 -IntervalSeconds 60
```

### With Custom Configuration
```powershell
.\SelfHealAutomation.ps1 -Once -ConfigPath .\SelfHealConfig.json
```

### JSON Output for Fleet Tools
```powershell
.\SelfHealAutomation.ps1 -Once -AuditOnly -OutputJson
```

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           SELFHEALAUTOMATION                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐  │
│  │   CHECKS    │───▶│  GUARDRAILS │───▶│ REMEDIATION │───▶│  EVIDENCE   │  │
│  │             │    │             │    │             │    │             │  │
│  │ • Disk      │    │ • MaxActions│    │ • Disk      │    │ • JSONL     │  │
│  │ • Services  │    │ • Cooldown  │    │ • Service   │    │ • Hash Chain│  │
│  │ • Network   │    │ • Circuit   │    │ • Network   │    │ • Evidence  │  │
│  │ • Security  │    │ • Resources │    │ • Security  │    │ • Files     │  │
│  └─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘  │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                         CONFIGURATION                                │   │
│  │  SelfHealConfig.json → Thresholds, Services, Intervals, Limits      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 13-Layer Implementation

| Layer | Name | Status |
|-------|------|--------|
| 1 | Intent & Contract | ✅ Complete |
| 2 | File Birth & Skeleton | ✅ Complete |
| 3 | Logging & Evidence | ✅ Complete |
| 4 | Guardrails Contract | ✅ Complete |
| 5 | Checks Catalogue | ✅ Complete |
| 6 | Remediation Catalogue | ✅ Complete |
| 7 | Idempotency & Safety | ✅ Complete |
| 8 | Configuration Injection | ✅ Complete |
| 9 | Human Observability | ✅ Complete |
| 10 | Test Harness | ✅ Complete |
| 11 | Integration Touchpoints | ✅ Complete |
| 12 | Code Quality | ✅ Complete |
| 13 | Release Gate | ✅ Complete |

---

## ALARP Compliance (+10% Beyond Market)

This system includes a complete **ALARP Register** documenting:

- **5 Hazard Classes:** Escalation, Corruption, Drift, Misuse, Availability
- **22 Controls:** 14 Preventive, 7 Detective, 1 Corrective
- **Rejected Controls:** Documented with disproportionality justifications
- **Residual Risks:** Explicitly stated and accepted

**Third-Party Reviewable:** A third party can answer "Why didn't you do more?" from the artifacts alone.

See: `ALARP_Register.yaml`

---

## Configuration Reference

### SelfHealConfig.json

```json
{
    "$schema": "./SelfHealConfig.schema.json",
    "version": "1.0",
    "checks": {
        "disk": {
            "criticalThresholdGb": 10,
            "warningThresholdGb": 20,
            "driveLetter": "C"
        },
        "services": {
            "criticalServices": ["Spooler", "wuauserv", "WinRM"]
        },
        "network": {
            "target": "8.8.8.8",
            "dnsTarget": "dns.google",
            "latencyThresholdMs": 100
        }
    },
    "remediations": {
        "maxActionsPerCycle": 3,
        "cooldownMinutes": 5,
        "circuitBreakerLimit": 5
    },
    "intervalSeconds": 300
}
```

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `-Once` | Switch | False | Run single cycle and exit |
| `-AuditOnly` | Switch | False | Observe only, no remediation |
| `-DryRun` | Switch | False | Show what would change |
| `-ConfigPath` | String | None | Path to JSON config file |
| `-LogPath` | String | `$env:ProgramData\SelfHeal\logs\*.log` | Human-readable log |
| `-JsonLogPath` | String | `$env:ProgramData\SelfHeal\logs\*.jsonl` | JSONL audit log |
| `-EvidencePath` | String | `$env:ProgramData\SelfHeal\evidence` | Evidence storage |
| `-IntervalSeconds` | Int | 300 | Seconds between cycles |
| `-OutputJson` | Switch | False | JSON status to stdout |
| `-Status` | Switch | False | Quick status check |

---

## Exit Codes

| Code | Name | Meaning |
|------|------|---------|
| 0 | Success | Healthy or remediated |
| 1 | ScriptError | Bug in script |
| 2 | UnhealthyNoAction | Unhealthy, audit mode active |
| 3 | GuardrailBlocked | Action blocked by guardrail |
| 4 | ConfigError | Configuration invalid |

---

## Guardrails

### Limits
- **MaxActionsPerCycle:** 3 (configurable)
- **CooldownSeconds:** 300 (5 minutes between same action)
- **CircuitBreakerLimit:** 5 consecutive failures trips breaker

### Emergency Override
Create file: `$env:ProgramData\SelfHeal\EMERGENCY_OVERRIDE.txt`

**Warning:** Override bypasses all guardrails. Use only in emergencies.

---

## Evidence Chain

### Log Format (JSONL)
```json
{
    "timestamp": "2026-02-03T12:00:00.000Z",
    "level": "ACTION",
    "component": "Invoke-DiskRemediation",
    "message": "Cleaned 15 files, freed 250MB",
    "correlationId": "abc123def456",
    "machineId": "SERVER01",
    "details": { "filesRemoved": 15, "freedMb": 250 },
    "previousHash": "a1b2c3d4e5f6g7h8",
    "hash": "h8g7f6e5d4c3b2a1"
}
```

### Evidence Files
```json
{
    "evidenceId": "guid",
    "timestamp": "ISO8601",
    "checkName": "Check-DiskHealth",
    "preState": { "freeGb": 5 },
    "postState": { "freeGb": 8 },
    "decision": "Guardrail approved",
    "action": "Invoke-DiskRemediation",
    "result": "Success",
    "chainHash": "linked-to-log-chain"
}
```

---

## Deployment

### Manual Installation
```powershell
.\Deploy-SelfHeal.ps1
```

### With Scheduled Task
```powershell
.\Deploy-SelfHeal.ps1 -CreateScheduledTask -TaskInterval 5
```

### Uninstall
```powershell
.\Deploy-SelfHeal.ps1 -Uninstall
```

---

## Testing

### Unit Tests
```powershell
.\Test-SelfHeal.ps1 -UnitTest
```

### Integration Tests
```powershell
.\Test-SelfHeal.ps1 -IntegrationTest
```

### Full Test Suite
```powershell
.\Test-SelfHeal.ps1 -UnitTest -IntegrationTest
```

---

## Troubleshooting

### Circuit Breaker Tripped
1. Check logs: `$env:ProgramData\SelfHeal\logs\SelfHealAutomation.jsonl`
2. Identify failing remediation
3. Fix underlying issue
4. Delete or edit: `$env:ProgramData\SelfHeal\guardrail_state.json`
5. Restart script

### Logs Not Writing
1. Verify directory exists: `$env:ProgramData\SelfHeal\logs`
2. Check permissions
3. Run as Administrator

### JSON Output Invalid
1. Use `-OutputJson` with `-Once`
2. Redirect stderr: `2>$null`
3. Parse last JSON line from stdout

---

## Files

| File | Purpose |
|------|---------|
| `SelfHealAutomation.ps1` | Main script |
| `SelfHealConfig.schema.json` | Configuration schema |
| `SelfHealConfig.example.json` | Example configuration |
| `Test-SelfHeal.ps1` | Test harness |
| `Deploy-SelfHeal.ps1` | Deployment helper |
| `ALARP_Register.yaml` | Risk register |
| `ALARP_Register.schema.yaml` | Risk register schema |
| `README.md` | This file |

---

## Governance KPIs

| Metric | Target | Measurement |
|--------|--------|-------------|
| Override rate | < 5% | WARN logs / total cycles |
| Unlogged action rate | 0% | Zero tolerance |
| Time to contain | < 5 min | Incident response |
| Evidence chain breaks | 0% | Hash validation |
| Circuit breaker trips | < 1/month | guardrail_state.json |

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 2.0.0 | 2026-02-03 | Elite edition with ALARP register |
| 1.0.0 | 2026-02-03 | Initial release |

---

## License & Attribution

**Author:** Architect  
**Steward:** Manus AI  
**Trust Class:** T2 (PRE-APPROVED within bounds)  
**Classification:** Sovereign Infrastructure  

---

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║                    THE BLADE OF TRUTH — DONE DONE                            ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
```
