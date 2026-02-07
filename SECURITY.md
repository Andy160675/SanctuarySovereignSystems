# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 1.0.x   | Yes       |

## Reporting a Vulnerability

If you discover a security vulnerability in Sanctuary Sovereign Systems, please report it responsibly. Do not open a public issue.

Contact the maintainers directly through GitHub's private vulnerability reporting feature on this repository.

## Security Architecture

This framework enforces security through **structural impossibility** rather than runtime checks. The three Axioms of Sovereignty (Evidence Immutability, Ambiguity-to-Containment, and Illegality-as-Unrepresentable) are enforced at the type system and kernel routing level.

All signals are hash-chained, all authority is separated, and all failures resolve to halt states. There are no backdoors, no silent fall-throughs, and no permissive defaults.

## Auth Code

`CODEX-V1-SUBTRACTIVE-INVARIANCE`
