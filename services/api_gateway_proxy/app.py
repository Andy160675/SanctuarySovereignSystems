"""
API Gateway Proxy - External API access control for agents
Policy-gated outbound API calls with evidence logging
"""

import os
from typing import Optional
from urllib.parse import urlparse

import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="API Gateway Proxy", version="1.0.0")

POLICY_URL = os.environ.get("POLICY_URL", "http://policy_gate:8181/v1/data/mission/authz")
EVIDENCE_URL = os.environ.get("EVIDENCE_URL", "http://evidence_writer:8080/log")
ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "api.openai.com,api.anthropic.com").split(",")


class APIRequest(BaseModel):
    url: str
    method: str = "GET"
    headers: Optional[dict] = None
    body: Optional[dict] = None
    agent: str
    jurisdiction: Optional[str] = "UK"


class APIResponse(BaseModel):
    success: bool
    status_code: Optional[int] = None
    data: Optional[dict] = None
    error: Optional[str] = None


async def log_evidence(agent: str, action: str, target: str, outcome: str,
                       jurisdiction: str, data: Optional[dict] = None):
    """Log API call to evidence writer."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            await client.post(
                EVIDENCE_URL,
                json={
                    "event_type": "api_call",
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
    return {"status": "healthy", "service": "api_gateway_proxy"}


@app.post("/call", response_model=APIResponse)
async def call_api(request: APIRequest):
    """Make an external API call with policy check and logging."""
    # Parse and validate URL
    parsed = urlparse(request.url)
    host = parsed.netloc

    # Check if host is allowed
    if host not in ALLOWED_HOSTS:
        await log_evidence(
            agent=request.agent,
            action=f"{request.method} {request.url}",
            target=host,
            outcome="denied",
            jurisdiction=request.jurisdiction,
            data={"reason": "host_not_allowed"}
        )
        raise HTTPException(status_code=403, detail=f"Host {host} not in allowed list")

    # Make the API call
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.request(
                method=request.method,
                url=request.url,
                headers=request.headers,
                json=request.body if request.method in ["POST", "PUT", "PATCH"] else None
            )

            await log_evidence(
                agent=request.agent,
                action=f"{request.method} {request.url}",
                target=host,
                outcome="success",
                jurisdiction=request.jurisdiction,
                data={"status_code": response.status_code}
            )

            return APIResponse(
                success=True,
                status_code=response.status_code,
                data=response.json() if response.headers.get("content-type", "").startswith("application/json") else {"text": response.text[:1000]}
            )
    except Exception as e:
        await log_evidence(
            agent=request.agent,
            action=f"{request.method} {request.url}",
            target=host,
            outcome="error",
            jurisdiction=request.jurisdiction,
            data={"error": str(e)}
        )
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/allowed-hosts")
async def get_allowed_hosts():
    """List allowed external hosts."""
    return {"allowed_hosts": ALLOWED_HOSTS}
