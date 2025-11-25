"""
Sovereign Version Control (SVC)
================================
Embedded lineage layer for the Sovereign System.

Every Trinity run becomes a commit:
- Hashed
- Chained to parent
- Narrated by DollAgent
- Immutable

Usage:
    from svc import commit_run, get_history, get_head

    # After Trinity run
    commit = commit_run(run_result)

    # Get full history
    history = get_history()

    # Get latest commit
    head = get_head()
"""

import json
import hashlib
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional, List

# SVC root directory - use sov_vc for CLI compatibility
SVC_ROOT = Path("C:/sovereign-system/sov_vc")
COMMITS_DIR = SVC_ROOT / "commits"
HEAD_FILE = SVC_ROOT / "HEAD"


def ensure_dirs():
    """Ensure SVC directories exist."""
    COMMITS_DIR.mkdir(parents=True, exist_ok=True)


def compute_commit_hash(commit_obj: Dict[str, Any]) -> str:
    """Compute SHA-256 hash of commit object (excluding commit_hash field)."""
    # Remove commit_hash if present for hashing
    obj_copy = {k: v for k, v in commit_obj.items() if k != "commit_hash"}
    encoded = json.dumps(obj_copy, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def get_head() -> Optional[str]:
    """Get the current HEAD commit filename."""
    if HEAD_FILE.exists():
        return HEAD_FILE.read_text().strip()
    return None


def get_parent_hash() -> str:
    """Get the hash of the parent commit (or GENESIS if first)."""
    head = get_head()
    if not head:
        return "GENESIS"

    commit_file = COMMITS_DIR / head
    if commit_file.exists():
        commit = json.loads(commit_file.read_text())
        return commit.get("commit_hash", "GENESIS")
    return "GENESIS"


def commit_run(
    run_id: str,
    case_id: str,
    query: str,
    evidence_count: int,
    mismatch_count: int,
    integrity_status: str,
    action_taken: str,
    risk_lens: str,
    llm_analysis: Optional[Dict[str, Any]] = None,
    pipeline_duration_ms: int = 0,
    extra_metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Create a new SVC commit from a Trinity run.

    Returns the commit object with hash.
    """
    ensure_dirs()

    timestamp = datetime.now(timezone.utc).isoformat()
    parent_hash = get_parent_hash()

    commit_obj = {
        "commit_id": str(uuid.uuid4()),
        "parent_commit": parent_hash,
        "timestamp": timestamp,
        "run_id": run_id,
        "case_id": case_id,
        "query": query,
        "evidence_count": evidence_count,
        "mismatch_count": mismatch_count,
        "integrity_status": integrity_status,
        "action_taken": action_taken,
        "risk_lens": risk_lens,
        "llm_analysis": llm_analysis or {},
        "pipeline_duration_ms": pipeline_duration_ms,
        "metadata": extra_metadata or {}
    }

    # Compute and add hash
    commit_hash = compute_commit_hash(commit_obj)
    commit_obj["commit_hash"] = commit_hash

    # Generate filename from timestamp
    safe_ts = timestamp.replace(":", "-").replace("+", "_")
    filename = f"{safe_ts}.json"

    # Write commit
    commit_file = COMMITS_DIR / filename
    commit_file.write_text(json.dumps(commit_obj, indent=2, default=str))

    # Update HEAD
    HEAD_FILE.write_text(filename)

    return commit_obj


def get_commit(filename: str) -> Optional[Dict[str, Any]]:
    """Load a specific commit by filename."""
    commit_file = COMMITS_DIR / filename
    if commit_file.exists():
        return json.loads(commit_file.read_text())
    return None


def get_history(limit: int = 100) -> List[Dict[str, Any]]:
    """Get commit history, newest first."""
    ensure_dirs()

    commits = []
    for file in sorted(COMMITS_DIR.glob("*.json"), reverse=True):
        if len(commits) >= limit:
            break
        try:
            commits.append(json.loads(file.read_text()))
        except json.JSONDecodeError:
            continue

    return commits


def verify_chain() -> Dict[str, Any]:
    """Verify the integrity of the commit chain."""
    commits = get_history(limit=10000)  # Get all

    if not commits:
        return {"valid": True, "commits_checked": 0, "errors": []}

    errors = []

    # Reverse to check oldest to newest
    commits = list(reversed(commits))

    for i, commit in enumerate(commits):
        # Verify hash
        stored_hash = commit.get("commit_hash")
        computed_hash = compute_commit_hash(commit)

        if stored_hash != computed_hash:
            errors.append({
                "commit_id": commit.get("commit_id"),
                "error": "hash_mismatch",
                "stored": stored_hash,
                "computed": computed_hash
            })

        # Verify parent chain (except first)
        if i > 0:
            expected_parent = commits[i - 1].get("commit_hash")
            actual_parent = commit.get("parent_commit")

            if expected_parent != actual_parent:
                errors.append({
                    "commit_id": commit.get("commit_id"),
                    "error": "parent_mismatch",
                    "expected": expected_parent,
                    "actual": actual_parent
                })

    return {
        "valid": len(errors) == 0,
        "commits_checked": len(commits),
        "errors": errors
    }


def get_stats() -> Dict[str, Any]:
    """Get SVC statistics."""
    commits = get_history(limit=10000)

    if not commits:
        return {
            "total_commits": 0,
            "first_commit": None,
            "latest_commit": None,
            "total_evidence_processed": 0,
            "total_mismatches": 0,
            "risk_distribution": {}
        }

    risk_dist = {"low": 0, "medium": 0, "high": 0, "unknown": 0}
    total_evidence = 0
    total_mismatches = 0

    for c in commits:
        risk = c.get("risk_lens", "unknown")
        risk_dist[risk] = risk_dist.get(risk, 0) + 1
        total_evidence += c.get("evidence_count", 0)
        total_mismatches += c.get("mismatch_count", 0)

    return {
        "total_commits": len(commits),
        "first_commit": commits[-1].get("timestamp") if commits else None,
        "latest_commit": commits[0].get("timestamp") if commits else None,
        "total_evidence_processed": total_evidence,
        "total_mismatches": total_mismatches,
        "risk_distribution": risk_dist,
        "chain_valid": verify_chain()["valid"]
    }
