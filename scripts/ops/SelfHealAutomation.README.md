# SelfHealAutomation.ps1 — The Blade of Truth

## Overview

Perform bounded, repeatable self-healing checks and remediations on a single host.

## Design Principles

- **Safety over completeness**
- **Explicit scope and guardrails**
- **Predictable behaviour under failure**
- **Clear logs for audit and incident review**

## This Script is NOT

- An orchestrator
- A policy engine
- A general-purpose automation framework

## Quick Start

```powershell
# Audit-only mode (observe, no action)
.\SelfHealAutomation.ps1 -Once -AuditOnly

# Single cycle with remediation
.\SelfHealAutomation.ps1 -Once

# Continuous mode with custom interval
.\SelfHealAutomation.ps1 -IntervalSeconds 60

# With configuration file
.\SelfHealAutomation.ps1 -ConfigPath .\config.json
```

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `-Once` | Switch | False | Run single cycle and exit |
| `-AuditOnly` | Switch | False | Observe only, no remediation |
| `-ConfigPath` | String | None | Path to JSON config file |
| `-LogPath` | String | `.\SelfHealAutomation.log` | Human-readable log |
| `-JsonLogPath` | String | `.\SelfHealAutomation.jsonl` | JSONL audit log |
| `-IntervalSeconds` | Int | 300 | Seconds between cycles |

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success — all checks passed |
| 1 | Partial — some checks failed, some actions blocked |
| 2 | Failure — circuit breaker tripped |

## Checks Catalogue

| Check | Purpose | Remediation |
|-------|---------|-------------|
| `Check-DiskSpace` | Detect low disk space | `Invoke-CleanTempFiles` |
| `Check-CriticalService` | Verify service running | `Invoke-RestartService` |
| `Check-NetworkConnectivity` | Test network reachability | None (observe only) |

## Guardrails

| Guardrail | Default | Purpose |
|-----------|---------|---------|
| MaxActionsPerCycle | 3 | Prevent runaway remediation |
| CooldownSeconds | 300 | Prevent rapid repeated actions |
| CircuitBreakerLimit | 5 | Hard stop after consecutive failures |
| AuditOnly | False | Complete remediation lockout |

## Configuration File Schema

```json
{
    "diskThresholdPercent": 10,
    "criticalServices": ["Spooler", "wuauserv"],
    "networkTarget": "8.8.8.8",
    "intervalSeconds": 300,
    "maxActionsPerCycle": 3,
    "cooldownSeconds": 300
}
```

## Log Format

### Human Log
```
[2026-02-03T10:30:00.000Z] [INFO] [Cycle] ========== CYCLE 1 START ==========
[2026-02-03T10:30:00.100Z] [AUDIT] [Check-DiskSpace] Disk space OK
[2026-02-03T10:30:00.200Z] [WARN] [Check-CriticalService] Service NOT running: Spooler
[2026-02-03T10:30:00.300Z] [ACTION] [Remediation] EXECUTING: Invoke-RestartService
```

### JSONL Audit Log
```json
{"timestamp":"2026-02-03T10:30:00.000Z","level":"INFO","component":"Cycle","message":"CYCLE 1 START","hostname":"SERVER01","auditOnly":false}
```

## Test Checklist

1. **Audit-only mode**: `.\SelfHealAutomation.ps1 -Once -AuditOnly`
   - Expected: All checks run, no remediations executed

2. **Single cycle**: `.\SelfHealAutomation.ps1 -Once`
   - Expected: Checks run, eligible remediations execute

3. **Guardrail test**: Trigger multiple failures
   - Expected: Actions blocked after MaxActionsPerCycle

4. **Circuit breaker**: Simulate consecutive failures
   - Expected: Circuit trips after limit

5. **Config load**: `.\SelfHealAutomation.ps1 -Once -AuditOnly -ConfigPath .\test.json`
   - Expected: Config values applied

## Known Limitations

- Network check has no remediation (observe only)
- Service restart limited to approved list
- No log rotation (external responsibility)

## Version History

| Version | Date | Notes |
|---------|------|-------|
| 1.0.0 | 2026-02-03 | Initial release under Intent Contract |

## Authorship

- **Author**: Architect
- **Steward**: Manus AI
- **Trust Class**: T2 (PRE-APPROVED within bounds)
