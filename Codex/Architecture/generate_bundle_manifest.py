#!/usr/bin/env python3
"""
Generate Governance Bundle Manifest.
Computes SHA-256 hashes for all files in the governance directory.

Usage:
    python generate_bundle_manifest.py --governance ./governance --output ./governance/bundle_manifest.json
"""
import argparse
import hashlib
import json
from pathlib import Path

def compute_sha256(file_path):
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def main():
    parser = argparse.ArgumentParser(description='Generate governance bundle manifest')
    parser.add_argument('--governance', default='./governance', help='Path to governance directory')
    parser.add_argument('--output', default='./governance/bundle_manifest.json', help='Path to output manifest JSON')
    args = parser.parse_args()

    gov_path = Path(args.governance)
    manifest = {
        "files": {},
        "version": None
    }

    # Load version if exists
    version_file = gov_path / "VERSION"
    if version_file.exists():
        manifest["version"] = version_file.read_text(encoding='utf-8').strip()

    for filepath in sorted(gov_path.rglob('*')):
        if filepath.is_dir():
            continue
        # Skip the manifest itself
        if filepath.name == "bundle_manifest.json":
            continue
        
        rel_path = filepath.relative_to(gov_path).as_posix()
        manifest["files"][rel_path] = compute_sha256(filepath)

    with open(args.output, "w", encoding='utf-8') as f:
        json.dump(manifest, f, indent=2)

    print(f"Manifest generated: {args.output} ({len(manifest['files'])} files)")

if __name__ == '__main__':
    main()
