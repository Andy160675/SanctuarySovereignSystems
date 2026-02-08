# Contributing to the Sovereign Recursion Engine

## The Rule

All contributions must preserve the 7 kernel invariants. No exceptions. If your change breaks an invariant, it does not merge — regardless of the feature value.

Run all tests before submitting:

```bash
python -m sovereign_engine.tests.run_all
```

74+ tests must pass. Zero P0 violations.

## What You Can Do

**Extend** — Add new signal types, domain handlers, legality rules, or Season-3 extensions. All extensions must pass the compliance gate in Phase 9.

**Harden** — Add tests, especially adversarial scenarios. The more ways we prove the invariants hold under stress, the stronger the engine.

**Optimize** — Improve performance within existing contracts. Timing contracts in the constitution define acceptable latency. Stay within them.

**Document** — Improve architecture docs, add examples, clarify behaviour.

## What You Cannot Do

- Modify the halt doctrine
- Remove or weaken the authority ladder
- Make the audit ledger mutable or bypassable
- Allow silent failures
- Add dependencies (the engine is zero-dependency by design)
- Introduce any state transition that isn't audited

## Process

1. Fork the repo
2. Create a feature branch from `main`
3. Make your changes
4. Run `python -m sovereign_engine.tests.run_all` — all must pass
5. Add tests for any new behaviour
6. Submit a PR with a clear description of what changed and why

## Code Style

- Pure Python. No external dependencies.
- Typed exceptions for every failure mode.
- Every new module must declare its phase dependency.
- Comments explain *why*, not *what*.

## Constitutional Amendments

Changes to `constitution.json` are constitutional amendments, not regular PRs. They require:

1. Written justification
2. Impact analysis on all downstream phases
3. Full test suite pass after amendment
4. Review by project maintainer

The constitution is the ground truth. Treat it accordingly.
