# -*- coding: utf-8 -*-
"""
Local audit anchoring + hash-chain for sovereign traceability.

This module implements the cryptographic continuity layer that binds:
- audit.json
- snapshots/*.json
- decision_*.json

into a single append-only, tamper-evident hash chain.

Guarantees:
- Temporal integrity across all governance activity
- File-level and timeline-level tamper detection
- Deterministic replay support for regulators and auditors

Principle: If it is not anchored, it is not sovereign truth.
"""

import json
import hashlib
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DATA_ROOT = Path("DATA")
CHAIN_FILE = DATA_ROOT / "_anchor_chain.json"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def iso_now() -> str:
    """UTC timestamp in ISO 8601 format."""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha256_hex(data: bytes) -> str:
    """Compute SHA-256 hash and return hex string."""
    return hashlib.sha256(data).hexdigest()


def sha256_file(file_path: Path) -> str:
    """Compute SHA-256 hash of file contents (LF-normalized for cross-platform)."""
    content = file_path.read_text(encoding="utf-8")
    # Normalize to LF line endings for consistent hashes across platforms
    content_lf = content.replace("\r\n", "\n")
    return sha256_hex(content_lf.encode("utf-8"))


# ---------------------------------------------------------------------------
# Chain Operations
# ---------------------------------------------------------------------------

def load_chain() -> List[Dict[str, Any]]:
    """Load the existing anchor chain from disk."""
    if not CHAIN_FILE.exists():
        return []
    try:
        return json.loads(CHAIN_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, IOError):
        return []


def save_chain(chain: List[Dict[str, Any]]) -> None:
    """Persist the anchor chain to disk."""
    CHAIN_FILE.parent.mkdir(parents=True, exist_ok=True)
    CHAIN_FILE.write_text(json.dumps(chain, indent=2), encoding="utf-8")


def get_chain_head() -> Optional[Dict[str, Any]]:
    """Return the most recent anchor entry, or None if chain is empty."""
    chain = load_chain()
    return chain[-1] if chain else None


def get_prev_hash() -> str:
    """Return the previous chain hash, or GENESIS if chain is empty."""
    head = get_chain_head()
    return head["chain_hash"] if head else "GENESIS"


# ---------------------------------------------------------------------------
# Anchor Operations
# ---------------------------------------------------------------------------

def append_anchor(record_type: str, file_path: Path) -> Dict[str, Any]:
    """
    Append a new anchor to the chain for the given file.

    Args:
        record_type: Type of record (e.g., "audit_snapshot", "governance_commit", "automation_log")
        file_path: Path to the file being anchored

    Returns:
        The newly created anchor record
    """
    chain = load_chain()

    # Hash the file payload (LF-normalized for cross-platform consistency)
    payload_hash = sha256_file(file_path)

    # Get previous chain hash
    prev_hash = chain[-1]["chain_hash"] if chain else "GENESIS"

    # Compute new chain hash (links to previous)
    timestamp = iso_now()
    chain_input = f"{prev_hash}|{payload_hash}|{timestamp}"
    chain_hash = sha256_hex(chain_input.encode("utf-8"))

    # Build anchor record (use forward slashes for cross-platform compatibility)
    anchor = {
        "index": len(chain),
        "timestamp": timestamp,
        "record_type": record_type,
        "file_path": str(file_path).replace("\\", "/"),
        "payload_hash": payload_hash,
        "prev_chain_hash": prev_hash,
        "chain_hash": chain_hash,
    }

    # Append and persist
    chain.append(anchor)
    save_chain(chain)

    return anchor


def anchor_file(file_path: Path, record_type: str = "generic") -> Dict[str, Any]:
    """
    Convenience wrapper for append_anchor.

    Args:
        file_path: Path to the file to anchor
        record_type: Classification of the record

    Returns:
        The anchor record
    """
    return append_anchor(record_type, file_path)


# ---------------------------------------------------------------------------
# Verification Operations
# ---------------------------------------------------------------------------

def normalize_path(path_str: str) -> Path:
    """Normalize path string to work on any OS."""
    # Replace backslashes with forward slashes for cross-platform compatibility
    normalized = path_str.replace("\\", "/")
    return Path(normalized)


def verify_anchor(anchor: Dict[str, Any]) -> Dict[str, Any]:
    """
    Verify a single anchor entry.

    Returns:
        Dict with verification results:
        - valid: bool
        - file_exists: bool
        - payload_match: bool
        - errors: List[str]
    """
    result = {
        "valid": True,
        "file_exists": False,
        "payload_match": False,
        "errors": [],
    }

    file_path = normalize_path(anchor["file_path"])

    if not file_path.exists():
        result["valid"] = False
        result["errors"].append(f"File not found: {file_path}")
        return result

    result["file_exists"] = True

    # Verify payload hash
    current_hash = sha256_file(file_path)
    if current_hash != anchor["payload_hash"]:
        result["valid"] = False
        result["payload_match"] = False
        result["errors"].append(
            f"Payload hash mismatch: expected {anchor['payload_hash'][:16]}..., got {current_hash[:16]}..."
        )
    else:
        result["payload_match"] = True

    return result


def verify_chain_integrity() -> Dict[str, Any]:
    """
    Verify the entire anchor chain for integrity.

    Returns:
        Dict with:
        - valid: bool (overall chain validity)
        - total_anchors: int
        - verified_anchors: int
        - broken_at: Optional[int] (index where chain breaks)
        - errors: List[str]
        - details: List[Dict] (per-anchor verification results)
    """
    chain = load_chain()

    result = {
        "valid": True,
        "total_anchors": len(chain),
        "verified_anchors": 0,
        "broken_at": None,
        "errors": [],
        "details": [],
    }

    if not chain:
        return result

    prev_hash = "GENESIS"

    for i, anchor in enumerate(chain):
        anchor_result = {
            "index": i,
            "record_type": anchor.get("record_type"),
            "file_path": anchor.get("file_path"),
            "valid": True,
            "errors": [],
        }

        # Check chain linkage
        if anchor.get("prev_chain_hash") != prev_hash:
            anchor_result["valid"] = False
            anchor_result["errors"].append(
                f"Chain hash mismatch: expected prev={prev_hash[:16]}..., got {anchor.get('prev_chain_hash', 'MISSING')[:16]}..."
            )
            if result["broken_at"] is None:
                result["broken_at"] = i
            result["valid"] = False

        # Verify the anchor's file
        file_verification = verify_anchor(anchor)
        if not file_verification["valid"]:
            anchor_result["valid"] = False
            anchor_result["errors"].extend(file_verification["errors"])
            if result["broken_at"] is None:
                result["broken_at"] = i
            result["valid"] = False

        # Recompute chain hash
        expected_chain_input = f"{anchor['prev_chain_hash']}|{anchor['payload_hash']}|{anchor['timestamp']}"
        expected_chain_hash = sha256_hex(expected_chain_input.encode("utf-8"))
        if expected_chain_hash != anchor.get("chain_hash"):
            anchor_result["valid"] = False
            anchor_result["errors"].append("Chain hash computation mismatch (possible tampering)")
            if result["broken_at"] is None:
                result["broken_at"] = i
            result["valid"] = False

        if anchor_result["valid"]:
            result["verified_anchors"] += 1

        result["details"].append(anchor_result)
        result["errors"].extend(anchor_result["errors"])

        # Update prev_hash for next iteration
        prev_hash = anchor.get("chain_hash", "")

    return result


def get_chain_summary() -> Dict[str, Any]:
    """
    Get a summary of the current chain state.

    Returns:
        Dict with chain statistics and head info
    """
    chain = load_chain()

    if not chain:
        return {
            "total_anchors": 0,
            "head_hash": None,
            "genesis_timestamp": None,
            "latest_timestamp": None,
            "record_types": {},
        }

    # Count record types
    record_types: Dict[str, int] = {}
    for anchor in chain:
        rt = anchor.get("record_type", "unknown")
        record_types[rt] = record_types.get(rt, 0) + 1

    return {
        "total_anchors": len(chain),
        "head_hash": chain[-1]["chain_hash"],
        "genesis_timestamp": chain[0]["timestamp"],
        "latest_timestamp": chain[-1]["timestamp"],
        "record_types": record_types,
    }
