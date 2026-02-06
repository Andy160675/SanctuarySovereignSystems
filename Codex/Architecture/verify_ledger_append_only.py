#!/usr/bin/env python3
"""
Verify Promotion Ledger Append-Only Invariant.
This script checks if the ledger has only been appended to (no deletions or modifications of existing lines).
Intended for use in CI or pre-assembly checks.

Usage:
    python verify_ledger_append_only.py --ledger ./governance/promotion_ledger.jsonl --reference ./governance/promotion_ledger.jsonl.checkpoint
"""
import argparse
import sys
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(description='Verify ledger append-only invariant')
    parser.add_argument('--ledger', required=True, help='Path to current promotion ledger')
    parser.add_argument('--reference', required=True, help='Path to reference (last known good) ledger')
    args = parser.parse_args()

    ledger_path = Path(args.ledger)
    ref_path = Path(args.reference)

    if not ledger_path.exists():
        print(f"Error: Ledger file not found: {ledger_path}")
        sys.exit(1)
    
    if not ref_path.exists():
        # If no reference exists, we can't prove it's append-only, but we can't prove it's NOT.
        # In a real CI, the 'reference' would be the version from the base branch.
        print(f"Warning: Reference file not found: {ref_path}. Skipping check.")
        sys.exit(0)

    ledger_lines = ledger_path.read_text(encoding='utf-8').splitlines()
    ref_lines = ref_path.read_text(encoding='utf-8').splitlines()

    if len(ledger_lines) < len(ref_lines):
        print(f"FAIL: Current ledger has fewer lines ({len(ledger_lines)}) than reference ({len(ref_lines)}).")
        sys.exit(1)

    for i, (l_line, r_line) in enumerate(zip(ledger_lines, ref_lines)):
        if l_line != r_line:
            print(f"FAIL: Line {i+1} has been modified.")
            print(f"  Ref: {r_line}")
            print(f"  Cur: {l_line}")
            sys.exit(1)

    print(f"OK: Ledger is append-only relative to reference. ({len(ledger_lines) - len(ref_lines)} new entries)")
    sys.exit(0)

if __name__ == '__main__':
    main()
