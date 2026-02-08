# Sovereign Recursion Engine

**Constitutional governance for autonomous systems.**

The Sovereign Recursion Engine enforces machine-readable authority, deterministic routing, and cryptographic auditability for AI agent systems. It implements subtractive invariance — eliminating impossible states architecturally rather than detecting them after the fact.

```
VIABLE = TOTAL - FORBIDDEN
```

The engine cannot structurally misroute authority or propagate illegal state. Not because it's clever. Because the impossible states are architecturally excluded.

## Why This Exists

AI execution speed is outpacing governance capability. The bottleneck is no longer automation — it's trust, verification, and accountable authority. This engine provides the governance substrate that makes fast inner loops safe to run.

Constraints aren't friction. They're what lets you keep the throttle open.

## Quick Start

```bash
# Clone
git clone https://github.com/Andy160675/SanctuarySovereignSystems.git
cd SanctuarySovereignSystems

# Run all invariant tests (74 tests)
python -m sovereign_engine.tests.run_all
```

Requires Python 3.8+. No external dependencies.

## Architecture

```
constitution.json → signals → router → legality → audit → timing → failure → configurator → engine → extensions
      P0              P1        P2        P3        P4       P5       P6          P7           P8        P9
```

Each phase depends on all prior phases. Skipping breaks containment.

See [`SEASONS.md`](SEASONS.md) for normative Season 1/2/3 boundary definitions.

| Phase | Module | Purpose |
|-------|--------|---------|
| 0 | `phase0_constitution.py` | Schema loader, validator, 16 invariant tests |
| 1 | `phase1_signals.py` | Typed signal tuple, factory, schema-guarded bus |
| 2 | `phase2_router.py` | Deterministic hierarchical router, authority handlers |
| 3 | `phase3_legality.py` | Pre-routing legality gate, containment events |
| 4 | `phase4_audit.py` | SHA-256 hash-chained append-only audit ledger |
| 5 | `phase5_timing.py` | Latency contracts, watchdog, halt controller |
| 6 | `phase6_failure.py` | Failure matrix, health monitors |
| 7 | `phase7_configurator.py` | Archetype compiler (managerial / immutable / federated) |
| 8 | `phase8_engine.py` | Full integration — boot-to-route pipeline |
| 9 | `phase9_extensions.py` | Season-3 plugin scaffold + compliance gate |

## The 7 Invariants

These are non-negotiable. All contributions must preserve them.

1. **Halt doctrine** — Ambiguity → halt. Unknown failure → halt. Halt rule is FIRST in routing grammar.
2. **Authority separation** — Three tiers: operator / innovator / steward. No cross-authority direct calls.
3. **Legality gate** — Illegal states terminated before routing. Every termination produces a containment event.
4. **Audit chain** — SHA-256 hash-linked, append-only, boot-validated. Corruption triggers truncation.
5. **Escalation protocol** — operator → innovator → steward. Exhausted escalation → halt.
6. **Default safe failure** — Router failure → halt. Audit failure → halt. Unknown → halt.
7. **Extension boundary** — Season-3 bolt-ons cannot modify halt doctrine, authority ladder, or audit requirements.

## Constitutional Ground Truth

`sovereign_engine/configs/constitution.json` is the canonical schema. It defines:

- **Authority ladder** — operator → innovator → steward
- **Signal schema** — required fields, valid types, domains, authority levels
- **Routing grammar** — deterministic rules with halt-on-ambiguity default
- **Forbidden states** — structural prohibitions enforced before routing
- **Failure semantics** — prescribed response for every failure type
- **Timing contracts** — latency bounds for routing, escalation, audit, halt
- **Audit requirements** — append-only, hash-chained, boot-validated
- **Archetypes** — governance profiles (managerial, immutable, federated)

Every module enforces this schema. Nothing overrides it.

## Governance Archetypes

The configurator (Phase 7) compiles governance profiles into runtime configurations:

| Archetype | Steward Role | Routing | Upgrades |
|-----------|-------------|---------|----------|
| **Managerial** | Active | Mutable | Enabled |
| **Immutable** | Passive | Locked | Disabled |
| **Federated** | Quorum | Quorum-mutable | Quorum-gated |

No archetype may violate the 7 kernel invariants.

## Design Principles

**Prefer stopping to lying.** The minus sign is not decorative.

- Ambiguity → halt (router)
- Unknown failure → halt (constitution)
- Corruption → truncate or seal (audit)
- Halted bus only accepts halt signals (signal bus)
- No silent success — every state transition is audited

## Project Structure

```
SanctuarySovereignSystems/
├── README.md
├── LICENSE                          # Apache 2.0
├── CLAUDE.md                        # Claude Code anchor prompt
├── CONTRIBUTING.md                  # Contribution rules
├── SEASONS.md                       # Normative Season 1/2/3 boundary definitions
├── sovereign_engine/
│   ├── configs/
│   │   └── constitution.json        # Constitutional ground truth
│   ├── core/
│   │   ├── phase0_constitution.py   # 420 lines
│   │   ├── phase1_signals.py        # 267 lines
│   │   ├── phase2_router.py         # 301 lines
│   │   ├── phase3_legality.py       # 183 lines
│   │   ├── phase4_audit.py          # 247 lines
│   │   ├── phase5_timing.py         # 178 lines
│   │   ├── phase6_failure.py        # 142 lines
│   │   ├── phase7_configurator.py   # 135 lines
│   │   ├── phase8_engine.py         # 288 lines
│   │   └── phase9_extensions.py     # 136 lines
│   └── tests/
│       └── run_all.py               # 74 tests incl. adversarial
└── docs/
    ├── ARCHITECTURE.md
    └── INVARIANTS.md
```

**Total: 3,331 lines of Python. 103 lines of JSON. Zero dependencies.**

## Test Results

```
74/74 tests passing. All invariants hold.

Phase 0 (Constitutional Ground Truth):  9/9
Phase 1 (Typed Signal Substrate):      11/11
Phase 2 (Router & Authority Kernel):    8/8
Phase 3 (Legality Gate):               9/9
Phase 4 (Audit Ledger):                6/6
Phase 5 (Timing & Halt):               4/4
Phase 6 (Failure Semantics):           4/4
Phase 7 (Configurator):                5/5
Phase 8 (Full Engine):                10/10
Phase 9 (Extension Scaffold):          5/5
Adversarial Scenarios:                  3/3
```

## License

Apache License 2.0 — see [LICENSE](LICENSE).

## Author

Andy Jones — [Codex Sovereign Systems](https://sovereigsanctuarysystems.co.uk)

---

*If the industrial age optimized production, and the information age optimized distribution, the AI age will optimize alignment under acceleration.*
