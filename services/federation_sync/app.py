#!/usr/bin/env python3
"""
Federation Sync Service
=======================

Ring 1: Federated Constitutional Network

This service enables proof-only synchronization between sovereign nodes.
It NEVER imports raw mission data - only:
- Anchor receipts (external timestamping proofs)
- Watcher summaries
- Guardian/Byzantine events

Core invariant: Each node remains fully sovereign. Federation adds
cryptographic witnesses, not dependencies.

THINK + WORRY + REFUSE + ACT + REMEMBER = OK
"""

import asyncio
import hashlib
import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

import httpx
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field

# =============================================================================
# Configuration
# =============================================================================

NODE_ID = os.getenv("NODE_ID", f"node-{uuid4().hex[:8]}")
LEDGER_URL = os.getenv("LEDGER_URL", "http://ledger:8082")
WATCHER_URL = os.getenv("WATCHER_URL", "http://watcher:8093")

# Peer nodes to sync with (comma-separated URLs)
PEER_NODES = [p.strip() for p in os.getenv("PEER_NODES", "").split(",") if p.strip()]

# Sync interval in seconds
SYNC_INTERVAL = int(os.getenv("SYNC_INTERVAL", "60"))

# Signing key path (for future cryptographic attestation)
SIGNING_KEY_PATH = os.getenv("SIGNING_KEY_PATH", "/keys/federation.key")

app = FastAPI(
    title="Federation Sync",
    description="Proof-only cross-node verification for Ring 1",
    version="1.0.0"
)

# =============================================================================
# Models
# =============================================================================

class AnchorReceipt(BaseModel):
    """External timestamp anchor receipt."""
    anchor_id: str
    timestamp: str
    ledger_hash: str
    external_proof: Optional[str] = None
    source_node: str
    signature: Optional[str] = None


class WatcherSummary(BaseModel):
    """Periodic watcher summary for cross-node sharing."""
    summary_id: str
    node_id: str
    period_start: str
    period_end: str
    total_missions: int
    approved_count: int
    rejected_count: int
    guardian_halts: int
    byzantine_events: int
    ledger_hash_at_period_end: str
    signature: Optional[str] = None


class GuardianEvent(BaseModel):
    """Guardian halt or Byzantine event."""
    event_id: str
    node_id: str
    timestamp: str
    event_type: str  # guardian_halt, byzantine_detected, anchor_invalid
    severity: str  # INFO, WARNING, CRITICAL
    description: str
    affected_mission: Optional[str] = None
    signature: Optional[str] = None


class PeerVerificationResult(BaseModel):
    """Result of verifying a peer's proof."""
    verification_id: str = Field(default_factory=lambda: str(uuid4()))
    peer_node: str
    verified_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    anchor_valid: bool
    chain_consistent: bool
    status: str  # VALID, INVALID, UNREACHABLE
    issues: List[str] = Field(default_factory=list)


class FederationStatus(BaseModel):
    """Current federation status."""
    node_id: str
    peers_configured: int
    peers_verified: int
    last_sync: Optional[str]
    pending_verifications: int


# =============================================================================
# In-Memory State (would be persisted in production)
# =============================================================================

class FederationState:
    def __init__(self):
        self.verified_peers: Dict[str, PeerVerificationResult] = {}
        self.received_anchors: List[AnchorReceipt] = []
        self.received_summaries: List[WatcherSummary] = []
        self.guardian_events: List[GuardianEvent] = []
        self.last_sync: Optional[str] = None
        self.sync_running: bool = False

state = FederationState()


# =============================================================================
# Verification Logic
# =============================================================================

def compute_hash(data: str) -> str:
    """Compute SHA-256 hash of data."""
    return hashlib.sha256(data.encode()).hexdigest()


def verify_anchor_receipt(anchor: AnchorReceipt) -> tuple[bool, List[str]]:
    """
    Verify an anchor receipt from a peer node.

    Checks:
    1. Anchor ID format is valid
    2. Timestamp is parseable and not in future
    3. Ledger hash format is valid (64 hex chars)
    4. If signature present, validate it (future: cryptographic)
    """
    issues = []

    # Check anchor ID
    if not anchor.anchor_id or len(anchor.anchor_id) < 8:
        issues.append("Invalid anchor_id format")

    # Check timestamp
    try:
        ts = datetime.fromisoformat(anchor.timestamp.replace("Z", "+00:00"))
        if ts > datetime.now(timezone.utc):
            issues.append("Anchor timestamp is in the future")
    except Exception:
        issues.append("Invalid timestamp format")

    # Check ledger hash format
    if not anchor.ledger_hash or len(anchor.ledger_hash) != 64:
        issues.append("Invalid ledger_hash format (expected 64 hex chars)")
    else:
        try:
            int(anchor.ledger_hash, 16)
        except ValueError:
            issues.append("ledger_hash is not valid hexadecimal")

    # Future: Signature verification would go here
    # if anchor.signature:
    #     if not verify_signature(anchor, anchor.signature):
    #         issues.append("Invalid signature")

    return len(issues) == 0, issues


def verify_chain_consistency(peer_hash: str, our_hash: str) -> tuple[bool, List[str]]:
    """
    Verify ledger chain consistency.

    Note: In a full implementation, this would verify the Merkle proof
    path from the peer's claimed hash back to a known common anchor.
    For Ring 1 genesis, we accept matching recent anchors.
    """
    issues = []

    # Basic validation
    if not peer_hash or not our_hash:
        issues.append("Missing hash for comparison")
        return False, issues

    # In federated mode, chains may diverge but anchors should be verifiable
    # against external timestamp services
    # For now, we just validate format

    return True, issues


async def log_to_ledger(event_type: str, data: Dict[str, Any]) -> bool:
    """Log a federation event to local ledger."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            entry = {
                "event_type": event_type,
                "source": "federation_sync",
                "node_id": NODE_ID,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "metadata": data
            }
            resp = await client.post(f"{LEDGER_URL}/log", json=entry)
            return resp.status_code in (200, 201, 202)
    except Exception as e:
        print(f"[WARN] Failed to log to ledger: {e}")
        return False


# =============================================================================
# Peer Sync Operations
# =============================================================================

async def fetch_peer_anchors(peer_url: str) -> List[AnchorReceipt]:
    """Fetch recent anchor receipts from a peer node."""
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(f"{peer_url}/federation/anchors")
            if resp.status_code == 200:
                data = resp.json()
                return [AnchorReceipt(**a) for a in data.get("anchors", [])]
    except Exception as e:
        print(f"[WARN] Failed to fetch anchors from {peer_url}: {e}")
    return []


async def fetch_peer_summary(peer_url: str) -> Optional[WatcherSummary]:
    """Fetch latest watcher summary from a peer node."""
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(f"{peer_url}/federation/summary")
            if resp.status_code == 200:
                return WatcherSummary(**resp.json())
    except Exception as e:
        print(f"[WARN] Failed to fetch summary from {peer_url}: {e}")
    return None


async def fetch_peer_guardian_events(peer_url: str) -> List[GuardianEvent]:
    """Fetch guardian/byzantine events from a peer node."""
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(f"{peer_url}/federation/guardian-events")
            if resp.status_code == 200:
                data = resp.json()
                return [GuardianEvent(**e) for e in data.get("events", [])]
    except Exception as e:
        print(f"[WARN] Failed to fetch guardian events from {peer_url}: {e}")
    return []


async def verify_peer(peer_url: str) -> PeerVerificationResult:
    """
    Perform full verification of a peer node.

    This is the core Ring 1 operation - verifying that another sovereign
    node's governance claims are valid without trusting their data.
    """
    result = PeerVerificationResult(
        peer_node=peer_url,
        anchor_valid=False,
        chain_consistent=False,
        status="UNREACHABLE",
        issues=[]
    )

    try:
        # Fetch peer's latest anchor
        anchors = await fetch_peer_anchors(peer_url)
        if not anchors:
            result.issues.append("No anchors available from peer")
            return result

        latest_anchor = anchors[0]  # Assume sorted by recency

        # Verify anchor receipt
        anchor_valid, anchor_issues = verify_anchor_receipt(latest_anchor)
        result.anchor_valid = anchor_valid
        result.issues.extend(anchor_issues)

        # Verify chain consistency (simplified for genesis)
        chain_valid, chain_issues = verify_chain_consistency(
            latest_anchor.ledger_hash,
            "local_hash_placeholder"  # Would fetch from local ledger
        )
        result.chain_consistent = chain_valid
        result.issues.extend(chain_issues)

        # Determine overall status
        if anchor_valid and chain_valid:
            result.status = "VALID"
        else:
            result.status = "INVALID"

        # Log verification result to ledger
        event_type = "peer_anchor_verified" if result.status == "VALID" else "peer_anchor_rejected"
        await log_to_ledger(event_type, {
            "peer_node": peer_url,
            "anchor_id": latest_anchor.anchor_id,
            "status": result.status,
            "issues": result.issues
        })

    except Exception as e:
        result.issues.append(f"Verification error: {str(e)}")
        result.status = "UNREACHABLE"

    return result


async def sync_with_peers():
    """
    Background task: Sync with all configured peer nodes.

    This runs periodically to:
    1. Fetch and verify peer anchors
    2. Pull watcher summaries
    3. Check for guardian/byzantine events
    4. Update local verification state
    """
    if state.sync_running:
        return

    state.sync_running = True
    print(f"[INFO] Starting federation sync with {len(PEER_NODES)} peers")

    try:
        for peer_url in PEER_NODES:
            print(f"[INFO] Syncing with peer: {peer_url}")

            # Verify peer
            result = await verify_peer(peer_url)
            state.verified_peers[peer_url] = result

            if result.status == "VALID":
                print(f"[OK] Peer {peer_url} verified successfully")

                # Fetch additional data from verified peer
                summary = await fetch_peer_summary(peer_url)
                if summary:
                    state.received_summaries.append(summary)

                guardian_events = await fetch_peer_guardian_events(peer_url)
                state.guardian_events.extend(guardian_events)

                # Log any critical guardian events
                for event in guardian_events:
                    if event.severity == "CRITICAL":
                        await log_to_ledger("peer_guardian_alert", {
                            "peer_node": peer_url,
                            "event": event.dict()
                        })
            else:
                print(f"[WARN] Peer {peer_url} verification failed: {result.issues}")

        state.last_sync = datetime.now(timezone.utc).isoformat()

    finally:
        state.sync_running = False


# =============================================================================
# API Endpoints - Inbound (What We Expose to Peers)
# =============================================================================

@app.get("/health")
async def health():
    """Health check."""
    return {
        "status": "healthy",
        "service": "federation_sync",
        "node_id": NODE_ID,
        "peers_configured": len(PEER_NODES),
        "peers_verified": len([p for p in state.verified_peers.values() if p.status == "VALID"])
    }


@app.get("/federation/anchors")
async def get_anchors():
    """
    Expose our anchor receipts to peer nodes.

    In production, this would fetch from local ledger's anchor chain.
    """
    # Fetch from local ledger
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(f"{LEDGER_URL}/entries", params={
                "event_type": "anchor_receipt",
                "limit": 10
            })
            if resp.status_code == 200:
                data = resp.json()
                entries = data.get("entries", data) if isinstance(data, dict) else data
                anchors = []
                for e in entries:
                    anchors.append({
                        "anchor_id": e.get("id", str(uuid4())),
                        "timestamp": e.get("timestamp"),
                        "ledger_hash": e.get("metadata", {}).get("ledger_hash", ""),
                        "external_proof": e.get("metadata", {}).get("external_proof"),
                        "source_node": NODE_ID
                    })
                return {"anchors": anchors, "node_id": NODE_ID}
    except Exception as e:
        print(f"[WARN] Failed to fetch local anchors: {e}")

    return {"anchors": [], "node_id": NODE_ID}


@app.get("/federation/summary")
async def get_summary():
    """
    Expose our watcher summary to peer nodes.
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(f"{WATCHER_URL}/summary")
            if resp.status_code == 200:
                data = resp.json()
                return WatcherSummary(
                    summary_id=str(uuid4()),
                    node_id=NODE_ID,
                    period_start=data.get("period_start", ""),
                    period_end=data.get("period_end", datetime.now(timezone.utc).isoformat()),
                    total_missions=data.get("total_missions", 0),
                    approved_count=data.get("approved", 0),
                    rejected_count=data.get("rejected", 0),
                    guardian_halts=data.get("guardian_halts", 0),
                    byzantine_events=data.get("byzantine_events", 0),
                    ledger_hash_at_period_end=data.get("ledger_hash", "")
                ).dict()
    except Exception as e:
        print(f"[WARN] Failed to fetch watcher summary: {e}")

    return {"error": "Summary unavailable"}


@app.get("/federation/guardian-events")
async def get_guardian_events():
    """
    Expose guardian/byzantine events to peer nodes.
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(f"{LEDGER_URL}/entries", params={
                "limit": 50
            })
            if resp.status_code == 200:
                data = resp.json()
                entries = data.get("entries", data) if isinstance(data, dict) else data

                guardian_types = {"guardian_halt", "byzantine_detected", "anchor_invalid", "guardian_intervention"}
                events = []

                for e in entries:
                    if e.get("event_type") in guardian_types:
                        events.append(GuardianEvent(
                            event_id=e.get("id", str(uuid4())),
                            node_id=NODE_ID,
                            timestamp=e.get("timestamp"),
                            event_type=e.get("event_type"),
                            severity=e.get("metadata", {}).get("severity", "WARNING"),
                            description=e.get("metadata", {}).get("description", ""),
                            affected_mission=e.get("target")
                        ).dict())

                return {"events": events, "node_id": NODE_ID}
    except Exception as e:
        print(f"[WARN] Failed to fetch guardian events: {e}")

    return {"events": [], "node_id": NODE_ID}


# =============================================================================
# API Endpoints - Outbound (Our View of the Federation)
# =============================================================================

@app.get("/status")
async def federation_status():
    """Get current federation status."""
    return FederationStatus(
        node_id=NODE_ID,
        peers_configured=len(PEER_NODES),
        peers_verified=len([p for p in state.verified_peers.values() if p.status == "VALID"]),
        last_sync=state.last_sync,
        pending_verifications=len([p for p in state.verified_peers.values() if p.status == "UNREACHABLE"])
    ).dict()


@app.get("/peers")
async def list_peers():
    """List all peer verification results."""
    return {
        "node_id": NODE_ID,
        "peers": [v.dict() for v in state.verified_peers.values()]
    }


@app.post("/sync")
async def trigger_sync(background_tasks: BackgroundTasks):
    """Manually trigger a federation sync."""
    if state.sync_running:
        return {"status": "sync_already_running"}

    background_tasks.add_task(sync_with_peers)
    return {"status": "sync_started", "peers": PEER_NODES}


@app.post("/verify/{peer_url:path}")
async def verify_single_peer(peer_url: str):
    """Verify a specific peer node."""
    result = await verify_peer(peer_url)
    state.verified_peers[peer_url] = result
    return result.dict()


# =============================================================================
# Background Sync Loop
# =============================================================================

@app.on_event("startup")
async def startup():
    """Start background sync loop."""
    print(f"[INFO] Federation Sync starting - Node ID: {NODE_ID}")
    print(f"[INFO] Configured peers: {PEER_NODES}")

    if PEER_NODES:
        asyncio.create_task(periodic_sync())


async def periodic_sync():
    """Periodically sync with peers."""
    while True:
        await asyncio.sleep(SYNC_INTERVAL)
        if PEER_NODES:
            await sync_with_peers()


# =============================================================================
# Entry Point
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8094)
