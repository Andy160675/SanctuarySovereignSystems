#!/usr/bin/env python3
"""
Filesystem Proxy - Policy-Gated File Access

All file operations go through OPA policy check before execution.
Evidence is logged to evidence_writer.
"""

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Filesystem Proxy", version="1.0.0")

# Configuration
STATE_ROOT = Path(os.getenv("STATE_ROOT", "/state"))
POLICY_URL = os.getenv("POLICY_URL", "http://policy_gate:8181/v1/data/mission/authz")
EVIDENCE_URL = os.getenv("EVIDENCE_URL", "http://evidence_writer:8080/log")


class ReadRequest(BaseModel):
    path: str
    agent: str
    jurisdiction: str = "UK"


class WriteRequest(BaseModel):
    path: str
    content: str
    agent: str
    jurisdiction: str = "UK"


class ListRequest(BaseModel):
    path: str
    agent: str
    jurisdiction: str = "UK"


def iso_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


async def check_policy(action: str, agent: str, jurisdiction: str, path: str) -> dict:
    """Query OPA for policy decision."""
    payload = {
        "input": {
            "action": action,
            "agent": agent,
            "jurisdiction": jurisdiction,
            "path": path,
            "timestamp": iso_now()
        }
    }

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.post(POLICY_URL, json=payload)
            if resp.status_code == 200:
                result = resp.json()
                return result.get("result", {})
    except Exception as e:
        # Fail closed - deny on policy error
        return {"allow": False, "deny_reasons": [f"Policy check failed: {str(e)}"]}

    return {"allow": False, "deny_reasons": ["Policy unavailable"]}


async def log_evidence(event: dict):
    """Log event to evidence writer."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            await client.post(EVIDENCE_URL, json=event)
    except Exception:
        # Don't fail on evidence logging error, but could log locally
        pass


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "filesystem-proxy", "timestamp": iso_now()}


@app.post("/read")
async def read_file(req: ReadRequest):
    """Read file with policy check."""

    # Check policy
    decision = await check_policy("read", req.agent, req.jurisdiction, req.path)

    if not decision.get("allow", False):
        await log_evidence({
            "event": "file_access_denied",
            "action": "read",
            "path": req.path,
            "agent": req.agent,
            "jurisdiction": req.jurisdiction,
            "reasons": decision.get("deny_reasons", []),
            "timestamp": iso_now()
        })
        raise HTTPException(status_code=403, detail={
            "error": "Policy denied",
            "reasons": decision.get("deny_reasons", [])
        })

    # Resolve path within state root
    target = STATE_ROOT / req.path.lstrip("/")

    if not target.exists():
        raise HTTPException(status_code=404, detail={"error": "File not found"})

    if not target.is_file():
        raise HTTPException(status_code=400, detail={"error": "Not a file"})

    # Read and hash
    content = target.read_bytes()
    content_hash = sha256_hex(content)

    # Log evidence
    await log_evidence({
        "event": "file_read",
        "action": "read",
        "path": req.path,
        "agent": req.agent,
        "jurisdiction": req.jurisdiction,
        "hash": content_hash,
        "size": len(content),
        "timestamp": iso_now()
    })

    return {
        "path": req.path,
        "hash": content_hash,
        "size": len(content),
        "content": content.decode("utf-8", errors="replace"),
        "timestamp": iso_now()
    }


@app.post("/list")
async def list_directory(req: ListRequest):
    """List directory with policy check."""

    decision = await check_policy("list", req.agent, req.jurisdiction, req.path)

    if not decision.get("allow", False):
        await log_evidence({
            "event": "directory_list_denied",
            "action": "list",
            "path": req.path,
            "agent": req.agent,
            "jurisdiction": req.jurisdiction,
            "reasons": decision.get("deny_reasons", []),
            "timestamp": iso_now()
        })
        raise HTTPException(status_code=403, detail={
            "error": "Policy denied",
            "reasons": decision.get("deny_reasons", [])
        })

    target = STATE_ROOT / req.path.lstrip("/")

    if not target.exists():
        raise HTTPException(status_code=404, detail={"error": "Path not found"})

    if not target.is_dir():
        raise HTTPException(status_code=400, detail={"error": "Not a directory"})

    entries = []
    for item in target.iterdir():
        entries.append({
            "name": item.name,
            "type": "directory" if item.is_dir() else "file",
            "size": item.stat().st_size if item.is_file() else None
        })

    await log_evidence({
        "event": "directory_listed",
        "action": "list",
        "path": req.path,
        "agent": req.agent,
        "jurisdiction": req.jurisdiction,
        "entry_count": len(entries),
        "timestamp": iso_now()
    })

    return {
        "path": req.path,
        "entries": entries,
        "timestamp": iso_now()
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
