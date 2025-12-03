"""
Database Proxy - Policy-gated database access for agents
Placeholder implementation - extend for actual DB connectivity
"""

import os
from typing import Optional

import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Database Proxy", version="1.0.0")

POLICY_URL = os.environ.get("POLICY_URL", "http://policy_gate:8181/v1/data/mission/authz")
EVIDENCE_URL = os.environ.get("EVIDENCE_URL", "http://evidence_writer:8080/log")


class QueryRequest(BaseModel):
    query: str
    agent: str
    jurisdiction: Optional[str] = "UK"


class QueryResponse(BaseModel):
    success: bool
    rows: Optional[list] = None
    error: Optional[str] = None


async def log_evidence(agent: str, action: str, target: str, outcome: str,
                       jurisdiction: str, data: Optional[dict] = None):
    """Log DB query to evidence writer."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            await client.post(
                EVIDENCE_URL,
                json={
                    "event_type": "db_query",
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
    return {"status": "healthy", "service": "db_proxy"}


@app.post("/query", response_model=QueryResponse)
async def execute_query(request: QueryRequest):
    """Execute a database query (placeholder)."""
    # Log the attempt
    await log_evidence(
        agent=request.agent,
        action="query",
        target="database",
        outcome="placeholder",
        jurisdiction=request.jurisdiction,
        data={"query_preview": request.query[:100]}
    )

    # Placeholder response
    return QueryResponse(
        success=True,
        rows=[],
        error="Database proxy is a placeholder - implement actual DB connectivity"
    )
