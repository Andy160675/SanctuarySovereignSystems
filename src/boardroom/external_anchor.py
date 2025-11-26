# -*- coding: utf-8 -*-
"""
External Anchor Adapter

Provides a unified interface for anchoring internal sovereign truths
(payload_hash, chain_hash, merkle_root, etc.) to external, third-party
infrastructure (RFC3161 TSA, IPFS, Arweave, etc.).

This layer:
- Does NOT alter governance logic
- Does NOT alter audit or automation logic
- ONLY adds an external "witness" to already-anchored internal truth

Constitutional property added:
- Internal sovereign truth: already present
- External non-repudiation: this module

The organism can now say to the world:
"I remember what I did, I can prove I didn't rewrite it,
and a third party can confirm when that memory existed."
"""

import json
import hashlib
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Optional, Dict, Any, Literal, List
from datetime import datetime, timezone

# Type alias for supported backends
AnchorBackend = Literal["rfc3161", "ipfs", "arweave", "none"]

# Configuration file location
CONFIG_DIR = Path("CONFIG")
CONFIG_FILE = CONFIG_DIR / "external_anchor.json"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def iso_now() -> str:
    """UTC timestamp in ISO 8601 format."""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha256_hex(data: bytes) -> str:
    """Compute SHA-256 hash and return hex string."""
    return hashlib.sha256(data).hexdigest()


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

@dataclass
class ExternalAnchorConfig:
    """
    Configuration for external anchoring.

    Stored in CONFIG/external_anchor.json
    """
    backend: AnchorBackend = "none"
    dry_run: bool = True

    # RFC3161 Timestamp Authority settings
    rfc3161_url: Optional[str] = None
    rfc3161_cert_path: Optional[str] = None

    # IPFS settings
    ipfs_gateway: Optional[str] = None
    ipfs_api_url: Optional[str] = None

    # Arweave settings (future)
    arweave_gateway: Optional[str] = None
    arweave_wallet_path: Optional[str] = None

    @classmethod
    def load(cls) -> "ExternalAnchorConfig":
        """Load configuration from file, or return defaults."""
        if not CONFIG_FILE.exists():
            return cls()
        try:
            data = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
            return cls(
                backend=data.get("backend", "none"),
                dry_run=bool(data.get("dry_run", True)),
                rfc3161_url=data.get("rfc3161_url"),
                rfc3161_cert_path=data.get("rfc3161_cert_path"),
                ipfs_gateway=data.get("ipfs_gateway"),
                ipfs_api_url=data.get("ipfs_api_url"),
                arweave_gateway=data.get("arweave_gateway"),
                arweave_wallet_path=data.get("arweave_wallet_path"),
            )
        except (json.JSONDecodeError, IOError):
            return cls()

    def save(self) -> None:
        """Persist configuration to file."""
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        CONFIG_FILE.write_text(json.dumps(asdict(self), indent=2), encoding="utf-8")

    def is_enabled(self) -> bool:
        """Check if external anchoring is enabled."""
        return self.backend != "none"


# ---------------------------------------------------------------------------
# Request / Receipt Data Classes
# ---------------------------------------------------------------------------

@dataclass
class ExternalAnchorRequest:
    """
    Minimal canonical payload for external anchoring.

    Contains everything needed to prove the existence of a governance decision
    at a specific point in time.
    """
    session_id: str
    commit_id: str
    record_type: str  # e.g., "governance_commit"
    payload_hash: str
    chain_hash: str
    merkle_root: Optional[str] = None
    timestamp: str = ""
    metadata: Optional[Dict[str, Any]] = None

    def to_bytes(self) -> bytes:
        """Serialize to canonical bytes for hashing/signing."""
        body = {
            "session_id": self.session_id,
            "commit_id": self.commit_id,
            "record_type": self.record_type,
            "payload_hash": self.payload_hash,
            "chain_hash": self.chain_hash,
            "merkle_root": self.merkle_root,
            "timestamp": self.timestamp or iso_now(),
            "metadata": self.metadata or {},
        }
        return json.dumps(body, sort_keys=True).encode("utf-8")

    def fingerprint(self) -> str:
        """Compute SHA-256 fingerprint of the request."""
        return sha256_hex(self.to_bytes())


@dataclass
class ExternalAnchorReceipt:
    """
    Receipt returned from external anchoring.

    Stored in the commit's external_anchor field.
    """
    backend: AnchorBackend
    dry_run: bool
    created_at: str
    request_fingerprint: str
    status: str = "SUCCESS"
    error: Optional[str] = None

    # RFC3161 specific fields
    rfc3161_token: Optional[str] = None
    rfc3161_url: Optional[str] = None
    rfc3161_serial: Optional[str] = None

    # IPFS specific fields
    ipfs_cid: Optional[str] = None
    ipfs_gateway_url: Optional[str] = None

    # Arweave specific fields
    arweave_tx_id: Optional[str] = None
    arweave_gateway_url: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


# ---------------------------------------------------------------------------
# Backend Implementations
# ---------------------------------------------------------------------------

def _fingerprint_request(req: ExternalAnchorRequest) -> str:
    """Compute fingerprint for a request."""
    return req.fingerprint()


def anchor_via_rfc3161(
    cfg: ExternalAnchorConfig,
    req: ExternalAnchorRequest
) -> ExternalAnchorReceipt:
    """
    Anchor via RFC3161 Timestamp Authority.

    Phase 1: Dry-run implementation.
    - Does NOT call external service in dry_run mode
    - Produces a deterministic pseudo-token

    Phase 2 (future): Live implementation.
    - Will POST req.to_bytes() to cfg.rfc3161_url
    - Parse and store the returned timestamp token
    """
    fingerprint = _fingerprint_request(req)

    if cfg.dry_run:
        # Dry-run: generate deterministic pseudo-token
        token = f"DRYRUN_RFC3161_{fingerprint[:32]}"
        serial = f"DRY-{fingerprint[:16]}"

        return ExternalAnchorReceipt(
            backend="rfc3161",
            dry_run=True,
            created_at=iso_now(),
            request_fingerprint=fingerprint,
            status="SUCCESS_DRYRUN",
            rfc3161_token=token,
            rfc3161_url=cfg.rfc3161_url,
            rfc3161_serial=serial,
        )

    # Live mode (Phase 2)
    # TODO: Implement actual RFC3161 client
    # This would use libraries like rfc3161ng or direct HTTP POST
    # to a TSA endpoint

    return ExternalAnchorReceipt(
        backend="rfc3161",
        dry_run=False,
        created_at=iso_now(),
        request_fingerprint=fingerprint,
        status="NOT_IMPLEMENTED",
        error="Live RFC3161 anchoring not yet implemented",
        rfc3161_url=cfg.rfc3161_url,
    )


def anchor_via_ipfs(
    cfg: ExternalAnchorConfig,
    req: ExternalAnchorRequest
) -> ExternalAnchorReceipt:
    """
    Anchor via IPFS (content-addressed storage).

    Phase 1: Dry-run implementation.
    - Derives a pseudo-CID from the fingerprint

    Phase 2 (future): Live implementation.
    - Will POST req.to_bytes() to cfg.ipfs_api_url
    - Return the actual CID
    """
    fingerprint = _fingerprint_request(req)

    if cfg.dry_run:
        # Dry-run: generate pseudo-CID (mimics CIDv1 format)
        pseudo_cid = f"bafybeig{fingerprint[:44]}"

        gateway_url = None
        if cfg.ipfs_gateway:
            gateway_url = f"{cfg.ipfs_gateway.rstrip('/')}/{pseudo_cid}"

        return ExternalAnchorReceipt(
            backend="ipfs",
            dry_run=True,
            created_at=iso_now(),
            request_fingerprint=fingerprint,
            status="SUCCESS_DRYRUN",
            ipfs_cid=pseudo_cid,
            ipfs_gateway_url=gateway_url,
        )

    # Live mode (Phase 2)
    # TODO: Implement actual IPFS client
    # This would use ipfshttpclient or direct HTTP API calls

    return ExternalAnchorReceipt(
        backend="ipfs",
        dry_run=False,
        created_at=iso_now(),
        request_fingerprint=fingerprint,
        status="NOT_IMPLEMENTED",
        error="Live IPFS anchoring not yet implemented",
    )


def anchor_via_arweave(
    cfg: ExternalAnchorConfig,
    req: ExternalAnchorRequest
) -> ExternalAnchorReceipt:
    """
    Anchor via Arweave (permanent storage).

    Phase 1: Dry-run implementation.
    - Generates pseudo transaction ID

    Phase 2 (future): Live implementation.
    - Will submit transaction to Arweave network
    """
    fingerprint = _fingerprint_request(req)

    if cfg.dry_run:
        # Dry-run: generate pseudo transaction ID
        pseudo_tx = fingerprint[:43]  # Arweave tx IDs are 43 chars

        gateway_url = None
        if cfg.arweave_gateway:
            gateway_url = f"{cfg.arweave_gateway.rstrip('/')}/{pseudo_tx}"

        return ExternalAnchorReceipt(
            backend="arweave",
            dry_run=True,
            created_at=iso_now(),
            request_fingerprint=fingerprint,
            status="SUCCESS_DRYRUN",
            arweave_tx_id=pseudo_tx,
            arweave_gateway_url=gateway_url,
        )

    # Live mode (Phase 2)
    return ExternalAnchorReceipt(
        backend="arweave",
        dry_run=False,
        created_at=iso_now(),
        request_fingerprint=fingerprint,
        status="NOT_IMPLEMENTED",
        error="Live Arweave anchoring not yet implemented",
    )


# ---------------------------------------------------------------------------
# Main Adapter Interface
# ---------------------------------------------------------------------------

def anchor_externally(
    req: ExternalAnchorRequest,
    cfg: Optional[ExternalAnchorConfig] = None,
) -> Optional[ExternalAnchorReceipt]:
    """
    Main adapter entrypoint.

    Args:
        req: The anchor request containing hashes and metadata
        cfg: Optional config override (loads from file if not provided)

    Returns:
        ExternalAnchorReceipt if a backend is configured, None otherwise

    Raises:
        ValueError: If an unsupported backend is specified
    """
    cfg = cfg or ExternalAnchorConfig.load()

    if cfg.backend == "none":
        return None

    if cfg.backend == "rfc3161":
        return anchor_via_rfc3161(cfg, req)

    if cfg.backend == "ipfs":
        return anchor_via_ipfs(cfg, req)

    if cfg.backend == "arweave":
        return anchor_via_arweave(cfg, req)

    raise ValueError(f"Unsupported backend: {cfg.backend}")


def get_supported_backends() -> List[str]:
    """Return list of supported backend names."""
    return ["none", "rfc3161", "ipfs", "arweave"]


def validate_config(cfg: ExternalAnchorConfig) -> List[str]:
    """
    Validate configuration and return list of warnings/errors.
    """
    issues: List[str] = []

    if cfg.backend not in get_supported_backends():
        issues.append(f"Unknown backend: {cfg.backend}")

    if cfg.backend == "rfc3161" and not cfg.rfc3161_url:
        issues.append("RFC3161 backend requires rfc3161_url")

    if cfg.backend == "ipfs" and not cfg.dry_run and not cfg.ipfs_api_url:
        issues.append("IPFS live mode requires ipfs_api_url")

    if cfg.backend == "arweave" and not cfg.dry_run and not cfg.arweave_wallet_path:
        issues.append("Arweave live mode requires arweave_wallet_path")

    return issues
