"""
core/transport/certificate_generator.py

Head certificate generator for the Pentad Connection Layer.
- Generates per-head key, CSR (with role-based DN/subjectAltName), and certificate signed by the head's Intermediate CA
- Produces a PEM bundle (leaf + intermediate + root)
- Emits minimal evidence metadata alongside artifacts

Paths are configurable via env vars for portability across Windows/Linux:
- PENTAD_PKI_DIR (default: evidence_store/pki in repo)
- OPENSSL_PATH (optional absolute path to openssl executable)
"""
from __future__ import annotations

import json
import os
import subprocess
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict


def _env_path(name: str, default: str) -> Path:
    p = os.getenv(name)
    return Path(p) if p else Path(default)


def _openssl() -> str:
    return os.getenv("OPENSSL_PATH", r"C:\\Program Files\\Git\\usr\\bin\\openssl.exe")


@dataclass
class HeadCertResult:
    head_id: str
    role: str
    private_key: str
    certificate: str
    bundle: str
    valid_from: str
    valid_until: str
    evidence: Dict


class HeadCertificateGenerator:
    """Generates certificates for Pentad heads with role-based constraints."""

    def __init__(self, head_id: str, role: str, ip_address: str, pki_dir: Path | None = None):
        self.head_id = head_id
        self.role = role
        self.ip_address = ip_address
        self.pki_dir = pki_dir or _env_path("PENTAD_PKI_DIR", "evidence_store/pki")
        self.pki_dir.mkdir(parents=True, exist_ok=True)

    def generate_certificate(self) -> HeadCertResult:
        """Generate a complete certificate package for a head."""
        openssl = _openssl()

        private_key_path = self.pki_dir / f"{self.head_id}.key"
        csr_path = self.pki_dir / f"{self.head_id}.csr"
        cert_path = self.pki_dir / f"{self.head_id}.crt"
        bundle_path = self.pki_dir / f"{self.head_id}.pem"

        # 1) key
        if not private_key_path.exists():
            subprocess.run([openssl, "genrsa", "-out", str(private_key_path), "2048"], check=True)

        # 2) CSR with role-based config
        csr_conf = self.pki_dir / f"{self.head_id}.csr.conf"
        csr_conf.write_text(self._generate_csr_config(), encoding="utf-8")
        subprocess.run([
            openssl, "req", "-new",
            "-key", str(private_key_path),
            "-out", str(csr_path),
            "-config", str(csr_conf)
        ], check=True)

        # 3) Sign with intermediate CA for this head
        ext_conf = self.pki_dir / f"{self.head_id}.ext.conf"
        ext_conf.write_text(self._generate_extensions_config(), encoding="utf-8")

        head_ca_crt = self.pki_dir / f"{self.head_id}-ca.crt"
        head_ca_key = self.pki_dir / f"{self.head_id}-ca.key"
        root_ca_crt = self.pki_dir / "root-ca.crt"
        if not head_ca_crt.exists() or not head_ca_key.exists() or not root_ca_crt.exists():
            raise FileNotFoundError("Intermediate CA or Root CA not found. Run Initialize-PentadCA.ps1 first.")

        subprocess.run([
            openssl, "x509", "-req", "-days", "365",
            "-in", str(csr_path),
            "-CA", str(head_ca_crt),
            "-CAkey", str(head_ca_key),
            "-CAcreateserial",
            "-out", str(cert_path),
            "-extfile", str(ext_conf)
        ], check=True)

        # 4) Bundle leaf + intermediate + root
        with open(bundle_path, "w", encoding="utf-8") as out:
            out.write(Path(cert_path).read_text(encoding="utf-8"))
            out.write(Path(head_ca_crt).read_text(encoding="utf-8"))
            out.write(Path(root_ca_crt).read_text(encoding="utf-8"))

        # 5) Evidence metadata
        now = datetime.utcnow()
        evidence = {
            "timestamp": now.isoformat(),
            "head_id": self.head_id,
            "role": self.role,
            "artifacts": {
                "key": str(private_key_path),
                "csr": str(csr_path),
                "cert": str(cert_path),
                "bundle": str(bundle_path),
            }
        }
        (self.pki_dir / f"{self.head_id}.evidence.json").write_text(json.dumps(evidence, indent=2), encoding="utf-8")

        return HeadCertResult(
            head_id=self.head_id,
            role=self.role,
            private_key=str(private_key_path),
            certificate=str(cert_path),
            bundle=str(bundle_path),
            valid_from=now.isoformat(),
            valid_until=(now + timedelta(days=365)).isoformat(),
            evidence=evidence,
        )

    def _generate_csr_config(self) -> str:
        role_mapping = {
            "constitutional": "Sovereign Legislature",
            "orchestration": "Sovereign Executive",
            "verification": "Sovereign Judiciary",
            "analytics": "Sovereign Intelligence",
            "safety": "Sovereign Security",
        }
        title = role_mapping.get(self.role, self.role)
        return f"""
[ req ]
default_bits = 2048
prompt = no
default_md = sha256
distinguished_name = dn
req_extensions = req_ext

[ dn ]
C = SO
O = Sovereign Systems
OU = Pentad
CN = {self.head_id}.pentad.internal
title = {title}

[ req_ext ]
subjectAltName = @alt_names
keyUsage = digitalSignature, keyEncipherment
extendedKeyUsage = serverAuth, clientAuth

[ alt_names ]
DNS.1 = {self.head_id}
DNS.2 = {self.head_id}.pentad.internal
IP.1 = {self.ip_address}
"""

    def _generate_extensions_config(self) -> str:
        role_constraints = {
            "constitutional": {
                "key_usage": "digitalSignature, keyEncipherment",
                "extended_key_usage": "serverAuth, clientAuth, codeSigning",
            },
            "safety": {
                "key_usage": "digitalSignature, keyEncipherment",
                "extended_key_usage": "serverAuth, clientAuth",
            },
        }
        c = role_constraints.get(self.role, role_constraints["constitutional"]) 
        return f"""
authorityKeyIdentifier=keyid,issuer
basicConstraints=CA:FALSE
keyUsage = critical, {c['key_usage']}
extendedKeyUsage = {c['extended_key_usage']}
subjectAltName = @alt_names

[ alt_names ]
DNS.1 = {self.head_id}
DNS.2 = {self.head_id}.pentad.internal
IP.1 = {self.ip_address}
"""
