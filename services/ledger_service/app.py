"""
Ledger Service - Immutable append-only audit trail
Hash-chained entries for tamper detection
WebSocket streaming for real-time event broadcast (v2.0.0)
"""

import asyncio
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Set
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel


# =============================================================================
# WebSocket Connection Manager
# =============================================================================

class ConnectionManager:
    """Manages WebSocket connections for real-time event broadcasting."""

    def __init__(self):
        self.active_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)
        print(f"[WS] Client connected. Total subscribers: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)
        print(f"[WS] Client disconnected. Total subscribers: {len(self.active_connections)}")

    async def broadcast(self, event: dict):
        """Broadcast event to all connected clients."""
        if not self.active_connections:
            return

        message = json.dumps(event)
        disconnected = set()

        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception:
                disconnected.add(connection)

        # Clean up disconnected clients
        for conn in disconnected:
            self.active_connections.discard(conn)


manager = ConnectionManager()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan - startup and shutdown."""
    print("[Ledger] Service starting with WebSocket support")
    yield
    print("[Ledger] Service shutting down")


app = FastAPI(title="Ledger Service", version="2.0.0", lifespan=lifespan)

LEDGER_PATH = Path(os.environ.get("LEDGER_PATH", "/data/ledger.jsonl"))
HASH_CHAIN = os.environ.get("HASH_CHAIN", "true").lower() == "true"

# Ensure ledger directory exists
LEDGER_PATH.parent.mkdir(parents=True, exist_ok=True)

# Track last hash for chain
_last_hash: Optional[str] = None


def compute_hash(data: str, prev_hash: Optional[str] = None) -> str:
    """Compute SHA-256 hash, optionally chained to previous."""
    content = f"{prev_hash or 'genesis'}:{data}"
    return hashlib.sha256(content.encode()).hexdigest()


def get_last_hash() -> Optional[str]:
    """Get the hash of the last ledger entry."""
    global _last_hash
    if _last_hash:
        return _last_hash

    if not LEDGER_PATH.exists():
        return None

    last_line = None
    with open(LEDGER_PATH, "r") as f:
        for line in f:
            if line.strip():
                last_line = line

    if last_line:
        try:
            entry = json.loads(last_line)
            _last_hash = entry.get("hash")
        except json.JSONDecodeError:
            pass

    return _last_hash


class LedgerEntry(BaseModel):
    event_type: str
    agent: Optional[str] = None
    action: Optional[str] = None
    target: Optional[str] = None
    outcome: Optional[str] = None
    metadata: Optional[dict] = None


class LedgerResponse(BaseModel):
    success: bool
    entry_id: str
    hash: str
    timestamp: str


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "ledger"}


@app.post("/append", response_model=LedgerResponse)
async def append_entry(entry: LedgerEntry):
    """Append a new entry to the ledger with hash chain."""
    global _last_hash

    timestamp = datetime.now(timezone.utc).isoformat()
    entry_id = f"L-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}"

    # Build the entry
    ledger_record = {
        "id": entry_id,
        "timestamp": timestamp,
        "event_type": entry.event_type,
        "agent": entry.agent,
        "action": entry.action,
        "target": entry.target,
        "outcome": entry.outcome,
        "metadata": entry.metadata or {},
    }

    # Compute hash chain
    prev_hash = get_last_hash() if HASH_CHAIN else None
    record_json = json.dumps(ledger_record, sort_keys=True)
    entry_hash = compute_hash(record_json, prev_hash)

    ledger_record["prev_hash"] = prev_hash
    ledger_record["hash"] = entry_hash

    # Append to ledger file
    with open(LEDGER_PATH, "a") as f:
        f.write(json.dumps(ledger_record) + "\n")

    _last_hash = entry_hash

    # Broadcast to all WebSocket subscribers
    await manager.broadcast(ledger_record)

    return LedgerResponse(
        success=True,
        entry_id=entry_id,
        hash=entry_hash,
        timestamp=timestamp
    )


@app.get("/entries")
async def get_entries(limit: int = 100, offset: int = 0):
    """Get recent ledger entries."""
    if not LEDGER_PATH.exists():
        return {"entries": [], "total": 0}

    entries = []
    with open(LEDGER_PATH, "r") as f:
        for line in f:
            if line.strip():
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    continue

    total = len(entries)
    entries = entries[offset:offset + limit]

    return {"entries": entries, "total": total, "offset": offset, "limit": limit}


@app.get("/verify")
async def verify_chain():
    """Verify the hash chain integrity."""
    if not LEDGER_PATH.exists():
        return {"valid": True, "entries_checked": 0, "message": "Empty ledger"}

    entries = []
    with open(LEDGER_PATH, "r") as f:
        for line in f:
            if line.strip():
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    continue

    if not entries:
        return {"valid": True, "entries_checked": 0}

    prev_hash = None
    for i, entry in enumerate(entries):
        stored_hash = entry.pop("hash", None)
        stored_prev = entry.pop("prev_hash", None)

        if stored_prev != prev_hash:
            return {
                "valid": False,
                "broken_at": i,
                "entry_id": entry.get("id"),
                "reason": "prev_hash mismatch"
            }

        record_json = json.dumps(entry, sort_keys=True)
        computed_hash = compute_hash(record_json, prev_hash)

        if computed_hash != stored_hash:
            return {
                "valid": False,
                "broken_at": i,
                "entry_id": entry.get("id"),
                "reason": "hash mismatch"
            }

        prev_hash = stored_hash

    return {"valid": True, "entries_checked": len(entries)}


# =============================================================================
# WebSocket Endpoint - Real-time Event Stream
# =============================================================================

def get_recent_entries(limit: int = 10):
    """Get the most recent ledger entries for initial context."""
    if not LEDGER_PATH.exists():
        return []

    entries = []
    with open(LEDGER_PATH, "r") as f:
        for line in f:
            if line.strip():
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    continue

    return entries[-limit:]  # Return last N entries


@app.websocket("/ws/events")
async def websocket_events(websocket: WebSocket):
    """
    WebSocket endpoint for real-time ledger event streaming.

    On connect: Sends last 10 events as context
    Ongoing: Broadcasts new events as they are appended

    Usage:
        const ws = new WebSocket('ws://localhost:8082/ws/events');
        ws.onmessage = (event) => { console.log(JSON.parse(event.data)); };
    """
    await manager.connect(websocket)

    try:
        # Send recent entries as initial context
        context_entries = get_recent_entries(10)
        await websocket.send_text(json.dumps({
            "type": "context",
            "data": context_entries,
            "count": len(context_entries)
        }))

        # Keep connection alive - listen for client messages (heartbeat/close)
        while True:
            try:
                # Wait for any message from client (ping/close)
                data = await asyncio.wait_for(websocket.receive_text(), timeout=60.0)
                # Handle ping
                if data == "ping":
                    await websocket.send_text(json.dumps({"type": "pong"}))
            except asyncio.TimeoutError:
                # Send heartbeat
                await websocket.send_text(json.dumps({"type": "heartbeat"}))

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        print(f"[WS] Error: {e}")
        manager.disconnect(websocket)


@app.get("/ws/subscribers")
async def get_subscriber_count():
    """Get the number of active WebSocket subscribers."""
    return {
        "subscribers": len(manager.active_connections),
        "status": "streaming"
    }
