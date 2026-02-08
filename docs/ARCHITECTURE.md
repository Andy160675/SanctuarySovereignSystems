# Architecture

## Core Principle: Subtractive Invariance

The engine enforces governance by eliminating impossible states rather than detecting violations after the fact.

```
VIABLE = TOTAL - FORBIDDEN
```

This is implemented through a pipeline where each phase removes a class of illegal states before the next phase executes.

## Pipeline Flow

```
Signal Created
    │
    ▼
┌─────────────┐
│ LEGALITY    │ ← Eliminates structurally illegal signals
│ GATE (P3)   │   (forbidden states, integrity failures, schema violations)
└──────┬──────┘
       │ legal signals only
       ▼
┌─────────────┐
│ ROUTER      │ ← Deterministic hierarchical routing
│ (P2)        │   Ambiguity → halt (never guess)
└──────┬──────┘
       │ routed signals only
       ▼
┌─────────────┐
│ AUTHORITY   │ ← Jurisdiction-checked execution
│ HANDLER     │   Wrong handler → escalate up the ladder
└──────┬──────┘
       │ execution result
       ▼
┌─────────────┐
│ AUDIT       │ ← Every decision hash-chained
│ LEDGER (P4) │   Append-only, boot-validated
└─────────────┘
```

## Authority Ladder

Three tiers with strict separation:

```
STEWARD (highest)
    │
    │  escalation
    ▼
INNOVATOR
    │
    │  escalation
    ▼
OPERATOR (lowest)
```

- Signals enter at the authority level matching their `authority` field
- If the handler can't process → escalate up
- If escalation exhausts all levels → halt
- No cross-authority direct calls (enforced by legality gate)

## Constitutional Schema

`constitution.json` defines the complete governance envelope:

- **What signals can exist** (signal schema)
- **Where they can go** (routing grammar)
- **What is forbidden** (legality constraints)
- **What happens on failure** (failure semantics)
- **How fast things must happen** (timing contracts)
- **How everything is recorded** (audit requirements)
- **What governance profiles are available** (archetypes)

The constitution loads at boot. If it fails validation, the engine does not start.

## Governance Archetypes

The configurator compiles governance profiles into runtime configs:

**Managerial** — Active steward oversight. Routing rules can be modified at runtime. Upgrades enabled. For systems requiring adaptive governance.

**Immutable** — Locked routing. No runtime modifications. No upgrades. Steward is passive observer only. For systems requiring maximum predictability.

**Federated** — Quorum-based decisions. Routing changes require multi-party agreement. For distributed governance across organizational boundaries.

All archetypes are validated against kernel invariants before activation. No archetype can violate the 7 invariants.

## Extension Model (Season 3)

Extensions declare a manifest specifying:
- Required authority level
- What they read from
- What they write to
- Whether they modify routing or legality

The compliance gate validates every extension against kernel invariants. Non-compliant extensions cannot activate. No extension can modify the halt doctrine, authority ladder, or audit requirements.

## Failure Philosophy

**Prefer stopping to lying.**

| Component | Failure | Response |
|-----------|---------|----------|
| Router | No matching rule | **Halt** |
| Router | Inactive handler | Escalate |
| Legality | Any violation | Terminate + contain |
| Audit | Write failure | **Halt** |
| Audit | Chain corruption | Truncate to last valid |
| Timing | Contract breach | Escalate |
| Authority | Escalation exhausted | **Halt** |
| Any | Unknown failure | **Halt** |

The system never guesses. It never continues silently. If it can't prove the next step is safe, it stops.
