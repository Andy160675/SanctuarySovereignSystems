# Operational Invariants (OPS)

- INV-OPS-001 Evidence before escalation: No “we’re ready” without artifacts (receipts, hashes, or build outputs) pinned to the decision.
- INV-OPS-002 Changes require a receipt: Any change to scripts/templates must emit an append-only receipt (id, who, when, what-hash, reason).
- INV-OPS-003 Halt on disagreement: If monitors/validators disagree, stop and log; do not auto-resolve. Require human adjudication or further evidence.
- INV-OPS-004 Append-only everywhere that matters: No overwrites in logs/bundles/builds; use JSONL or immutably versioned artifacts.
