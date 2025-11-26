# -*- coding: utf-8 -*-
"""
Governed Chain Verification Flow

Turns a manual "Verify Now" action into:
- A governance decision
- A chain-anchored commit
- An optional external anchor
- An automated chain verification run
- A verification artifact suitable for evidence bundles

This ensures no human action exists outside the ledger.
"""

import json
import uuid
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, Optional

from . import anchoring
from . import external_anchor
from . import automation

DATA_ROOT = Path("DATA")
COMMITS_DIR = DATA_ROOT / "_commits"
CHAIN_VERIFY_DIR = DATA_ROOT / "_chain_verifications"


def iso_now() -> str:
    """UTC timestamp in ISO 8601 format."""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _ensure_dirs() -> None:
    """Ensure required directories exist."""
    COMMITS_DIR.mkdir(parents=True, exist_ok=True)
    CHAIN_VERIFY_DIR.mkdir(parents=True, exist_ok=True)


def _new_ids() -> tuple:
    """Generate new session and commit IDs."""
    session_id = f"chain-verify-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}-{uuid.uuid4().hex[:8]}"
    commit_id = f"govcommit-{session_id}"
    return session_id, commit_id


def run_governed_chain_verification(
    requested_by: str = "ui:operator",
    rationale: str = "Manual chain verification triggered from Governance & Evidence Board.",
) -> Dict[str, Any]:
    """
    Main entry point for governed chain verification.

    Creates a governance commit with consensus_action=VERIFY_CHAIN_NOW,
    anchors it locally (and externally if configured),
    dispatches automation which runs verify_chain(),
    persists the verification result,
    and returns a compact summary for UI use.

    Args:
        requested_by: Identity of the requester
        rationale: Reason for the verification request

    Returns:
        Dict with session info, paths, and verification summary
    """
    _ensure_dirs()
    session_id, commit_id = _new_ids()
    topic = "Run chain integrity verification now"

    commit_path = COMMITS_DIR / f"decision_{session_id}.json"

    # --- 1) Governance commit record ---
    commit_record: Dict[str, Any] = {
        "commit_id": commit_id,
        "session_id": session_id,
        "record_type": "governance_commit",
        "topic": topic,
        "requested_by": requested_by,
        "requested_at": iso_now(),
        "governance": {
            "overall_passed": True,
            "requires_reconciliation": False,
            "consensus_action": "VERIFY_CHAIN_NOW",
            "consensus_outcome": "APPROVED",
            "rationale": rationale,
        },
        "snapshot_path": None,
    }

    # Write commit file first (without external anchor - that goes in sidecar)
    commit_path.write_text(json.dumps(commit_record, indent=2), encoding="utf-8")

    # --- 2) Local anchor into hash chain ---
    anchor_receipt = anchoring.append_anchor("governance_commit", commit_path)
    anchor_path = commit_path.with_suffix(".anchor.json")
    anchor_path.write_text(json.dumps(anchor_receipt, indent=2), encoding="utf-8")

    # --- 3) External witness (if configured) - stored in sidecar, not main commit ---
    ext_anchor_path = commit_path.with_suffix(".external.json")
    try:
        ext_req = external_anchor.ExternalAnchorRequest(
            session_id=session_id,
            commit_id=commit_id,
            record_type="governance_commit",
            payload_hash=anchor_receipt.get("payload_hash", ""),
            chain_hash=anchor_receipt.get("chain_hash", ""),
            merkle_root=None,
            timestamp=anchor_receipt.get("timestamp", ""),
            metadata={
                "file_path": anchor_receipt.get("file_path"),
                "prev_chain_hash": anchor_receipt.get("prev_chain_hash"),
                "origin": "governed_chain_verification",
            },
        )

        ext_receipt = external_anchor.anchor_externally(ext_req)
        if ext_receipt is not None:
            ext_anchor_path.write_text(json.dumps(ext_receipt.to_dict(), indent=2), encoding="utf-8")
    except Exception as e:
        ext_anchor_path.write_text(json.dumps({"error": str(e)}, indent=2), encoding="utf-8")

    # --- 4) Automation dispatch: execute VERIFY_CHAIN_NOW logic ---
    automation.dispatch_from_commit(commit_path)

    # --- 5) Load the latest verification report for this session ---
    verify_path = CHAIN_VERIFY_DIR / f"verify_{session_id}.json"
    verification: Optional[Dict[str, Any]] = None
    if verify_path.exists():
        verification = json.loads(verify_path.read_text(encoding="utf-8"))

    # Compact UI-friendly summary
    summary = {
        "session_id": session_id,
        "commit_id": commit_id,
        "commit_path": str(commit_path),
        "anchor_path": str(anchor_path),
        "verification_path": str(verify_path) if verify_path.exists() else None,
        "verification_status": verification.get("valid", "UNKNOWN") if verification else "UNKNOWN",
        "verification_summary": {
            "total_anchors": verification.get("total_anchors"),
            "verified_anchors": verification.get("verified_anchors"),
            "errors": len(verification.get("errors", [])) if verification else None,
        } if verification else None,
    }

    return summary
