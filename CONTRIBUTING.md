# Contributing to Sanctuary Sovereign Systems

## Constitutional Constraints

All contributions must comply with the Sovereign Constitutional Codex. Specifically:

1. **No contribution may weaken the three Axioms** (Evidence Immutability, Ambiguity-to-Containment, Illegality-as-Unrepresentable).
2. **No contribution may bypass the Legality Lane** or introduce untyped signals.
3. **All new signal types must be registered** in the `SIGNAL_AUTHORITY_MAP` with an appropriate authority level.
4. **All contributions must pass the compliance test suite** before merge.

## Process

1. Fork the repository.
2. Create a feature branch from `main`.
3. Implement your changes.
4. Run `python3 tests/compliance/test_constitutional_compliance.py` — all tests must pass.
5. Run `python3 tests/integration/test_kernel_pipeline.py` — all tests must pass.
6. Submit a pull request with a clear description of what impossibility your change addresses or what extension point it uses.

## Code Standards

All code must include docstrings that reference the relevant Article of the Codex. Every module must state which constitutional impossibility it enforces or which extension point it operates within.

## Auth Code

`CODEX-V1-SUBTRACTIVE-INVARIANCE`
