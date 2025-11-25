#!/usr/bin/env python3
"""
sov.py - Sovereign Version Control CLI
=======================================
Git-like CLI for the Sovereign System's run history.

Commands:
    log             List commits (newest first), HEAD marked
    show <file>     Pretty print a commit JSON
    diff <a> <b>    Structural diff between two commits

Usage:
    python sov.py log
    python sov.py show 2025-01-15T10-30-00_0000.json
    python sov.py diff commit_a.json commit_b.json
"""

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# SVC store location
BASE = Path("C:/sovereign-system/sov_vc")
COMMITS_DIR = BASE / "commits"
HEAD_FILE = BASE / "HEAD"


def get_head() -> Optional[str]:
    """Get current HEAD filename."""
    if HEAD_FILE.exists():
        return HEAD_FILE.read_text().strip()
    return None


def list_commits() -> List[Path]:
    """List all commit files, sorted by filename (newest first)."""
    if not COMMITS_DIR.exists():
        return []
    return sorted(COMMITS_DIR.glob("*.json"), reverse=True)


def load_commit(filename: str) -> Optional[Dict[str, Any]]:
    """Load a commit by filename."""
    commit_file = COMMITS_DIR / filename
    if commit_file.exists():
        return json.loads(commit_file.read_text())
    return None


def cmd_log():
    """List commits with summary info."""
    commits = list_commits()
    head = get_head()

    if not commits:
        print("No commits yet.")
        return

    print(f"{'FILENAME':<40} {'CASE':<16} {'EV':>3} {'MM':>3} {'STATUS':<12} {'COMMIT':<10}")
    print("-" * 90)

    for commit_path in commits:
        filename = commit_path.name
        is_head = (filename == head)

        try:
            data = json.loads(commit_path.read_text())
            case_id = data.get("case_id", "?")[:16]
            evidence = data.get("evidence_count", 0)
            mismatches = data.get("mismatch_count", 0)
            integrity = data.get("integrity_status", "?")[:12]
            commit_hash = data.get("commit_hash", "?")[:8]

            head_marker = " <- HEAD" if is_head else ""
            print(f"{filename:<40} {case_id:<16} {evidence:>3} {mismatches:>3} {integrity:<12} {commit_hash:<10}{head_marker}")

        except Exception as e:
            print(f"{filename:<40} [error: {e}]")


def cmd_show(filename: str):
    """Pretty print a commit."""
    data = load_commit(filename)
    if data is None:
        print(f"Commit not found: {filename}")
        sys.exit(1)

    print(json.dumps(data, indent=2, default=str))


def diff_values(a: Any, b: Any, path: str = "") -> List[str]:
    """Recursively diff two values, return list of differences."""
    diffs = []

    if type(a) != type(b):
        diffs.append(f"{path}: type changed from {type(a).__name__} to {type(b).__name__}")
        return diffs

    if isinstance(a, dict):
        all_keys = set(a.keys()) | set(b.keys())
        for key in sorted(all_keys):
            child_path = f"{path}.{key}" if path else key
            if key not in a:
                diffs.append(f"{child_path}: added")
            elif key not in b:
                diffs.append(f"{child_path}: removed")
            else:
                diffs.extend(diff_values(a[key], b[key], child_path))

    elif isinstance(a, list):
        if len(a) != len(b):
            diffs.append(f"{path}: list length changed from {len(a)} to {len(b)}")
        for i in range(min(len(a), len(b))):
            diffs.extend(diff_values(a[i], b[i], f"{path}[{i}]"))

    else:
        if a != b:
            diffs.append(f"{path}: {repr(a)} -> {repr(b)}")

    return diffs


def cmd_diff(file_a: str, file_b: str):
    """Structural diff between two commits."""
    data_a = load_commit(file_a)
    data_b = load_commit(file_b)

    if data_a is None:
        print(f"Commit not found: {file_a}")
        sys.exit(1)
    if data_b is None:
        print(f"Commit not found: {file_b}")
        sys.exit(1)

    print(f"Diff: {file_a} -> {file_b}")
    print("-" * 60)

    diffs = diff_values(data_a, data_b)

    if not diffs:
        print("No differences.")
    else:
        for d in diffs:
            print(f"  {d}")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(0)

    cmd = sys.argv[1].lower()

    if cmd == "log":
        cmd_log()
    elif cmd == "show":
        if len(sys.argv) < 3:
            print("Usage: sov.py show <filename>")
            sys.exit(1)
        cmd_show(sys.argv[2])
    elif cmd == "diff":
        if len(sys.argv) < 4:
            print("Usage: sov.py diff <file_a> <file_b>")
            sys.exit(1)
        cmd_diff(sys.argv[2], sys.argv[3])
    else:
        print(f"Unknown command: {cmd}")
        print("Commands: log, show, diff")
        sys.exit(1)


if __name__ == "__main__":
    main()
