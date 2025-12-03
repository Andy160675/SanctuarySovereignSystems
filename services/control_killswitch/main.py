#!/usr/bin/env python3
"""
Control Kill-Switch - Emergency Agent Termination

Provides endpoints to immediately halt agent containers.
All kill events are logged for audit.
"""

import json
import os
import subprocess
from datetime import datetime, timezone
from typing import List, Optional

import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Control Kill-Switch", version="1.0.0")

EVIDENCE_URL = os.getenv("EVIDENCE_URL", "http://evidence_writer:8080/log")

# Agent container patterns to kill
AGENT_PATTERNS = [
    "advocate",
    "confessor",
    "evidence_validator",
    "analyst",
    "agent"
]


def iso_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


async def log_evidence(event: dict):
    """Log event to evidence writer."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            await client.post(EVIDENCE_URL, json=event)
    except Exception:
        pass


def get_agent_containers() -> List[dict]:
    """List running containers matching agent patterns."""
    try:
        result = subprocess.run(
            ["docker", "ps", "--format", "{{.ID}}\t{{.Names}}\t{{.Image}}"],
            capture_output=True,
            text=True,
            timeout=10
        )
        containers = []
        for line in result.stdout.strip().split("\n"):
            if line:
                parts = line.split("\t")
                if len(parts) >= 3:
                    container_id, name, image = parts[0], parts[1], parts[2]
                    # Check if matches agent pattern
                    for pattern in AGENT_PATTERNS:
                        if pattern in name.lower() or pattern in image.lower():
                            containers.append({
                                "id": container_id,
                                "name": name,
                                "image": image
                            })
                            break
        return containers
    except Exception as e:
        return []


def kill_container(container_id: str) -> bool:
    """Kill a specific container."""
    try:
        result = subprocess.run(
            ["docker", "kill", container_id],
            capture_output=True,
            text=True,
            timeout=30
        )
        return result.returncode == 0
    except Exception:
        return False


class KillResponse(BaseModel):
    killed: List[str]
    failed: List[str]
    timestamp: str


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "control-killswitch", "timestamp": iso_now()}


@app.get("/agents")
async def list_agents():
    """List running agent containers."""
    containers = get_agent_containers()
    return {
        "agents": containers,
        "count": len(containers),
        "timestamp": iso_now()
    }


@app.post("/kill/agents")
async def kill_all_agents():
    """Emergency kill all agent containers."""
    containers = get_agent_containers()

    killed = []
    failed = []

    for container in containers:
        if kill_container(container["id"]):
            killed.append(container["name"])
        else:
            failed.append(container["name"])

    # Log evidence
    await log_evidence({
        "event": "emergency_kill",
        "scope": "all_agents",
        "killed": killed,
        "failed": failed,
        "total_targeted": len(containers),
        "timestamp": iso_now()
    })

    return KillResponse(
        killed=killed,
        failed=failed,
        timestamp=iso_now()
    )


@app.post("/kill/{container_name}")
async def kill_specific(container_name: str):
    """Kill a specific container by name."""
    containers = get_agent_containers()

    target = None
    for c in containers:
        if c["name"] == container_name:
            target = c
            break

    if not target:
        raise HTTPException(status_code=404, detail={"error": f"Container '{container_name}' not found"})

    success = kill_container(target["id"])

    await log_evidence({
        "event": "targeted_kill",
        "container": container_name,
        "success": success,
        "timestamp": iso_now()
    })

    if success:
        return {"killed": container_name, "timestamp": iso_now()}
    else:
        raise HTTPException(status_code=500, detail={"error": "Kill failed"})


@app.post("/halt")
async def halt_system():
    """Emergency halt - kill all sovereign containers."""
    try:
        # Get ALL sovereign-related containers
        result = subprocess.run(
            ["docker", "ps", "-q", "--filter", "name=sovereign"],
            capture_output=True,
            text=True,
            timeout=10
        )
        container_ids = result.stdout.strip().split("\n")
        container_ids = [c for c in container_ids if c]

        killed = []
        for cid in container_ids:
            if kill_container(cid):
                killed.append(cid)

        await log_evidence({
            "event": "system_halt",
            "killed_count": len(killed),
            "timestamp": iso_now()
        })

        return {
            "halted": True,
            "containers_killed": len(killed),
            "timestamp": iso_now()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": str(e)})


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
