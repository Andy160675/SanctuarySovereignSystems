"""
Policy Manifest Signature Validator
Fail-Closed Mode
"""
from __future__ import annotations
import hashlib
from pathlib import Path
import yaml

class SignatureError(Exception):
    pass

class PolicySignature:
    def __init__(self, manifest: str = "constitution/policy_manifest.yml", sig_file: str = "constitution/policy_manifest.sig"):
        self.manifest = Path(manifest)
        self.sig_file = Path(sig_file)

    def compute_hash(self) -> str:
        content = self.manifest.read_bytes()
        return hashlib.sha256(content).hexdigest()

    def validate_signature(self) -> None:
        if not self.sig_file.exists():
            raise SignatureError("Missing required signature file for policy manifest.")
        stored = self.sig_file.read_text(encoding="utf-8").strip()
        current = self.compute_hash().strip()
        if stored != current:
            raise SignatureError("Policy manifest hash does not match signature. Rejecting all operations.")
