#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generate a synthetic, non-sensitive demo DATA tree.

This creates a fake but structurally correct DATA/ directory that:
- Uses real anchoring code (so invariants pass)
- Contains no production or personal data
- Is safe for public/partner-facing snapshots

Artifacts created:
  DATA/
    _anchor_chain.json
    _automation_log.json
    _commits/
      decision_synthetic-demo-001.json
      decision_synthetic-demo-001.anchor.json
    _chain_verifications/
      verify_synthetic-demo-001.json
    _synthetic_manifest.json

Usage:
  # From repo root
  python tools/generate_synthetic_demo.py

  # Optionally clear existing DATA first
  python tools/generate_synthetic_demo.py --clear
"""

import argparse
import json
import shutil
import sys
from pathlib import Path
from datetime import datetime, timezone

# Make project root importable
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def iso_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def clear_data_dir(data_root: Path) -> None:
    """Remove existing DATA directory contents."""
    if data_root.exists():
        for item in data_root.iterdir():
            if item.is_dir():
                shutil.rmtree(item)
            else:
                item.unlink()
        print(f"[SYNTH-DEMO] Cleared existing DATA at {data_root}")


def init_empty_chain(data_root: Path) -> Path:
    """Initialize an empty anchor chain."""
    chain_file = data_root / "_anchor_chain.json"
    chain_file.write_text("[]", encoding="utf-8")
    return chain_file


def init_empty_automation_log(data_root: Path) -> Path:
    """Initialize an empty automation log."""
    log_file = data_root / "_automation_log.json"
    log_file.write_text("[]", encoding="utf-8")
    return log_file


def build_synthetic_commit(commits_dir: Path) -> Path:
    """Create a synthetic governance commit."""
    session_id = "synthetic-demo-001"
    commit_id = f"govcommit-{session_id}"

    commit = {
        "commit_id": commit_id,
        "session_id": session_id,
        "record_type": "governance_commit",
        "topic": "Synthetic demo: governed chain verification",
        "requested_by": "synthetic-generator",
        "requested_at": iso_now(),
        "governance": {
            "overall_passed": True,
            "requires_reconciliation": False,
            "consensus_action": "VERIFY_CHAIN_NOW",
            "consensus_outcome": "APPROVED",
            "rationale": "Generated for demo purposes only (no real data).",
        },
        "origin": {
            "mode": "synthetic",
            "generator": "tools/generate_synthetic_demo.py",
        },
        "snapshot_path": None,
    }

    commits_dir.mkdir(parents=True, exist_ok=True)
    commit_path = commits_dir / f"decision_{session_id}.json"
    commit_path.write_text(json.dumps(commit, indent=2), encoding="utf-8")
    return commit_path


def anchor_commit(commit_path: Path) -> Path:
    """Anchor the commit using real anchoring code."""
    from src.boardroom.anchoring import append_anchor

    receipt = append_anchor("governance_commit", commit_path)
    anchor_path = commit_path.with_suffix(".anchor.json")
    anchor_path.write_text(json.dumps(receipt, indent=2), encoding="utf-8")
    return anchor_path


def create_verify_report(data_root: Path, commit_path: Path) -> Path:
    """Create a verification report using real verification code."""
    from src.boardroom.anchoring import verify_chain_integrity

    verify_dir = data_root / "_chain_verifications"
    verify_dir.mkdir(parents=True, exist_ok=True)

    commit = json.loads(commit_path.read_text(encoding="utf-8"))
    session_id = commit["session_id"]

    # Run real verification
    report = verify_chain_integrity()
    report["governance_commit_id"] = commit["commit_id"]
    report["governance_session_id"] = session_id
    report["triggered_at"] = iso_now()
    report["triggered_by"] = "synthetic-generator"
    report["origin"] = {
        "mode": "synthetic",
        "generator": "tools/generate_synthetic_demo.py",
    }

    verify_path = verify_dir / f"verify_{session_id}.json"
    verify_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return verify_path


def write_synthetic_manifest(
    data_root: Path,
    commit_path: Path,
    anchor_path: Path,
    verify_path: Path,
    chain_path: Path,
) -> Path:
    """Write manifest documenting the synthetic demo."""
    manifest = {
        "generated_at": iso_now(),
        "mode": "synthetic_demo",
        "session_id": "synthetic-demo-001",
        "generator": "tools/generate_synthetic_demo.py",
        "artifacts": {
            "commit_path": str(commit_path.relative_to(data_root.parent)),
            "anchor_path": str(anchor_path.relative_to(data_root.parent)),
            "verify_report_path": str(verify_path.relative_to(data_root.parent)),
            "chain_path": str(chain_path.relative_to(data_root.parent)),
        },
        "notes": [
            "This DATA tree is synthetic, contains no production or personal data.",
            "Safe to include in public/partner-facing snapshots.",
            "All artifacts were created using real anchoring code.",
            "Invariant tests will pass against this tree.",
        ],
    }

    manifest_path = data_root / "_synthetic_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest_path


def main():
    parser = argparse.ArgumentParser(
        description="Generate synthetic demo DATA tree."
    )
    parser.add_argument(
        "--clear",
        action="store_true",
        help="Clear existing DATA directory before generating.",
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path("DATA"),
        help="Path to DATA directory (default: DATA).",
    )

    args = parser.parse_args()
    data_root = args.data_dir.resolve()
    commits_dir = data_root / "_commits"

    print(f"[SYNTH-DEMO] Target DATA root: {data_root}")

    # Optionally clear existing data
    if args.clear:
        clear_data_dir(data_root)

    # Ensure directories exist
    data_root.mkdir(parents=True, exist_ok=True)

    # Initialize empty chain and log
    chain_path = init_empty_chain(data_root)
    print(f"[SYNTH-DEMO] Initialized chain: {chain_path}")

    log_path = init_empty_automation_log(data_root)
    print(f"[SYNTH-DEMO] Initialized automation log: {log_path}")

    # Create synthetic commit
    commit_path = build_synthetic_commit(commits_dir)
    print(f"[SYNTH-DEMO] Created commit: {commit_path}")

    # Anchor the commit (uses real anchoring code)
    anchor_path = anchor_commit(commit_path)
    print(f"[SYNTH-DEMO] Created anchor: {anchor_path}")

    # Create verification report (uses real verification code)
    verify_path = create_verify_report(data_root, commit_path)
    print(f"[SYNTH-DEMO] Created verify report: {verify_path}")

    # Write synthetic manifest
    manifest_path = write_synthetic_manifest(
        data_root, commit_path, anchor_path, verify_path, chain_path
    )
    print(f"[SYNTH-DEMO] Created manifest: {manifest_path}")

    print()
    print("[SYNTH-DEMO] Synthetic DATA tree ready.")
    print("[SYNTH-DEMO] Run invariant tests to verify:")
    print("  pytest tests/test_governed_chain_verify.py -v")


if __name__ == "__main__":
    main()
