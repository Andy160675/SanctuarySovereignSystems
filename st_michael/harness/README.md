# ST MICHAEL Rust Harness

> **Status**: Placeholder — Implementation pending Rust workspace integration

## Purpose

The Rust harness provides cryptographic enforcement that cannot be bypassed by Python runtime manipulation:

1. **Signature Verification** — Validate identity signatures on votes
2. **Override Proof Verification** — Ensure proofs haven't been tampered with
3. **Delay Enforcement** — Hardware-timer-backed cooling period enforcement
4. **Ledger Anchoring** — Hash chain anchoring for audit trail

## Planned Components

```
harness/
├── Cargo.toml
├── src/
│   ├── lib.rs           # Library entry point
│   ├── signature.rs     # Ed25519/GPG signature verification
│   ├── proof.rs         # Override proof validation
│   ├── delay.rs         # 72h cooling period enforcement
│   └── anchor.rs        # Ledger hash chain operations
└── tests/
    └── integration_tests.rs
```

## Integration

The harness will be called from Python via:

```python
# Option 1: Subprocess
result = subprocess.run(
    ["st_michael_harness", "verify", "--proof", proof_path],
    capture_output=True
)

# Option 2: PyO3 bindings (future)
from st_michael_harness import verify_signature, enforce_delay
```

## Output Format

All harness operations produce `ST_MICHAEL_VOTE_RESULT.json`:

```json
{
  "operation": "verify_override",
  "proposal_id": "PROP-2025-001",
  "status": "VERIFIED",
  "signature_valid": true,
  "cooling_complete": true,
  "quorum_verified": true,
  "timestamp": "2025-12-03T23:00:00Z",
  "harness_hash": "abc123..."
}
```

## Security Model

- Harness binary is signed and verified at boot
- No network access — pure cryptographic operations
- All inputs/outputs logged for audit
- Panic on any verification failure (fail-secure)

---

*Implementation: Pending integration with `/crates/` workspace*
