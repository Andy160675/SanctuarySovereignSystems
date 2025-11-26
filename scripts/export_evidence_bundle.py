#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Evidence Bundle Exporter - Sealed evidence packet generator

Creates tamper-evident ZIP bundles containing:
- Session snapshot
- Governance decision
- Anchor receipt
- Automation log slice
- Bundle manifest with verification hashes

Usage:
    python scripts/export_evidence_bundle.py --session SESSION_ID
    python scripts/export_evidence_bundle.py --session SESSION_ID --output ./bundles/
    python scripts/export_evidence_bundle.py --all --output ./bundles/
"""

import sys
import json
import zipfile
import hashlib
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.boardroom.anchoring import load_chain, sha256_hex


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DATA_ROOT = Path("DATA")
SNAPSHOTS_DIR = DATA_ROOT / "_work" / "snapshots"
COMMITS_DIR = DATA_ROOT / "_commits"
AUDIT_FILE = DATA_ROOT / "_work" / "audit.json"
AUTOMATION_LOG = DATA_ROOT / "_automation_log.json"
CHAIN_FILE = DATA_ROOT / "_anchor_chain.json"

DEFAULT_OUTPUT_DIR = Path("exports")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def iso_now() -> str:
    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


def sha256_file(file_path: Path) -> str:
    """Compute SHA-256 hash of file."""
    return sha256_hex(file_path.read_bytes())


def load_json_file(file_path: Path) -> Optional[Dict[str, Any]]:
    """Load JSON file, return None if not found."""
    if not file_path.exists():
        return None
    try:
        return json.loads(file_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, IOError):
        return None


def find_session_files(session_id: str) -> Dict[str, Optional[Path]]:
    """Find all files related to a session."""
    files: Dict[str, Optional[Path]] = {
        "snapshot": None,
        "commit": None,
        "anchor": None,
    }

    # Find snapshot
    for snapshot_file in SNAPSHOTS_DIR.glob("*.json"):
        if session_id in snapshot_file.name:
            files["snapshot"] = snapshot_file
            break

    # Find commit
    for commit_file in COMMITS_DIR.glob("decision_*.json"):
        if session_id in commit_file.name:
            files["commit"] = commit_file
            files["anchor"] = commit_file.with_suffix(".anchor.json")
            break

    return files


def get_automation_slice(session_id: str) -> List[Dict[str, Any]]:
    """Get automation log entries for a session."""
    if not AUTOMATION_LOG.exists():
        return []

    log = load_json_file(AUTOMATION_LOG) or []
    return [entry for entry in log if entry.get("session_id") == session_id]


def list_sessions() -> List[str]:
    """List all available session IDs."""
    sessions = set()

    # From snapshots
    for f in SNAPSHOTS_DIR.glob("*.json"):
        # Extract session ID from filename
        sessions.add(f.stem)

    # From commits
    for f in COMMITS_DIR.glob("decision_*.json"):
        # decision_<session_id>.json
        session_id = f.stem.replace("decision_", "")
        sessions.add(session_id)

    return sorted(sessions)


# ---------------------------------------------------------------------------
# Bundle Creation
# ---------------------------------------------------------------------------

def create_evidence_bundle(
    session_id: str,
    output_dir: Path,
    verbose: bool = False
) -> Optional[Path]:
    """
    Create a sealed evidence bundle for a session.

    Returns:
        Path to the created ZIP file, or None if session not found
    """
    files = find_session_files(session_id)

    # Check if we have any files
    if all(v is None for v in files.values()):
        print(f"❌ No files found for session: {session_id}")
        return None

    output_dir.mkdir(parents=True, exist_ok=True)

    bundle_name = f"evidence_bundle_{session_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.zip"
    bundle_path = output_dir / bundle_name

    # Build manifest
    manifest: Dict[str, Any] = {
        "bundle_id": f"bundle-{session_id}",
        "session_id": session_id,
        "created_at": iso_now(),
        "files": {},
        "integrity": {},
    }

    with zipfile.ZipFile(bundle_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        # Add snapshot
        if files["snapshot"] and files["snapshot"].exists():
            arcname = f"snapshot/{files['snapshot'].name}"
            zf.write(files["snapshot"], arcname)
            manifest["files"]["snapshot"] = arcname
            manifest["integrity"]["snapshot_sha256"] = sha256_file(files["snapshot"])
            if verbose:
                print(f"  + Added: {arcname}")

        # Add commit
        if files["commit"] and files["commit"].exists():
            arcname = f"governance/{files['commit'].name}"
            zf.write(files["commit"], arcname)
            manifest["files"]["commit"] = arcname
            manifest["integrity"]["commit_sha256"] = sha256_file(files["commit"])
            if verbose:
                print(f"  + Added: {arcname}")

        # Add anchor receipt
        if files["anchor"] and files["anchor"].exists():
            arcname = f"governance/{files['anchor'].name}"
            zf.write(files["anchor"], arcname)
            manifest["files"]["anchor"] = arcname
            manifest["integrity"]["anchor_sha256"] = sha256_file(files["anchor"])
            if verbose:
                print(f"  + Added: {arcname}")

        # Add automation slice
        automation_slice = get_automation_slice(session_id)
        if automation_slice:
            slice_json = json.dumps(automation_slice, indent=2)
            arcname = f"automation/automation_slice_{session_id}.json"
            zf.writestr(arcname, slice_json)
            manifest["files"]["automation_slice"] = arcname
            manifest["integrity"]["automation_sha256"] = sha256_hex(slice_json.encode("utf-8"))
            if verbose:
                print(f"  + Added: {arcname}")

        # Add chain excerpt (anchors for this session)
        chain = load_chain()
        session_anchors = [
            a for a in chain
            if session_id in str(a.get("file_path", ""))
        ]
        if session_anchors:
            chain_json = json.dumps(session_anchors, indent=2)
            arcname = f"chain/chain_excerpt_{session_id}.json"
            zf.writestr(arcname, chain_json)
            manifest["files"]["chain_excerpt"] = arcname
            manifest["integrity"]["chain_excerpt_sha256"] = sha256_hex(chain_json.encode("utf-8"))
            if verbose:
                print(f"  + Added: {arcname}")

        # Compute bundle hash (before adding manifest)
        bundle_content_hash = sha256_hex(
            json.dumps(manifest["integrity"], sort_keys=True).encode("utf-8")
        )
        manifest["bundle_content_hash"] = bundle_content_hash

        # Add manifest
        manifest_json = json.dumps(manifest, indent=2)
        zf.writestr("MANIFEST.json", manifest_json)
        if verbose:
            print(f"  + Added: MANIFEST.json")

    return bundle_path


def export_all_sessions(output_dir: Path, verbose: bool = False) -> List[Path]:
    """Export bundles for all sessions."""
    sessions = list_sessions()
    bundles = []

    for session_id in sessions:
        if verbose:
            print(f"\nExporting session: {session_id}")
        bundle = create_evidence_bundle(session_id, output_dir, verbose)
        if bundle:
            bundles.append(bundle)

    return bundles


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Export sealed evidence bundles"
    )
    parser.add_argument(
        "--session", "-s",
        help="Session ID to export"
    )
    parser.add_argument(
        "--all", "-a",
        action="store_true",
        help="Export all sessions"
    )
    parser.add_argument(
        "--output", "-o",
        default=str(DEFAULT_OUTPUT_DIR),
        help=f"Output directory (default: {DEFAULT_OUTPUT_DIR})"
    )
    parser.add_argument(
        "--list", "-l",
        action="store_true",
        help="List available sessions"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output"
    )

    args = parser.parse_args()
    output_dir = Path(args.output)

    # List sessions
    if args.list:
        sessions = list_sessions()
        if sessions:
            print("Available sessions:")
            for s in sessions:
                print(f"  - {s}")
        else:
            print("No sessions found.")
        return

    # Export all
    if args.all:
        print("=" * 60)
        print("  EVIDENCE BUNDLE EXPORTER - All Sessions")
        print("=" * 60)
        bundles = export_all_sessions(output_dir, args.verbose)
        print()
        print(f"Exported {len(bundles)} bundle(s) to {output_dir}")
        for b in bundles:
            print(f"  - {b.name}")
        return

    # Export single session
    if args.session:
        print("=" * 60)
        print(f"  EVIDENCE BUNDLE EXPORTER - Session: {args.session}")
        print("=" * 60)
        bundle = create_evidence_bundle(args.session, output_dir, args.verbose)
        if bundle:
            print()
            print(f"✅ Bundle created: {bundle}")
            print(f"   Size: {bundle.stat().st_size:,} bytes")
        else:
            print("❌ Failed to create bundle")
            sys.exit(1)
        return

    # No action specified
    parser.print_help()


if __name__ == "__main__":
    main()
