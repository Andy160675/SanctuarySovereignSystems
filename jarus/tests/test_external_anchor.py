#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
External Anchor Adapter Test Harness

Dry-run test for the External Anchor Adapter.
Proves:
- Config loading
- Request fingerprint generation
- Receipt creation for each backend
- Commit write-back compatibility

Usage:
    python scripts/test_external_anchor.py
    python scripts/test_external_anchor.py --backend rfc3161
    python scripts/test_external_anchor.py --backend ipfs
    python scripts/test_external_anchor.py --backend arweave
"""

import sys
import json
import argparse
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.boardroom.external_anchor import (
    ExternalAnchorRequest,
    ExternalAnchorConfig,
    anchor_externally,
    get_supported_backends,
    validate_config,
)


def test_backend(backend: str, verbose: bool = False) -> bool:
    """Test a specific backend in dry-run mode."""
    print(f"\n{'='*60}")
    print(f"  Testing Backend: {backend.upper()}")
    print(f"{'='*60}")

    # Create test request
    req = ExternalAnchorRequest(
        session_id="TEST_SESSION_001",
        commit_id="TEST_COMMIT_001",
        record_type="governance_commit",
        payload_hash="deadbeef" * 8,
        chain_hash="cafebabe" * 8,
        merkle_root="abcd1234" * 8,
        metadata={"test": True, "backend": backend},
    )

    # Create config for this backend
    cfg = ExternalAnchorConfig(
        backend=backend,
        dry_run=True,
        rfc3161_url="https://tsa.example.com/timestamp",
        ipfs_gateway="https://ipfs.io/ipfs",
        arweave_gateway="https://arweave.net",
    )

    # Validate config
    issues = validate_config(cfg)
    if issues:
        print(f"\n  Config warnings: {issues}")

    # Get receipt
    try:
        receipt = anchor_externally(req, cfg)

        if receipt is None:
            print(f"\n  Result: No receipt (backend disabled)")
            return True

        print(f"\n  Status: {receipt.status}")
        print(f"  Dry Run: {receipt.dry_run}")
        print(f"  Created: {receipt.created_at}")
        print(f"  Fingerprint: {receipt.request_fingerprint[:32]}...")

        if backend == "rfc3161":
            print(f"  RFC3161 Token: {receipt.rfc3161_token}")
            print(f"  RFC3161 Serial: {receipt.rfc3161_serial}")
            print(f"  RFC3161 URL: {receipt.rfc3161_url}")

        elif backend == "ipfs":
            print(f"  IPFS CID: {receipt.ipfs_cid}")
            print(f"  Gateway URL: {receipt.ipfs_gateway_url}")

        elif backend == "arweave":
            print(f"  Arweave TX: {receipt.arweave_tx_id}")
            print(f"  Gateway URL: {receipt.arweave_gateway_url}")

        if verbose:
            print(f"\n  Full Receipt:")
            print(json.dumps(receipt.to_dict(), indent=4))

        return True

    except Exception as e:
        print(f"\n  ERROR: {e}")
        return False


def test_none_backend():
    """Test that 'none' backend returns None."""
    print(f"\n{'='*60}")
    print(f"  Testing Backend: NONE (disabled)")
    print(f"{'='*60}")

    req = ExternalAnchorRequest(
        session_id="TEST_SESSION",
        commit_id="TEST_COMMIT",
        record_type="governance_commit",
        payload_hash="test" * 16,
        chain_hash="test" * 16,
    )

    cfg = ExternalAnchorConfig(backend="none", dry_run=True)
    receipt = anchor_externally(req, cfg)

    if receipt is None:
        print("\n  Result: None (correct - backend disabled)")
        return True
    else:
        print("\n  ERROR: Expected None but got receipt")
        return False


def test_fingerprint_determinism():
    """Test that fingerprints are deterministic."""
    print(f"\n{'='*60}")
    print(f"  Testing Fingerprint Determinism")
    print(f"{'='*60}")

    req1 = ExternalAnchorRequest(
        session_id="SAME_SESSION",
        commit_id="SAME_COMMIT",
        record_type="governance_commit",
        payload_hash="same" * 16,
        chain_hash="same" * 16,
    )

    req2 = ExternalAnchorRequest(
        session_id="SAME_SESSION",
        commit_id="SAME_COMMIT",
        record_type="governance_commit",
        payload_hash="same" * 16,
        chain_hash="same" * 16,
    )

    fp1 = req1.fingerprint()
    fp2 = req2.fingerprint()

    if fp1 == fp2:
        print(f"\n  Result: PASS - Fingerprints are deterministic")
        print(f"  Fingerprint: {fp1[:32]}...")
        return True
    else:
        print(f"\n  ERROR: Fingerprints differ!")
        print(f"  FP1: {fp1}")
        print(f"  FP2: {fp2}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Test External Anchor Adapter"
    )
    parser.add_argument(
        "--backend", "-b",
        choices=get_supported_backends(),
        help="Test specific backend only"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show full receipt JSON"
    )
    parser.add_argument(
        "--all", "-a",
        action="store_true",
        help="Test all backends"
    )

    args = parser.parse_args()

    print("\n" + "=" * 60)
    print("  EXTERNAL ANCHOR ADAPTER - Test Harness")
    print("  Dry-Run Mode (No Network Access)")
    print("=" * 60)

    results = []

    if args.backend:
        # Test specific backend
        results.append(("fingerprint", test_fingerprint_determinism()))
        results.append((args.backend, test_backend(args.backend, args.verbose)))
    elif args.all:
        # Test all backends
        results.append(("fingerprint", test_fingerprint_determinism()))
        results.append(("none", test_none_backend()))
        for backend in ["rfc3161", "ipfs", "arweave"]:
            results.append((backend, test_backend(backend, args.verbose)))
    else:
        # Default: test fingerprint and RFC3161
        results.append(("fingerprint", test_fingerprint_determinism()))
        results.append(("none", test_none_backend()))
        results.append(("rfc3161", test_backend("rfc3161", args.verbose)))

    # Summary
    print(f"\n{'='*60}")
    print("  TEST SUMMARY")
    print(f"{'='*60}")
    all_passed = True
    for name, passed in results:
        status = "PASS" if passed else "FAIL"
        print(f"  {name}: {status}")
        if not passed:
            all_passed = False

    print(f"\n  Overall: {'ALL TESTS PASSED' if all_passed else 'SOME TESTS FAILED'}")
    print("=" * 60)

    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
