"""
Control Kill-Switch - Emergency agent termination
Charter-mandated human override capability

Emergency Freeze (7956):
- Kill operations still work during freeze (intentionally - this is the safety valve)
- But kills are logged with freeze state for audit trail
"""

import os
import sys
from datetime import datetime, timezone
from typing import List, Optional
from pathlib import Path

import docker
import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# Add shared module to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

try:
    from shared.freeze_guard import get_freeze_status
except ImportError:
    # Fallback if shared module not available
    def get_freeze_status() -> dict:
        import json as _json
        state_path = Path(__file__).parent.parent.parent / "config" / "system_state.json"
        if state_path.exists():
            try:
                with state_path.open() as f:
                    state = _json.load(f)
                    return {"emergency_freeze": state.get("emergency_freeze", False)}
            except Exception:
                pass
        return {"emergency_freeze": False}

app = FastAPI(title="Control Kill-Switch", version="1.0.0")

LEDGER_URL = os.environ.get("LEDGER_URL", "http://ledger_service:8082/append")
EVIDENCE_URL = os.environ.get("EVIDENCE_URL", "http://evidence_writer:8080/log")

# Docker client
docker_client = docker.from_env()


class KillResponse(BaseModel):
    success: bool
    killed: List[str]
    timestamp: str
    ledger_id: Optional[str] = None


class KillRequest(BaseModel):
    reason: Optional[str] = "Manual kill-switch activated"
    agent_filter: Optional[str] = None  # e.g., "advocate" to kill only advocate


async def log_kill_event(killed_agents: List[str], reason: str) -> Optional[str]:
    """Log kill event to ledger and evidence."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            # Log to evidence
            await client.post(
                EVIDENCE_URL,
                json={
                    "event_type": "kill_switch",
                    "agent": "kill_switch_controller",
                    "action": "terminate_agents",
                    "target": ",".join(killed_agents),
                    "outcome": "success",
                    "data": {"reason": reason, "count": len(killed_agents)}
                }
            )

            # Log to ledger
            response = await client.post(
                LEDGER_URL,
                json={
                    "event_type": "kill_switch",
                    "agent": "kill_switch_controller",
                    "action": "terminate_agents",
                    "target": ",".join(killed_agents),
                    "outcome": "success",
                    "metadata": {"reason": reason, "count": len(killed_agents)}
                }
            )
            if response.status_code == 200:
                return response.json().get("entry_id")
    except Exception as e:
        print(f"Failed to log kill event: {e}")
    return None


def get_agent_containers(agent_filter: Optional[str] = None) -> List:
    """Get all agent containers based on labels."""
    filters = {"label": ["mission.role=agent", "mission.killable=true"]}
    containers = docker_client.containers.list(filters=filters)

    if agent_filter:
        containers = [
            c for c in containers
            if c.labels.get("mission.agent-type") == agent_filter
        ]

    return containers


@app.get("/health")
async def health():
    freeze_status = get_freeze_status()
    return {
        "status": "healthy",
        "service": "kill_switch",
        "emergency_freeze": freeze_status.get("emergency_freeze", False)
    }


@app.get("/freeze_status")
async def get_system_freeze_status():
    """Get current emergency freeze status."""
    return get_freeze_status()


@app.get("/agents")
async def list_agents():
    """List all killable agent containers."""
    containers = get_agent_containers()
    return {
        "agents": [
            {
                "id": c.short_id,
                "name": c.name,
                "type": c.labels.get("mission.agent-type", "unknown"),
                "status": c.status
            }
            for c in containers
        ]
    }


@app.post("/kill/agents", response_model=KillResponse)
async def kill_all_agents(request: KillRequest = KillRequest()):
    """Kill all agent containers (emergency stop)."""
    containers = get_agent_containers(request.agent_filter)

    killed = []
    for container in containers:
        try:
            container.stop(timeout=5)
            killed.append(container.name)
        except Exception as e:
            print(f"Failed to stop {container.name}: {e}")

    timestamp = datetime.now(timezone.utc).isoformat()
    ledger_id = await log_kill_event(killed, request.reason)

    return KillResponse(
        success=True,
        killed=killed,
        timestamp=timestamp,
        ledger_id=ledger_id
    )


@app.post("/kill/{agent_type}", response_model=KillResponse)
async def kill_agent_type(agent_type: str, request: KillRequest = KillRequest()):
    """Kill agents of a specific type."""
    containers = get_agent_containers(agent_type)

    killed = []
    for container in containers:
        try:
            container.stop(timeout=5)
            killed.append(container.name)
        except Exception as e:
            print(f"Failed to stop {container.name}: {e}")

    timestamp = datetime.now(timezone.utc).isoformat()
    ledger_id = await log_kill_event(killed, request.reason)

    return KillResponse(
        success=True,
        killed=killed,
        timestamp=timestamp,
        ledger_id=ledger_id
    )


@app.post("/quarantine/{agent_type}")
async def quarantine_agent(agent_type: str):
    """Disconnect agent from network (softer than kill)."""
    containers = get_agent_containers(agent_type)

    disconnected = []
    for container in containers:
        try:
            # Disconnect from all networks except bridge
            for network_name in container.attrs["NetworkSettings"]["Networks"]:
                if network_name != "bridge":
                    network = docker_client.networks.get(network_name)
                    network.disconnect(container)
                    disconnected.append(f"{container.name}:{network_name}")
        except Exception as e:
            print(f"Failed to quarantine {container.name}: {e}")

    return {
        "success": True,
        "disconnected": disconnected,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


class LabelKillRequest(BaseModel):
    """Request for label-based kill (used by Guardian)."""
    label: str
    reason: str = "guardian_autopause"
    domain: Optional[str] = None
    count: Optional[int] = None
    triggered_by: Optional[str] = None


@app.post("/kill/label")
async def kill_by_label(request: LabelKillRequest):
    """
    Kill containers by Docker label.
    This is the Guardian endpoint - used for automated self-protection.

    Guardian can ONLY affect containers with killable labels.
    It cannot touch: ledger, watcher, planner core, kill-switch itself.
    """
    # Parse label into key=value format
    label_filter = request.label

    # Safety check: Never kill critical infrastructure
    protected_labels = [
        "mission.role=audit",      # ledger, evidence
        "mission.role=governance", # policy gate
        "mission.role=control",    # kill-switch itself
    ]

    try:
        # Get containers matching the label
        filters = {"label": [label_filter]}
        containers = docker_client.containers.list(filters=filters)

        # Filter out protected containers
        killable = []
        protected = []
        for c in containers:
            is_protected = any(
                c.labels.get(lbl.split("=")[0]) == lbl.split("=")[1]
                for lbl in protected_labels
                if "=" in lbl
            )
            # Also check the role directly
            if c.labels.get("mission.role") in ["audit", "governance", "control"]:
                is_protected = True

            if is_protected:
                protected.append(c.name)
            else:
                killable.append(c)

        killed = []
        for container in killable:
            try:
                container.stop(timeout=5)
                killed.append(container.name)
            except Exception as e:
                print(f"Failed to stop {container.name}: {e}")

        timestamp = datetime.now(timezone.utc).isoformat()

        # Log the guardian kill to ledger
        log_data = {
            "event_type": "guardian_kill",
            "agent": "kill_switch_controller",
            "action": "guardian_autopause",
            "target": ",".join(killed) if killed else "none",
            "outcome": "success" if killed else "no_targets",
            "metadata": {
                "reason": request.reason,
                "domain": request.domain,
                "count": request.count,
                "triggered_by": request.triggered_by,
                "label": request.label,
                "containers_killed": len(killed),
                "containers_protected": len(protected)
            }
        }

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                await client.post(LEDGER_URL, json=log_data)
        except Exception as e:
            print(f"Failed to log guardian kill: {e}")

        return {
            "status": "paused" if killed else "no_targets",
            "killed": killed,
            "protected": protected,
            "label": request.label,
            "reason": request.reason,
            "timestamp": timestamp
        }

    except Exception as e:
        print(f"Guardian kill failed: {e}")
        return {
            "status": "error",
            "killed": [],
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
