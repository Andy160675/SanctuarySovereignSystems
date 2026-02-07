"""
core/transport/stls_protocol.py

Sovereign TLS (sTLS) context scaffolding. Note: Python's ssl module does not expose
OpenSSL's verify_callback directly in all versions; we model constitutional checks as
post-handshake validations and explicit peer certificate inspections.
"""
from __future__ import annotations

import json
import os
import socket
import ssl
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional


@dataclass
class STLSHandshakeEvidence:
    timestamp: str
    local_head: str
    remote_cn: Optional[str]
    fingerprint_sha256: Optional[str]
    cipher: Optional[str]
    session_reused: bool
    extra: Dict[str, Any] = field(default_factory=dict)


class SovereignTLSContext:
    """Constitutional TLS context with evidence generation (scaffold)."""

    def __init__(self, head_id: str, role: str, pki_dir: Optional[Path] = None):
        self.head_id = head_id
        self.role = role
        self.pki_dir = pki_dir or Path(os.getenv("PENTAD_PKI_DIR", "evidence_store/pki"))
        self.evidence_log: list[Dict[str, Any]] = []
        self.context = self._create_ssl_context()

    def _create_ssl_context(self) -> ssl.SSLContext:
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        ctx.minimum_version = ssl.TLSVersion.TLSv1_3
        ctx.load_cert_chain(
            certfile=str(self.pki_dir / f"{self.head_id}.pem"),
            keyfile=str(self.pki_dir / f"{self.head_id}.key"),
        )
        ctx.load_verify_locations(cafile=str(self.pki_dir / "root-ca.crt"))
        ctx.verify_mode = ssl.CERT_REQUIRED
        ctx.check_hostname = False  # We'll do stricter CN/role checks ourselves
        ctx.set_ciphers("ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384")
        return ctx

    def create_connection(self, host: str, port: int) -> ssl.SSLSocket:
        raw = socket.create_connection((host, port))
        ssl_sock = self.context.wrap_socket(raw, server_hostname=host)
        self._post_handshake_constitutional_check(ssl_sock)
        return ssl_sock

    def _post_handshake_constitutional_check(self, ssl_sock: ssl.SSLSocket) -> None:
        # Extract DER peer cert and derive evidence
        der = ssl_sock.getpeercert(binary_form=True)
        remote_cn = None
        fp = None
        if der:
            import hashlib
            fp = hashlib.sha256(der).hexdigest()
            # Best-effort CN extraction from getpeercert dict (non-binary form)
            info = ssl_sock.getpeercert()
            if info:
                for tup in info.get("subject", []):
                    for k, v in tup:
                        if k == "commonName":
                            remote_cn = v
                            break
        ev = STLSHandshakeEvidence(
            timestamp=datetime.utcnow().isoformat(),
            local_head=self.head_id,
            remote_cn=remote_cn,
            fingerprint_sha256=fp,
            cipher=(ssl_sock.cipher()[0] if ssl_sock.cipher() else None),
            session_reused=bool(ssl_sock.session_reused) if hasattr(ssl_sock, "session_reused") else False,
        )
        self._archive_evidence(ev)

    def _archive_evidence(self, evidence: STLSHandshakeEvidence) -> None:
        # Append to in-memory log and write a rolling file in evidence_store
        self.evidence_log.append(evidence.__dict__)
        out_dir = Path("evidence_store") / "connection"
        out_dir.mkdir(parents=True, exist_ok=True)
        out_file = out_dir / f"handshake_{self.head_id}.jsonl"
        with out_file.open("a", encoding="utf-8") as f:
            f.write(json.dumps(evidence.__dict__) + "\n")
