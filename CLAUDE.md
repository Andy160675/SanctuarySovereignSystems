# CLAUDE.md — Sovereign Recursion Engine

## What This Is

Production kernel for the Sovereign Recursion Engine.
Constitutional AI governance implementing subtractive invariance: `VIABLE = TOTAL - FORBIDDEN`

**74/74 tests passing. All invariants hold.**

## Run Tests

```bash
python -m sovereign_engine.tests.run_all
```

## Ground Truth

`sovereign_engine/configs/constitution.json` is the canonical constitutional schema.
Every module enforces it. Nothing overrides it.

## Dependency Chain

```
constitution → signals → router → legality → audit → timing → failure → configurator → engine → extensions
     P0           P1        P2        P3        P4       P5       P6          P7           P8        P9
```

Each phase depends on all prior phases. Skipping breaks containment.

Season boundaries are defined in `SEASONS.md`. Season 2 = this kernel. Season 3 = extensions via Phase 9 compliance gate.

## Module Map

| File | Phase | Purpose |
|------|-------|---------|
| `core/phase0_constitution.py` | 0 | Schema loader, validator, 16 invariant tests |
| `core/phase1_signals.py` | 1 | Typed signal tuple, factory, schema-guarded bus |
| `core/phase2_router.py` | 2 | Deterministic hierarchical router, authority handlers |
| `core/phase3_legality.py` | 3 | Pre-routing legality gate, containment events |
| `core/phase4_audit.py` | 4 | SHA-256 hash-chained append-only audit ledger |
| `core/phase5_timing.py` | 5 | Latency contracts, watchdog, halt controller |
| `core/phase6_failure.py` | 6 | Failure matrix, health monitors |
| `core/phase7_configurator.py` | 7 | Archetype compiler (managerial/immutable/federated) |
| `core/phase8_engine.py` | 8 | Full integration — boot-to-route pipeline |
| `core/phase9_extensions.py` | 9 | Season-3 plugin scaffold + compliance gate |
| `tests/run_all.py` | — | 74 tests incl. adversarial scenarios |
| `configs/constitution.json` | 0 | Machine-readable constitutional schema |

## 7 Non-Negotiable Invariants

1. **Halt doctrine**: Ambiguity → halt. Halt rule is FIRST in routing grammar.
2. **Authority separation**: operator / innovator / steward. No cross-authority direct calls.
3. **Legality gate**: Illegal states terminated before routing. Every termination audited.
4. **Audit chain**: SHA-256 hash-linked, append-only, boot-validated, truncate-on-corruption.
5. **Escalation protocol**: operator → innovator → steward. Exhausted → halt.
6. **Default safe failure**: Router failure → halt. Audit failure → halt. Unknown → halt.
7. **Extension boundary**: Season-3 bolt-ons cannot modify halt doctrine, authority ladder, or audit.

## Rules for Extending

- **All new work extends the kernel. Nothing rewrites it.**
- New modules must register invariant tests with Phase 0.
- New signal types must be added to `constitution.json` and validated.
- New authority levels require constitutional amendment (not code change).
- New failure types must map to halt/escalate/contain — no silent failures.
- Run tests after every change. 74+ must pass.

## Document Control

Format: `CSS-[DOMAIN]-[TYPE]-[SEQ]`

### Operational Documents (operations/css-ops/)

| Ref | Title | Status |
|-----|-------|--------|
| CSS-OPS-DOC-003 | Post-SIP Autonomous Execution Engine | v1.0 DRAFT — FOR LT REVIEW |
| CSS-OPS-DOC-004 | PIOPL Agent Deployment Engine | v1.0 DRAFT — FOR LT REVIEW |
| CSS-OPS-DOC-005 | PIOPL Enterprise Operating Plan | v1.0 DRAFT — FOR LT REVIEW |
| CSS-OPS-DOC-006 | Meeting Structures, Escalation Paths & Andon | v1.0 DRAFT — FOR LT REVIEW |
| CSS-OPS-TRACK-001 | Immediate Actions Tracker (5 tracks) | v1.0 LIVE |

Canonical format: `.md` (version-controlled). Distribution: `.docx` (LT sign-off).
See `governance/CSS-DOC-REGISTER-001.md` for full register and `ARTIFACT_REGISTER.json` for SHA-256 integrity verification.

## Owner

Andy Jones — Codex Sovereign Systems
