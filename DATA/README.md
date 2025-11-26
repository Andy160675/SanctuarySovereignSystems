# DATA Directory Schema

This directory contains the sovereign system's runtime data. Each subdirectory serves a specific purpose in the governance and audit architecture.

## Directory Structure

```
DATA/
├── _anchor_chain.json      # The hash chain (audit spine)
├── _automation_log.json    # Automation dispatch history
├── _commits/               # Governance decision artifacts
│   └── decision_*.json     # Individual governance commits
│   └── *.anchor.json       # Local anchor sidecars
│   └── *.external.json     # External witness sidecars
├── _chain_verifications/   # Chain verification reports
│   └── verify_*.json       # Per-session verification results
├── _pipelines/             # Automation pipeline artifacts
│   └── poc/                # POC pipeline triggers
│   └── data/               # Data pipeline triggers
│   └── review/             # Review pipeline triggers
│   └── approvals/          # Approval pipeline triggers
└── _work/                  # Working directory for sessions
    └── snapshots/          # Per-session snapshots
    └── audit.json          # Rolling audit index
```

## File Schemas

### _anchor_chain.json

The cryptographic audit spine. Array of anchor records:

```json
[
  {
    "index": 0,
    "timestamp": "2025-11-26T14:30:35Z",
    "record_type": "governance_commit",
    "file_path": "DATA/_commits/decision_*.json",
    "payload_hash": "<sha256 of file contents>",
    "prev_chain_hash": "GENESIS",
    "chain_hash": "<sha256 of prev_chain_hash + payload_hash>"
  }
]
```

### Governance Commits (decision_*.json)

```json
{
  "commit_id": "govcommit-<session_id>",
  "session_id": "<timestamp>-<uuid>",
  "record_type": "governance_commit",
  "topic": "Description of the decision",
  "requested_by": "ui:operator",
  "requested_at": "2025-11-26T14:30:35Z",
  "governance": {
    "overall_passed": true,
    "requires_reconciliation": false,
    "consensus_action": "VERIFY_CHAIN_NOW",
    "consensus_outcome": "APPROVED",
    "rationale": "Why this action was taken"
  },
  "snapshot_path": null
}
```

### Verification Reports (verify_*.json)

```json
{
  "valid": true,
  "total_anchors": 7,
  "verified_anchors": 7,
  "errors": [],
  "governance_commit_id": "govcommit-<session_id>",
  "governance_session_id": "<session_id>",
  "triggered_at": "2025-11-26T14:30:35Z",
  "triggered_by": "ui:operator"
}
```

## Initialization

On first run, these directories are created automatically. For a fresh start:

```bash
# Clear all runtime data (preserves schema)
rm -rf DATA/_*
```

The system will recreate the structure on next governance action.

## Cross-Platform Notes

- All file paths use forward slashes internally
- Line endings are normalized to LF for consistent hashing
- Timestamps are UTC in ISO 8601 format

## Security Considerations

- This directory contains audit-sensitive data
- Do not commit actual chain data to public repositories
- Use `.gitignore` to exclude runtime artifacts
- Keep `.gitkeep` files to preserve directory structure

---

*"The organism's memory lives here."*
