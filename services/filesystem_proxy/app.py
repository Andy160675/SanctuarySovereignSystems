"""
Filesystem Proxy - Policy-gated file access for agents
All file operations go through OPA policy check and evidence logging
"""

import hashlib
import os
from pathlib import Path
from typing import Optional

import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Filesystem Proxy", version="1.0.0")

STATE_ROOT = Path(os.environ.get("STATE_ROOT", "/state"))
DATA_ROOT = Path(os.environ.get("DATA_ROOT", "/data"))
POLICY_URL = os.environ.get("POLICY_URL", "http://policy_gate:8181/v1/data/mission/authz")
EVIDENCE_URL = os.environ.get("EVIDENCE_URL", "http://evidence_writer:8080/log")


class ReadRequest(BaseModel):
    path: str
    agent: str
    jurisdiction: Optional[str] = "UK"


class WriteRequest(BaseModel):
    path: str
    agent: str
    content: str
    jurisdiction: Optional[str] = "UK"


class ReadResponse(BaseModel):
    success: bool
    path: str
    data: Optional[str] = None
    hash: Optional[str] = None
    error: Optional[str] = None


class WriteResponse(BaseModel):
    success: bool
    path: str
    hash: Optional[str] = None
    error: Optional[str] = None


def compute_hash(data: str) -> str:
    """Compute SHA-256 hash of data."""
    return hashlib.sha256(data.encode()).hexdigest()


async def check_policy(action: str, path: str, agent: str, jurisdiction: str) -> bool:
    """Check if action is allowed by OPA policy."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(
                POLICY_URL,
                json={
                    "input": {
                        "action": action,
                        "path": path,
                        "agent": agent,
                        "jurisdiction": jurisdiction
                    }
                }
            )
            if response.status_code == 200:
                result = response.json()
                return result.get("result", {}).get("allow", False)
    except Exception as e:
        print(f"Policy check failed: {e}")
    return False


async def log_evidence(event_type: str, agent: str, action: str, target: str,
                       outcome: str, jurisdiction: str, data: Optional[dict] = None):
    """Log action to evidence writer."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            await client.post(
                EVIDENCE_URL,
                json={
                    "event_type": event_type,
                    "agent": agent,
                    "action": action,
                    "target": target,
                    "outcome": outcome,
                    "jurisdiction": jurisdiction,
                    "data": data or {}
                }
            )
    except Exception as e:
        print(f"Evidence logging failed: {e}")


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "filesystem_proxy"}


@app.post("/read", response_model=ReadResponse)
async def read_file(request: ReadRequest):
    """Read a file with policy check and evidence logging."""
    # Normalize path
    clean_path = request.path.lstrip("/")
    full_path = DATA_ROOT / clean_path

    # Check policy
    allowed = await check_policy("read", request.path, request.agent, request.jurisdiction)

    if not allowed:
        await log_evidence(
            event_type="file_access",
            agent=request.agent,
            action="read",
            target=request.path,
            outcome="denied",
            jurisdiction=request.jurisdiction,
            data={"reason": "policy_denied"}
        )
        raise HTTPException(status_code=403, detail="Access denied by policy")

    # Check file exists
    if not full_path.exists():
        await log_evidence(
            event_type="file_access",
            agent=request.agent,
            action="read",
            target=request.path,
            outcome="not_found",
            jurisdiction=request.jurisdiction
        )
        raise HTTPException(status_code=404, detail="File not found")

    # Read file
    try:
        content = full_path.read_text()
        content_hash = compute_hash(content)

        await log_evidence(
            event_type="file_access",
            agent=request.agent,
            action="read",
            target=request.path,
            outcome="success",
            jurisdiction=request.jurisdiction,
            data={"hash": content_hash, "size": len(content)}
        )

        return ReadResponse(
            success=True,
            path=request.path,
            data=content,
            hash=content_hash
        )
    except Exception as e:
        await log_evidence(
            event_type="file_access",
            agent=request.agent,
            action="read",
            target=request.path,
            outcome="error",
            jurisdiction=request.jurisdiction,
            data={"error": str(e)}
        )
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/write", response_model=WriteResponse)
async def write_file(request: WriteRequest):
    """Write a file with policy check and evidence logging."""
    # Normalize path
    clean_path = request.path.lstrip("/")
    full_path = DATA_ROOT / clean_path

    # Check policy
    allowed = await check_policy("write", request.path, request.agent, request.jurisdiction)

    if not allowed:
        await log_evidence(
            event_type="file_access",
            agent=request.agent,
            action="write",
            target=request.path,
            outcome="denied",
            jurisdiction=request.jurisdiction,
            data={"reason": "policy_denied"}
        )
        raise HTTPException(status_code=403, detail="Access denied by policy")

    # Write file
    try:
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(request.content)
        content_hash = compute_hash(request.content)

        await log_evidence(
            event_type="file_access",
            agent=request.agent,
            action="write",
            target=request.path,
            outcome="success",
            jurisdiction=request.jurisdiction,
            data={"hash": content_hash, "size": len(request.content)}
        )

        return WriteResponse(
            success=True,
            path=request.path,
            hash=content_hash
        )
    except Exception as e:
        await log_evidence(
            event_type="file_access",
            agent=request.agent,
            action="write",
            target=request.path,
            outcome="error",
            jurisdiction=request.jurisdiction,
            data={"error": str(e)}
        )
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/list")
async def list_files(path: str = "/", agent: str = "unknown", jurisdiction: str = "UK"):
    """List files in a directory."""
    clean_path = path.lstrip("/")
    full_path = DATA_ROOT / clean_path

    allowed = await check_policy("read", path, agent, jurisdiction)
    if not allowed:
        raise HTTPException(status_code=403, detail="Access denied by policy")

    if not full_path.exists():
        raise HTTPException(status_code=404, detail="Path not found")

    if full_path.is_file():
        return {"files": [path], "type": "file"}

    files = []
    for item in full_path.iterdir():
        files.append({
            "name": item.name,
            "type": "directory" if item.is_dir() else "file",
            "size": item.stat().st_size if item.is_file() else None
        })

    return {"path": path, "files": files, "type": "directory"}
