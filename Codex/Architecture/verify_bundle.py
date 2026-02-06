#!/usr/bin/env python3
"""
Verify Governance Bundle Integrity.
Checks local governance files against a manifest.

Usage:
    python verify_bundle.py --governance ./governance --manifest ./governance/bundle_manifest.json
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

def compute_sha256(file_path):
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except Exception:
        return None

def main():
    parser = argparse.ArgumentParser(description='Verify governance bundle integrity')
    parser.add_argument('--governance', default='./governance', help='Path to governance directory')
    parser.add_argument('--manifest', default='./governance/bundle_manifest.json', help='Path to manifest JSON')
    args = parser.parse_args()

    gov_path = Path(args.governance)
    manifest_path = Path(args.manifest)

    if not manifest_path.exists():
        print(f"Error: Manifest not found at {manifest_path}")
        sys.exit(1)

    with manifest_path.open('r', encoding='utf-8') as f:
        manifest = json.load(f)

    expected_files = manifest.get("files", {})
    version = manifest.get("version", "UNKNOWN")
    print(f"Verifying Governance Bundle v{version}...")

    failures = 0
    # Check all files in manifest exist and match hash
    for rel_path, expected_hash in expected_files.items():
        full_path = gov_path / rel_path
        if not full_path.exists():
            print(f"FAIL: Missing file: {rel_path}")
            failures += 1
            continue
        
        actual_hash = compute_sha256(full_path)
        if actual_hash != expected_hash:
            print(f"FAIL: Hash mismatch for {rel_path}")
            print(f"  Expected: {expected_hash}")
            print(f"  Actual:   {actual_hash}")
            failures += 1

    # Optional: Check for extra files not in manifest
    # This might be expected (local logs/ledger entries), but we should be aware.
    local_files = set()
    for filepath in gov_path.rglob('*'):
        if filepath.is_dir():
            continue
        if filepath.name == "bundle_manifest.json":
            continue
        local_files.add(filepath.relative_to(gov_path).as_posix())

    extra_files = local_files - set(expected_files.keys())
    if extra_files:
        print(f"INFO: {len(extra_files)} local files not in manifest (e.g. local evidence/logs)")

    if failures == 0:
        print(f"OK: Governance bundle v{version} verified successfully.")
        sys.exit(0)
    else:
        print(f"FAIL: {failures} integrity issues found.")
        sys.exit(1)

if __name__ == '__main__':
    main()
