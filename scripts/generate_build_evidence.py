from __future__ import annotations

import argparse
import subprocess
from pathlib import Path
import sys
import os

# Add project root to sys.path
sys.path.append(os.getcwd())

from src.core.evidence.api import get_global_evidence_chain


def _run(cmd: list[str]) -> str:
    try:
        out = subprocess.check_output(cmd, stderr=subprocess.STDOUT, text=True).strip()
        return out
    except Exception:
        return "unknown"


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate build evidence entry.")
    parser.add_argument("--bolt-on-version", required=True, help="e.g. governance-core/v1.0")
    parser.add_argument("--storage", default="audit/evidence/chain.jsonl")
    args = parser.parse_args()

    commit = _run(["git", "rev-parse", "HEAD"])
    branch = _run(["git", "rev-parse", "--abbrev-ref", "HEAD"])
    status = _run(["git", "status", "--porcelain"])

    content = {
        "event": "build_validation",
        "commit": commit,
        "branch": branch,
        "working_tree_clean": status == "",
    }

    chain = get_global_evidence_chain(Path(args.storage))
    rec = chain.append(
        event_type="build_validation",
        content=content,
        bolt_on_version=args.bolt_on_version,
    )

    print(f"Evidence appended: {rec.id}")
    print(f"Chain tip: {chain.tip}")
    print(f"Chain valid: {chain.verify_chain()}")


if __name__ == "__main__":
    main()
