#!/usr/bin/env python3
"""
Ledger Integrity Test
=====================
Validates that the ledger maintains hash chain integrity.
This is a Phase 0 exit test.
"""

import hashlib
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LEDGER_PATH = ROOT / "data" / "ledger.jsonl"


def main():
    if not LEDGER_PATH.exists():
        print("Ledger integrity: SKIP (no ledger file yet - OK for Phase 0 bootstrap)")
        return

    prev_hash = None
    line_num = 0

    with LEDGER_PATH.open() as f:
        for line in f:
            line_num += 1
            if not line.strip():
                continue

            try:
                entry = json.loads(line)
            except json.JSONDecodeError as e:
                print(f"Ledger integrity: FAILED (line {line_num})")
                print(f"  JSON parse error: {e}")
                sys.exit(1)

            # Verify hash
            stored_hash = entry.get("hash")
            if not stored_hash:
                print(f"Ledger integrity: FAILED (line {line_num})")
                print("  Missing hash field")
                sys.exit(1)

            # Recompute hash from entry data (excluding the hash itself)
            base = {k: v for k, v in entry.items() if k != "hash"}
            recomputed = hashlib.sha256(
                json.dumps(base, sort_keys=True).encode("utf-8")
            ).hexdigest()

            if recomputed != stored_hash:
                print(f"Ledger integrity: FAILED (line {line_num})")
                print(f"  Expected hash: {recomputed}")
                print(f"  Stored hash: {stored_hash}")
                sys.exit(1)

            # Verify chain
            if prev_hash and entry.get("prev_hash") != prev_hash:
                print(f"Ledger integrity: FAILED (line {line_num})")
                print(f"  Expected prev_hash: {prev_hash}")
                print(f"  Stored prev_hash: {entry.get('prev_hash')}")
                sys.exit(1)

            prev_hash = stored_hash

    print(f"Ledger integrity: OK ({line_num} entries verified)")


if __name__ == "__main__":
    main()
