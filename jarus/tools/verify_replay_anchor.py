#!/usr/bin/env python3
"""
Ed25519 Replay Anchor Verification Tool
========================================

Verifies signed replay anchors from the Watcher agent.
Each anchor contains:
- Mission ID
- Merkle root of the ledger at snapshot time
- Timestamp
- Ed25519 signature

Usage:
    python verify_replay_anchor.py <anchor_file.json>
    python verify_replay_anchor.py --batch <directory>
    python verify_replay_anchor.py --generate-keypair

This tool is read-only and does not modify any state.
"""

import argparse
import base64
import hashlib
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple, Dict, Any

try:
    from cryptography.hazmat.primitives.asymmetric.ed25519 import (
        Ed25519PrivateKey,
        Ed25519PublicKey,
    )
    from cryptography.hazmat.primitives import serialization
    from cryptography.exceptions import InvalidSignature
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False
    print("Warning: cryptography library not installed. Install with: pip install cryptography")


# Default paths
KEYS_DIR = Path(__file__).parent.parent / "keys"
PUBLIC_KEY_PATH = KEYS_DIR / "watcher_public.pem"
PRIVATE_KEY_PATH = KEYS_DIR / "watcher_private.pem"


def generate_keypair(output_dir: Optional[Path] = None) -> Tuple[Path, Path]:
    """Generate a new Ed25519 keypair for signing replay anchors."""
    if not CRYPTO_AVAILABLE:
        raise RuntimeError("cryptography library required for key generation")

    output_dir = output_dir or KEYS_DIR
    output_dir.mkdir(parents=True, exist_ok=True)

    # Generate private key
    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key()

    # Serialize private key
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )

    # Serialize public key
    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )

    private_path = output_dir / "watcher_private.pem"
    public_path = output_dir / "watcher_public.pem"

    private_path.write_bytes(private_pem)
    public_path.write_bytes(public_pem)

    # Secure the private key
    os.chmod(private_path, 0o600)

    print(f"Generated keypair:")
    print(f"  Private key: {private_path}")
    print(f"  Public key:  {public_path}")
    print(f"\nKeep the private key secure. Share only the public key.")

    return private_path, public_path


def load_public_key(path: Optional[Path] = None) -> "Ed25519PublicKey":
    """Load Ed25519 public key from PEM file."""
    if not CRYPTO_AVAILABLE:
        raise RuntimeError("cryptography library required")

    path = path or PUBLIC_KEY_PATH
    if not path.exists():
        raise FileNotFoundError(f"Public key not found: {path}")

    key_bytes = path.read_bytes()
    return serialization.load_pem_public_key(key_bytes)


def load_private_key(path: Optional[Path] = None) -> "Ed25519PrivateKey":
    """Load Ed25519 private key from PEM file."""
    if not CRYPTO_AVAILABLE:
        raise RuntimeError("cryptography library required")

    path = path or PRIVATE_KEY_PATH
    if not path.exists():
        raise FileNotFoundError(f"Private key not found: {path}")

    key_bytes = path.read_bytes()
    return serialization.load_pem_private_key(key_bytes, password=None)


def compute_anchor_digest(anchor: Dict[str, Any]) -> bytes:
    """
    Compute the canonical digest for an anchor.
    The digest is computed over the deterministic JSON representation
    of the anchor data (excluding the signature itself).
    """
    # Extract signable fields in canonical order
    signable = {
        "mission_id": anchor.get("mission_id"),
        "merkle_root": anchor.get("merkle_root"),
        "timestamp": anchor.get("timestamp"),
        "event_count": anchor.get("event_count"),
        "ledger_hash": anchor.get("ledger_hash"),
    }

    # Remove None values
    signable = {k: v for k, v in signable.items() if v is not None}

    # Canonical JSON (sorted keys, no spaces)
    canonical = json.dumps(signable, sort_keys=True, separators=(",", ":"))

    # SHA-256 digest
    return hashlib.sha256(canonical.encode("utf-8")).digest()


def sign_anchor(anchor: Dict[str, Any], private_key: "Ed25519PrivateKey") -> str:
    """Sign an anchor and return base64-encoded signature."""
    digest = compute_anchor_digest(anchor)
    signature = private_key.sign(digest)
    return base64.b64encode(signature).decode("ascii")


def verify_anchor(anchor: Dict[str, Any], public_key: "Ed25519PublicKey") -> bool:
    """
    Verify an anchor's signature.
    Returns True if valid, False otherwise.
    """
    signature_b64 = anchor.get("signature")
    if not signature_b64:
        return False

    try:
        signature = base64.b64decode(signature_b64)
        digest = compute_anchor_digest(anchor)
        public_key.verify(signature, digest)
        return True
    except (InvalidSignature, Exception):
        return False


def verify_anchor_file(
    anchor_path: Path,
    public_key_path: Optional[Path] = None,
    verbose: bool = True
) -> Dict[str, Any]:
    """
    Verify a single anchor file.
    Returns a verification result dict.
    """
    result = {
        "file": str(anchor_path),
        "valid": False,
        "error": None,
        "anchor": None,
    }

    # Load anchor
    try:
        anchor = json.loads(anchor_path.read_text())
        result["anchor"] = {
            "mission_id": anchor.get("mission_id"),
            "merkle_root": anchor.get("merkle_root"),
            "timestamp": anchor.get("timestamp"),
            "event_count": anchor.get("event_count"),
        }
    except json.JSONDecodeError as e:
        result["error"] = f"Invalid JSON: {e}"
        return result
    except Exception as e:
        result["error"] = f"Failed to read file: {e}"
        return result

    # Check required fields
    required = ["mission_id", "merkle_root", "timestamp", "signature"]
    missing = [f for f in required if f not in anchor]
    if missing:
        result["error"] = f"Missing required fields: {missing}"
        return result

    # Load public key and verify
    try:
        public_key = load_public_key(public_key_path)
        result["valid"] = verify_anchor(anchor, public_key)
        if not result["valid"]:
            result["error"] = "Signature verification failed"
    except FileNotFoundError as e:
        result["error"] = str(e)
    except Exception as e:
        result["error"] = f"Verification error: {e}"

    if verbose:
        status = "[VALID]" if result["valid"] else "[INVALID]"
        print(f"{status}: {anchor_path.name}")
        if result["anchor"]:
            print(f"   Mission: {result['anchor']['mission_id']}")
            print(f"   Merkle:  {result['anchor']['merkle_root'][:16]}...")
            print(f"   Time:    {result['anchor']['timestamp']}")
        if result["error"]:
            print(f"   Error:   {result['error']}")
        print()

    return result


def verify_batch(
    directory: Path,
    public_key_path: Optional[Path] = None,
    pattern: str = "*.json"
) -> Dict[str, Any]:
    """
    Verify all anchor files in a directory.
    Returns summary statistics.
    """
    anchor_files = list(directory.glob(pattern))

    if not anchor_files:
        print(f"No anchor files found in {directory}")
        return {"total": 0, "valid": 0, "invalid": 0, "errors": []}

    print(f"Verifying {len(anchor_files)} anchor files...\n")

    results = []
    for anchor_path in sorted(anchor_files):
        result = verify_anchor_file(anchor_path, public_key_path, verbose=True)
        results.append(result)

    valid_count = sum(1 for r in results if r["valid"])
    invalid_count = len(results) - valid_count
    errors = [r for r in results if r["error"]]

    print("=" * 50)
    print(f"SUMMARY: {valid_count}/{len(results)} valid")
    if invalid_count > 0:
        print(f"WARNING: {invalid_count} invalid anchors detected")

    return {
        "total": len(results),
        "valid": valid_count,
        "invalid": invalid_count,
        "errors": errors,
        "results": results,
    }


def create_anchor(
    mission_id: str,
    merkle_root: str,
    event_count: int,
    ledger_hash: Optional[str] = None,
    sign: bool = True,
    private_key_path: Optional[Path] = None,
) -> Dict[str, Any]:
    """
    Create a new replay anchor, optionally signed.
    """
    anchor = {
        "mission_id": mission_id,
        "merkle_root": merkle_root,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "event_count": event_count,
        "version": "1.0",
    }

    if ledger_hash:
        anchor["ledger_hash"] = ledger_hash

    if sign:
        private_key = load_private_key(private_key_path)
        anchor["signature"] = sign_anchor(anchor, private_key)

    return anchor


def main():
    parser = argparse.ArgumentParser(
        description="Verify Ed25519 signed replay anchors from the Watcher agent"
    )

    parser.add_argument(
        "anchor_file",
        nargs="?",
        help="Path to anchor JSON file to verify"
    )

    parser.add_argument(
        "--batch",
        metavar="DIR",
        help="Verify all anchor files in directory"
    )

    parser.add_argument(
        "--public-key",
        metavar="PATH",
        help="Path to public key PEM file"
    )

    parser.add_argument(
        "--generate-keypair",
        action="store_true",
        help="Generate a new Ed25519 keypair"
    )

    parser.add_argument(
        "--output-dir",
        metavar="DIR",
        help="Output directory for generated keypair"
    )

    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON"
    )

    args = parser.parse_args()

    if not CRYPTO_AVAILABLE:
        print("Error: cryptography library is required")
        print("Install with: pip install cryptography")
        sys.exit(1)

    # Generate keypair
    if args.generate_keypair:
        output_dir = Path(args.output_dir) if args.output_dir else None
        generate_keypair(output_dir)
        sys.exit(0)

    # Batch verification
    if args.batch:
        directory = Path(args.batch)
        if not directory.is_dir():
            print(f"Error: {args.batch} is not a directory")
            sys.exit(1)

        public_key_path = Path(args.public_key) if args.public_key else None
        result = verify_batch(directory, public_key_path)

        if args.json:
            print(json.dumps(result, indent=2))

        sys.exit(0 if result["invalid"] == 0 else 1)

    # Single file verification
    if args.anchor_file:
        anchor_path = Path(args.anchor_file)
        if not anchor_path.exists():
            print(f"Error: {args.anchor_file} not found")
            sys.exit(1)

        public_key_path = Path(args.public_key) if args.public_key else None
        result = verify_anchor_file(anchor_path, public_key_path)

        if args.json:
            print(json.dumps(result, indent=2))

        sys.exit(0 if result["valid"] else 1)

    # No arguments - show help
    parser.print_help()
    sys.exit(0)


if __name__ == "__main__":
    main()
