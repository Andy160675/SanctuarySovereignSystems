#!/usr/bin/env python3
"""
Boardroom Coordinator - Elite Control Plane for Avatar Boardroom
================================================================
Real-time state machine for the 13-avatar governance decision organ.

Manages:
- Per-avatar state (presence, attention, heartbeat)
- Mission lifecycle (DISCUSSING, VOTING, DECIDED)
- Turn-taking protocol (single speaker, Chair recognition)
- Vote collection and decision rules
- WebSocket broadcast to all connected clients

Protocol Events:
- init_state, mission_started, mission_updated, mission_closed
- turn_requested, turn_granted, turn_released
- vote_started, vote_cast, vote_closed
- alert_raised (from Sentinel, Guardian, Watcher, Confessor)

Emergency Freeze (7956):
- All mutating endpoints check freeze state before executing
- Returns immediate rejection when GLOBAL_FREEZE=true
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from enum import Enum
from datetime import datetime, timezone
import json
import asyncio
import uuid
import httpx
import os
import sys

# Add shared module to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

try:
    from shared.freeze_guard import emergency_freeze_active, get_freeze_status
except ImportError:
    # Fallback if shared module not available
    def emergency_freeze_active() -> bool:
        """Check freeze state from config file directly."""
        import json as _json
        from pathlib import Path
        state_path = Path(__file__).parent.parent.parent / "config" / "system_state.json"
        if state_path.exists():
            try:
                with state_path.open() as f:
                    return _json.load(f).get("emergency_freeze", False)
            except Exception:
                return False
        return False

    def get_freeze_status() -> dict:
        return {"emergency_freeze": emergency_freeze_active()}

app = FastAPI(
    title="Boardroom Coordinator",
    version="1.0.0",
    description="Elite control plane for the 13-avatar governance decision organ"
)

# Configuration
LEDGER_URL = os.getenv("LEDGER_URL", "http://ledger_service:8082")


# --- Enums ---
class AvatarStatus(str, Enum):
    OFFLINE = "offline"
    IDLE = "idle"
    SPEAKING = "speaking"
    VOTING = "voting"
    ALERT = "alert"


class MissionStatus(str, Enum):
    NONE = "none"
    DISCUSSING = "discussing"
    VOTING = "voting"
    DECIDED = "decided"


class Decision(str, Enum):
    APPROVE = "approve"
    REJECT = "reject"
    DEFER = "defer"


# --- Avatar Registry (The 13) ---
AVATAR_REGISTRY = {
    1: {"name": "The Chair", "trinity": "Governance", "role": "Ultimate arbiter, enforces turn-taking, final veto"},
    2: {"name": "The Auditor", "trinity": "Governance", "role": "Keeper of truth, ledger, forensic analysis"},
    3: {"name": "The Strategist", "trinity": "Governance", "role": "Forward-looking visionary, simulations, long-term path"},
    4: {"name": "The Synthesist", "trinity": "Intelligence", "role": "Meta-analyst, cross-domain risk assessment"},
    5: {"name": "The Archivist", "trinity": "Intelligence", "role": "Librarian, semantic search, institutional memory"},
    6: {"name": "The Ethicist", "trinity": "Intelligence", "role": "Moral compass, natural law, ethical oversight"},
    7: {"name": "The Legalist", "trinity": "Execution", "role": "Master of contracts and compliance"},
    8: {"name": "The Guardian", "trinity": "Execution", "role": "Protector, cyber security, threat hunting"},
    9: {"name": "The Quartermaster", "trinity": "Execution", "role": "Resources, infrastructure, scaling"},
    10: {"name": "The Scribe", "trinity": "Support", "role": "Chronicler, transcription, documentation"},
    11: {"name": "The Herald", "trinity": "Support", "role": "External interface, API gateway, communications"},
    12: {"name": "The Weaver", "trinity": "Support", "role": "Architect of connections, service mesh, routing"},
    13: {"name": "The Sentinel", "trinity": "Support", "role": "Silent observer, adversarial testing, weakness detection"},
}


# --- State Models ---
class AvatarState(BaseModel):
    avatar_id: int
    name: str
    trinity: str
    role: str
    status: AvatarStatus = AvatarStatus.IDLE
    current_topic: Optional[str] = None
    last_heartbeat: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    vote: Optional[Decision] = None


class MissionState(BaseModel):
    mission_id: str
    prompt: str
    risk_level: str = "MEDIUM"
    origin: str = "unknown"
    status: MissionStatus = MissionStatus.DISCUSSING
    votes: Dict[int, Decision] = Field(default_factory=dict)
    decision: Optional[Decision] = None
    rationale: Optional[str] = None
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    decided_at: Optional[datetime] = None


class BoardroomState:
    """Singleton state manager for the Boardroom."""

    def __init__(self):
        self.session_id = str(uuid.uuid4())
        self.avatars: Dict[int, AvatarState] = {}
        self.current_speaker: Optional[int] = None
        self.active_mission: Optional[MissionState] = None
        self.vote_window_open: bool = False
        self.clients: List[WebSocket] = []
        self.event_history: List[dict] = []

        # Initialize all 13 avatars
        for avatar_id, info in AVATAR_REGISTRY.items():
            self.avatars[avatar_id] = AvatarState(
                avatar_id=avatar_id,
                name=info["name"],
                trinity=info["trinity"],
                role=info["role"]
            )

    def to_dict(self) -> dict:
        """Serialize state for broadcast."""
        return {
            "session_id": self.session_id,
            "avatars": {k: v.model_dump(mode="json") for k, v in self.avatars.items()},
            "current_speaker": self.current_speaker,
            "active_mission": self.active_mission.model_dump(mode="json") if self.active_mission else None,
            "vote_window_open": self.vote_window_open,
        }


# Global state
state = BoardroomState()


# --- Request/Response Models ---
class TurnRequest(BaseModel):
    avatar_id: int
    topic: str


class VoteRequest(BaseModel):
    avatar_id: int
    decision: Decision


class StartMissionRequest(BaseModel):
    mission_id: str
    prompt: str
    risk_level: str = "MEDIUM"
    origin: str = "Planner"


class IngestEventRequest(BaseModel):
    mission_id: str
    event_type: str
    payload: dict


class DecisionRequest(BaseModel):
    decision: Decision
    rationale: str


class AlertRequest(BaseModel):
    avatar_id: int
    alert_type: str
    severity: str
    message: str


# --- WebSocket Broadcast ---
async def broadcast(event_type: str, payload: dict):
    """Broadcast an event to all connected WebSocket clients."""
    message = {
        "type": event_type,
        "payload": payload,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    state.event_history.append(message)

    if state.clients:
        disconnected = []
        for client in state.clients:
            try:
                await client.send_text(json.dumps(message, default=str))
            except Exception:
                disconnected.append(client)

        for client in disconnected:
            state.clients.remove(client)


async def log_to_ledger(event_type: str, payload: dict):
    """Log significant events to the immutable ledger."""
    try:
        async with httpx.AsyncClient() as client:
            await client.post(
                f"{LEDGER_URL}/append",
                json={
                    "event_type": f"boardroom.{event_type}",
                    "payload": payload,
                    "signer": "boardroom_coordinator"
                },
                timeout=5.0
            )
    except Exception:
        pass  # Non-blocking ledger write


# --- WebSocket Endpoint ---
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Real-time WebSocket connection for Boardroom clients."""
    await websocket.accept()
    state.clients.append(websocket)

    # Send initial state
    await websocket.send_text(json.dumps({
        "type": "init_state",
        "payload": state.to_dict(),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }, default=str))

    try:
        while True:
            data = await websocket.receive_text()
            # Handle client commands if needed
            try:
                cmd = json.loads(data)
                if cmd.get("type") == "heartbeat":
                    avatar_id = cmd.get("avatar_id")
                    if avatar_id and avatar_id in state.avatars:
                        state.avatars[avatar_id].last_heartbeat = datetime.now(timezone.utc)
            except json.JSONDecodeError:
                pass
    except WebSocketDisconnect:
        state.clients.remove(websocket)


# --- Turn-Taking Endpoints ---
@app.post("/coordinator/request_turn")
async def request_turn(request: TurnRequest):
    """An avatar requests the floor. Enforces single-speaker invariant."""
    if request.avatar_id not in state.avatars:
        raise HTTPException(status_code=404, detail="Avatar not found")

    if state.current_speaker is not None:
        return {
            "status": "denied",
            "reason": f"Avatar {state.current_speaker} ({state.avatars[state.current_speaker].name}) has the floor"
        }

    # Grant the floor
    state.current_speaker = request.avatar_id
    state.avatars[request.avatar_id].status = AvatarStatus.SPEAKING
    state.avatars[request.avatar_id].current_topic = request.topic

    await broadcast("turn_granted", {
        "avatar_id": request.avatar_id,
        "avatar_name": state.avatars[request.avatar_id].name,
        "topic": request.topic
    })

    return {"status": "granted", "avatar_id": request.avatar_id}


@app.post("/coordinator/release_turn")
async def release_turn(request: TurnRequest):
    """The current speaker releases the floor."""
    if request.avatar_id not in state.avatars:
        raise HTTPException(status_code=404, detail="Avatar not found")

    if state.current_speaker != request.avatar_id:
        return {"status": "error", "reason": "You do not have the floor"}

    state.current_speaker = None
    state.avatars[request.avatar_id].status = AvatarStatus.IDLE
    state.avatars[request.avatar_id].current_topic = None

    await broadcast("turn_released", {
        "avatar_id": request.avatar_id,
        "avatar_name": state.avatars[request.avatar_id].name
    })

    return {"status": "released"}


# --- Mission Lifecycle Endpoints ---
@app.post("/sessions/start_mission")
async def start_mission(request: StartMissionRequest):
    """Start a new mission in the Boardroom. Broadcasts to all clients."""
    # EMERGENCY FREEZE CHECK (7956)
    if emergency_freeze_active():
        return {
            "status": "rejected",
            "reason": "SYSTEM_EMERGENCY_FREEZE_ACTIVE",
            "message": "Emergency freeze is engaged. All mission operations are halted.",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    if state.active_mission and state.active_mission.status != MissionStatus.DECIDED:
        raise HTTPException(
            status_code=409,
            detail=f"Mission {state.active_mission.mission_id} is still active"
        )

    state.active_mission = MissionState(
        mission_id=request.mission_id,
        prompt=request.prompt,
        risk_level=request.risk_level,
        origin=request.origin
    )

    # Reset all avatar votes
    for avatar in state.avatars.values():
        avatar.vote = None

    state.vote_window_open = False

    await broadcast("mission_started", {
        "mission_id": request.mission_id,
        "prompt": request.prompt,
        "risk_level": request.risk_level,
        "origin": request.origin
    })

    await log_to_ledger("mission_started", {
        "mission_id": request.mission_id,
        "prompt": request.prompt,
        "risk_level": request.risk_level
    })

    return {"status": "mission_started", "mission_id": request.mission_id}


@app.post("/sessions/ingest_event")
async def ingest_event(request: IngestEventRequest):
    """Ingest events from Trinity agents into the Boardroom context."""
    if not state.active_mission:
        raise HTTPException(status_code=400, detail="No active mission")

    if state.active_mission.mission_id != request.mission_id:
        raise HTTPException(status_code=400, detail="Mission ID mismatch")

    await broadcast("mission_updated", {
        "mission_id": request.mission_id,
        "event_type": request.event_type,
        "payload": request.payload
    })

    return {"status": "event_ingested", "event_type": request.event_type}


@app.post("/sessions/start_voting")
async def start_voting():
    """Open the voting window for the active mission."""
    # EMERGENCY FREEZE CHECK (7956)
    if emergency_freeze_active():
        return {
            "status": "rejected",
            "reason": "SYSTEM_EMERGENCY_FREEZE_ACTIVE",
            "message": "Emergency freeze is engaged. Voting operations are halted.",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    if not state.active_mission:
        raise HTTPException(status_code=400, detail="No active mission")

    if state.active_mission.status != MissionStatus.DISCUSSING:
        raise HTTPException(status_code=400, detail="Mission not in DISCUSSING state")

    state.active_mission.status = MissionStatus.VOTING
    state.vote_window_open = True

    # Set all avatars to voting status
    for avatar in state.avatars.values():
        avatar.status = AvatarStatus.VOTING

    await broadcast("vote_started", {
        "mission_id": state.active_mission.mission_id
    })

    return {"status": "voting_started"}


@app.post("/coordinator/cast_vote")
async def cast_vote(request: VoteRequest):
    """An avatar casts a vote. Only valid when vote window is open."""
    if request.avatar_id not in state.avatars:
        raise HTTPException(status_code=404, detail="Avatar not found")

    if not state.active_mission:
        raise HTTPException(status_code=400, detail="No active mission")

    if not state.vote_window_open:
        return {"status": "error", "reason": "Vote window is not open"}

    # Record the vote
    state.active_mission.votes[request.avatar_id] = request.decision
    state.avatars[request.avatar_id].vote = request.decision

    await broadcast("vote_cast", {
        "avatar_id": request.avatar_id,
        "avatar_name": state.avatars[request.avatar_id].name,
        "decision": request.decision.value
    })

    return {"status": "recorded", "votes_cast": len(state.active_mission.votes)}


@app.post("/sessions/decision")
async def finalize_decision(request: DecisionRequest):
    """Close voting and record the final Boardroom decision."""
    # EMERGENCY FREEZE CHECK (7956)
    if emergency_freeze_active():
        return {
            "status": "rejected",
            "reason": "SYSTEM_EMERGENCY_FREEZE_ACTIVE",
            "message": "Emergency freeze is engaged. Decision operations are halted.",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    if not state.active_mission:
        raise HTTPException(status_code=400, detail="No active mission")

    if state.active_mission.status == MissionStatus.DECIDED:
        raise HTTPException(status_code=400, detail="Mission already decided")

    # Close voting
    state.vote_window_open = False
    state.active_mission.status = MissionStatus.DECIDED
    state.active_mission.decision = request.decision
    state.active_mission.rationale = request.rationale
    state.active_mission.decided_at = datetime.now(timezone.utc)

    # Reset avatar states
    for avatar in state.avatars.values():
        avatar.status = AvatarStatus.IDLE

    await broadcast("mission_closed", {
        "mission_id": state.active_mission.mission_id,
        "decision": request.decision.value,
        "rationale": request.rationale,
        "votes": {k: v.value for k, v in state.active_mission.votes.items()}
    })

    # Log to ledger
    await log_to_ledger("board_decision", {
        "mission_id": state.active_mission.mission_id,
        "decision": request.decision.value,
        "rationale": request.rationale,
        "votes": {str(k): v.value for k, v in state.active_mission.votes.items()},
        "decided_at": state.active_mission.decided_at.isoformat()
    })

    return {
        "status": "decided",
        "mission_id": state.active_mission.mission_id,
        "decision": request.decision.value
    }


# --- Alert Endpoints ---
@app.post("/coordinator/raise_alert")
async def raise_alert(request: AlertRequest):
    """Raise an alert from any avatar (Sentinel, Guardian, Watcher, Confessor)."""
    if request.avatar_id not in state.avatars:
        raise HTTPException(status_code=404, detail="Avatar not found")

    state.avatars[request.avatar_id].status = AvatarStatus.ALERT

    await broadcast("alert_raised", {
        "avatar_id": request.avatar_id,
        "avatar_name": state.avatars[request.avatar_id].name,
        "alert_type": request.alert_type,
        "severity": request.severity,
        "message": request.message
    })

    return {"status": "alert_raised"}


# --- Query Endpoints ---
@app.get("/coordinator/state")
async def get_state():
    """Get the current Boardroom state."""
    return state.to_dict()


@app.get("/coordinator/avatars")
async def get_avatars():
    """Get all avatar states."""
    return {k: v.model_dump(mode="json") for k, v in state.avatars.items()}


@app.get("/coordinator/mission")
async def get_mission():
    """Get the active mission state."""
    if not state.active_mission:
        return {"status": "no_active_mission"}
    return state.active_mission.model_dump(mode="json")


@app.get("/coordinator/events")
async def get_events(limit: int = 50):
    """Get recent Boardroom events."""
    return state.event_history[-limit:]


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    freeze_status = get_freeze_status()
    return {
        "status": "healthy",
        "service": "boardroom_coordinator",
        "session_id": state.session_id,
        "connected_clients": len(state.clients),
        "active_mission": state.active_mission.mission_id if state.active_mission else None,
        "emergency_freeze": freeze_status.get("emergency_freeze", False)
    }


@app.get("/freeze_status")
async def get_system_freeze_status():
    """Get current emergency freeze status."""
    return get_freeze_status()
