#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Chain Integrity Verifier - Offline admin tool

Verifies the sovereign hash chain for:
- File integrity (payload hashes)
- Chain continuity (prev_hash linkage)
- Tamper detection

Usage:
    python scripts/verify_chain.py
    python scripts/verify_chain.py --verbose
    python scripts/verify_chain.py --json
"""

import sys
import json
import argparse
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.boardroom.anchoring import (
    load_chain,
    verify_chain_integrity,
    get_chain_summary,
    CHAIN_FILE,
)


def print_banner():
    """Print verification banner."""
    print("=" * 70)
    print("  SOVEREIGN CHAIN INTEGRITY VERIFIER")
    print("  Cryptographic Audit Trail Verification")
    print("=" * 70)
    print()


def print_summary(summary: dict):
    """Print chain summary."""
    print("CHAIN SUMMARY")
    print("-" * 40)
    print(f"  Total Anchors:     {summary['total_anchors']}")
    print(f"  Head Hash:         {summary['head_hash'][:32] if summary['head_hash'] else 'N/A'}...")
    print(f"  Genesis:           {summary['genesis_timestamp'] or 'N/A'}")
    print(f"  Latest:            {summary['latest_timestamp'] or 'N/A'}")
    print()
    if summary['record_types']:
        print("  Record Types:")
        for rt, count in summary['record_types'].items():
            print(f"    - {rt}: {count}")
    print()


def print_verification_result(result: dict, verbose: bool = False):
    """Print verification results."""
    print("VERIFICATION RESULT")
    print("-" * 40)

    status = "✅ VALID" if result['valid'] else "❌ INVALID"
    print(f"  Status:            {status}")
    print(f"  Total Anchors:     {result['total_anchors']}")
    print(f"  Verified:          {result['verified_anchors']}")

    if result['broken_at'] is not None:
        print(f"  Broken at Index:   {result['broken_at']}")

    print()

    if result['errors']:
        print("ERRORS DETECTED:")
        for error in result['errors'][:10]:  # Limit to first 10
            print(f"  ⚠️  {error}")
        if len(result['errors']) > 10:
            print(f"  ... and {len(result['errors']) - 10} more errors")
        print()

    if verbose and result['details']:
        print("DETAILED VERIFICATION:")
        print("-" * 40)
        for detail in result['details']:
            status_icon = "✅" if detail['valid'] else "❌"
            print(f"  [{detail['index']:04d}] {status_icon} {detail['record_type']}")
            print(f"         File: {detail['file_path']}")
            if detail['errors']:
                for err in detail['errors']:
                    print(f"         Error: {err}")
        print()


def output_json(summary: dict, result: dict):
    """Output results as JSON."""
    output = {
        "verified_at": datetime.utcnow().isoformat() + "Z",
        "chain_file": str(CHAIN_FILE),
        "summary": summary,
        "verification": result,
    }
    print(json.dumps(output, indent=2))


def main():
    parser = argparse.ArgumentParser(
        description="Verify sovereign chain integrity"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show detailed per-anchor verification"
    )
    parser.add_argument(
        "--json", "-j",
        action="store_true",
        help="Output results as JSON"
    )
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Only show pass/fail status"
    )

    args = parser.parse_args()

    # Check if chain file exists
    if not CHAIN_FILE.exists():
        if args.json:
            print(json.dumps({"error": "Chain file not found", "valid": None}))
        else:
            print(f"❌ Chain file not found: {CHAIN_FILE}")
        sys.exit(1)

    # Load and verify
    summary = get_chain_summary()
    result = verify_chain_integrity()

    if args.json:
        output_json(summary, result)
    elif args.quiet:
        if result['valid']:
            print("PASS")
        else:
            print("FAIL")
    else:
        print_banner()
        print_summary(summary)
        print_verification_result(result, verbose=args.verbose)

        # Final verdict
        print("=" * 70)
        if result['valid']:
            print("  VERDICT: ✅ CHAIN INTEGRITY VERIFIED")
            print("  All anchors are valid and chain continuity is intact.")
        else:
            print("  VERDICT: ❌ CHAIN INTEGRITY COMPROMISED")
            print("  Review errors above and investigate tampering.")
        print("=" * 70)

    # Exit code
    sys.exit(0 if result['valid'] else 1)


if __name__ == "__main__":
    main()
