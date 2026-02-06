# Operational Invariants (OPS)

- INV-OPS-001 Evidence before escalation: No “we’re ready” without artifacts (receipts, hashes, or build outputs) pinned to the decision.
- INV-OPS-002 Changes require a receipt: Any change to scripts/templates must emit an append-only receipt (id, who, when, what-hash, reason).
- INV-OPS-003 Halt on disagreement: If monitors/validators disagree, stop and log; do not auto-resolve. Require human adjudication or further evidence.
- INV-OPS-004 Append-only everywhere that matters: No overwrites in logs/bundles/builds; use JSONL or immutably versioned artifacts.

## Autonomous Runtime Constraints (ARC)

- INV-ARC-001 Mandatory Preflight: No script may execute without validating its starting state against pinned invariants.
- INV-ARC-002 Evidenced Exit: No script may complete without emitting a trajectory record (evidence fragment or receipt).
- INV-ARC-003 Hard Abort on Breach: If an invariant is violated, scripts must halt immediately and log state; partial progress must be reversible.
- INV-ARC-004 Deterministic Entry: Scripts must consume explicitly defined state; no "shadow inputs" or unmodeled environment variables.
