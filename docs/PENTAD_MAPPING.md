# PENTAD ROLE MAPPING (TEMPLATE)

This document maps physical hardware to the five roles of the Pentad.
Final assignment pending result of `Invoke-FleetInventory.ps1`.

| Pentad Role | Required Specs | Physical Host (Node-0) | Physical Host (Node-1) | Status |
|-------------|----------------|------------------------|------------------------|--------|
| **Orchestrator** | High Availability, Low Latency | PC-CORE-1 (Primary) | Tenerife-Master (Back) | Active |
| **Truth Engine** | High RAM (32GB+), NVMe | PC-CORE-1 | N/A | Active |
| **Agent Fleet** | Multi-core, GPU/NPU opt | NODE-MOBILE | Tenerife-Worker-1 | In-Progress |
| **Evidence Store**| Immutable Storage, GPG | NAS-01 | Tenerife-NAS | Active |
| **Boardroom UI** | Low overhead | NODE-MOBILE | Tenerife-Master | In-Progress |

## Resilience Forcing Functions (Codified)

The following rules are hardcoded in `scripts/health/Test-PentadResilience.ps1`:

1. **PC A down > 15m**: System enters **READ-ONLY**. No new workflows authorized.
2. **PC E down > 5m**: **SEVER EXTERNAL NETWORK**. Isolation protocol engaged.
3. **NAS unreachable > 10m**: **HALT NEW WORKFLOWS**. Evidence chain integrity is priority.
4. **Any 2 heads unresponsive**: System state set to **DEGRADED**. Operator notified.
5. **Any 3 heads unresponsive**: **MANUAL ONLY**. Autonomous operation suspended.
6. **Evidence chain gap**: Immediate execution halt.

## R&D Pipeline Roles

- **Research (PC D)**: Strategic horizon analysis and benchmarking.
- **Design (PC A)**: Protocol specification and security architectural review.
- **Implementation (PC B)**: Code generation and automated testing.
- **Verification (PC C)**: Compliance auditing and integrity checks.
- **Safety (PC E)**: Boundary enforcement and experimental isolation.
- **Archive (NAS)**: Immutable storage of research artifacts and evidence.

## Node-1 (Tenerife) - Cold Witness

Node-1 acts as a **Cold Witness**. It proves system state even if Node-0 is compromised. It never acts as a hot failover for execution, maintaining the "Truth at a Distance" principle.

*Last updated: 2026-02-05*
