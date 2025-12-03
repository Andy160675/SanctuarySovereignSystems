"""
Runtime Interface - Unified API Gateway for Sovereign System
============================================================

Provides:
1. System health aggregation (/system/health)
2. Natural language proposal interface (/propose_nl)
3. Structured proposal submission (/propose)

v1.0.0 - Initial release
"""

import asyncio
import json
import os
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List

import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel


app = FastAPI(title="Runtime Interface", version="1.0.0")


# =============================================================================
# Configuration
# =============================================================================

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://ollama:11434")
MODEL_NAME = os.getenv("MODEL_NAME", "llama3.2")
PLANNER_URL = os.getenv("PLANNER_URL", "http://planner-agent:8000")
LEDGER_URL = os.getenv("LEDGER_URL", "http://ledger_service:8082")
POLICY_GATE_URL = os.getenv("POLICY_GATE_URL", "http://policy_gate:8181")

# Service health endpoints - internal Docker network URLs
SERVICE_HEALTH_MAP = {
    "policy_gate": os.getenv("POLICY_GATE_HEALTH", "http://policy_gate:8181/health"),
    "planner": os.getenv("PLANNER_HEALTH", "http://planner-agent:8000/health"),
    "advocate": os.getenv("ADVOCATE_HEALTH", "http://advocate-agent:8000/health"),
    "confessor": os.getenv("CONFESSOR_HEALTH", "http://confessor-agent:8000/health"),
    "watcher": os.getenv("WATCHER_HEALTH", "http://watcher-agent:8000/health"),
    "ledger": os.getenv("LEDGER_HEALTH", "http://ledger_service:8082/health"),
    "killswitch": os.getenv("KILLSWITCH_HEALTH", "http://control_killswitch:8000/health"),
    "amendment": os.getenv("AMENDMENT_HEALTH", "http://amendment-service:8095/health"),
}


# =============================================================================
# Models
# =============================================================================

class ServiceHealth(BaseModel):
    name: str
    status: str  # "healthy" | "unhealthy" | "unknown"
    detail: Optional[str] = None


class SystemHealth(BaseModel):
    overall: str  # "healthy" | "degraded" | "unhealthy"
    services: List[ServiceHealth]
    checked_at: str


class NLProposal(BaseModel):
    proposal: str  # Natural language proposal from the user


class StructuredProposal(BaseModel):
    mission_type: str
    details: Dict[str, Any]
    justification: str
    sector: Optional[str] = "general"


class ProposalResponse(BaseModel):
    status: str
    proposal_id: Optional[str] = None
    mission_id: Optional[str] = None
    message: str
    structured_proposal: Optional[Dict[str, Any]] = None


# =============================================================================
# System Health Aggregation
# =============================================================================

@app.get("/system/health", response_model=SystemHealth)
async def system_health():
    """
    Aggregate health status from all services.

    Returns overall system status:
    - healthy: All services are healthy
    - degraded: Some services are unknown/unreachable
    - unhealthy: One or more services are unhealthy
    """
    results: List[ServiceHealth] = []
    any_unhealthy = False
    any_unknown = False

    async with httpx.AsyncClient(timeout=3.0) as client:
        for name, url in SERVICE_HEALTH_MAP.items():
            try:
                response = await client.get(url)
                if response.status_code == 200:
                    # Special handling for OPA policy_gate (returns policies list, not {"status": "healthy"})
                    if name == "policy_gate":
                        results.append(ServiceHealth(name=name, status="healthy"))
                    else:
                        data = response.json()
                        status_val = data.get("status", "unknown").lower()
                        if status_val == "healthy":
                            results.append(ServiceHealth(name=name, status="healthy"))
                        else:
                            any_unhealthy = True
                            results.append(ServiceHealth(
                                name=name,
                                status="unhealthy",
                                detail=str(data)
                            ))
                else:
                    any_unhealthy = True
                    results.append(ServiceHealth(
                        name=name,
                        status="unhealthy",
                        detail=f"HTTP {response.status_code}"
                    ))
            except httpx.ConnectError:
                any_unknown = True
                results.append(ServiceHealth(
                    name=name,
                    status="unknown",
                    detail="Connection refused"
                ))
            except httpx.TimeoutException:
                any_unknown = True
                results.append(ServiceHealth(
                    name=name,
                    status="unknown",
                    detail="Timeout"
                ))
            except Exception as e:
                any_unknown = True
                results.append(ServiceHealth(
                    name=name,
                    status="unknown",
                    detail=str(e)
                ))

    if any_unhealthy:
        overall = "unhealthy"
    elif any_unknown:
        overall = "degraded"
    else:
        overall = "healthy"

    return SystemHealth(
        overall=overall,
        services=results,
        checked_at=datetime.now(timezone.utc).isoformat()
    )


# =============================================================================
# Natural Language Proposal Interface
# =============================================================================

NL_SYSTEM_PROMPT = """You are a sovereign AI system's intent parser. Your task is to convert a user's natural-language proposal into a structured JSON object.

The output must be a single, valid JSON object. Do not include any other text, explanations, or markdown formatting.

The JSON object must have the following keys:
- "mission_type": A string, e.g., "MONITOR", "ANALYZE", "REVIEW", "EXECUTE", "REPORT".
- "details": A JSON object containing the specific parameters for the mission.
- "justification": A string summarizing the user's intent.
- "sector": A string representing the target domain (e.g., "finance", "compliance", "operations", "security"). If not specified, use "general".

Example Input: "Review the lease agreement for tenant compliance issues."
Example Output:
{"mission_type": "REVIEW", "details": {"target": "lease_agreement", "focus": "tenant_compliance", "output": "compliance_report"}, "justification": "User wants to review a lease document for compliance issues.", "sector": "compliance"}

Example Input: "Monitor transactions above 10000 for wallet 0x123abc."
Example Output:
{"mission_type": "MONITOR", "details": {"target": "wallet", "identifier": "0x123abc", "condition": "transaction_amount_gt", "threshold": 10000}, "justification": "User wants to monitor high-value transactions for a specific wallet.", "sector": "finance"}

IMPORTANT: Output ONLY the JSON object, no other text."""


async def translate_nl_to_structured(proposal_text: str) -> Dict[str, Any]:
    """Use LLM to translate natural language to structured proposal."""
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{OLLAMA_URL}/api/generate",
                json={
                    "model": MODEL_NAME,
                    "prompt": f"{NL_SYSTEM_PROMPT}\n\nUser Input: {proposal_text}",
                    "stream": False,
                    "format": "json"
                }
            )

            if response.status_code == 200:
                llm_response = response.json().get("response", "").strip()

                # Clean up response if needed
                if "```" in llm_response:
                    json_start = llm_response.find("{")
                    json_end = llm_response.rfind("}") + 1
                    if json_start >= 0 and json_end > json_start:
                        llm_response = llm_response[json_start:json_end]

                return json.loads(llm_response)

    except json.JSONDecodeError as e:
        print(f"[runtime_interface] Failed to parse LLM response as JSON: {e}")
        raise
    except Exception as e:
        print(f"[runtime_interface] Error calling Ollama: {e}")
        raise

    raise ValueError("Failed to get valid response from LLM")


@app.post("/propose_nl", response_model=ProposalResponse)
async def propose_natural_language(nl_proposal: NLProposal):
    """
    Accept a natural-language proposal, translate it to structured format,
    and submit it to the Planner.

    This creates a conversational interface to the Sovereign System.
    """
    print(f"[runtime_interface] Received NL proposal: '{nl_proposal.proposal[:100]}...'")

    try:
        # Step 1: Translate NL to structured proposal
        structured = await translate_nl_to_structured(nl_proposal.proposal)
        print(f"[runtime_interface] Translated to: {json.dumps(structured, indent=2)}")

        # Step 2: Submit to Planner
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{PLANNER_URL}/plan",
                json={
                    "objective": structured.get("justification", nl_proposal.proposal),
                    "context": json.dumps(structured.get("details", {})),
                    "jurisdiction": "UK"
                }
            )

            if response.status_code in (200, 202):
                result = response.json()
                return ProposalResponse(
                    status="submitted",
                    mission_id=result.get("mission_id"),
                    message="Natural language proposal translated and submitted successfully",
                    structured_proposal=structured
                )
            else:
                return ProposalResponse(
                    status="failed",
                    message=f"Planner returned {response.status_code}: {response.text}",
                    structured_proposal=structured
                )

    except json.JSONDecodeError:
        raise HTTPException(
            status_code=500,
            detail="Failed to parse LLM response into valid JSON. Please try rephrasing your proposal."
        )
    except Exception as e:
        print(f"[runtime_interface] Error processing NL proposal: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process natural language proposal: {str(e)}"
        )


@app.post("/propose", response_model=ProposalResponse)
async def propose_structured(proposal: StructuredProposal):
    """
    Submit a structured proposal directly to the Planner.
    """
    print(f"[runtime_interface] Received structured proposal: {proposal.mission_type}")

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{PLANNER_URL}/plan",
                json={
                    "objective": proposal.justification,
                    "context": json.dumps(proposal.details),
                    "jurisdiction": "UK"
                }
            )

            if response.status_code in (200, 202):
                result = response.json()
                return ProposalResponse(
                    status="submitted",
                    mission_id=result.get("mission_id"),
                    message="Structured proposal submitted successfully",
                    structured_proposal=proposal.dict()
                )
            else:
                return ProposalResponse(
                    status="failed",
                    message=f"Planner returned {response.status_code}"
                )

    except Exception as e:
        print(f"[runtime_interface] Error submitting proposal: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to submit proposal: {str(e)}"
        )


# =============================================================================
# Ledger Event Stream Proxy (optional - direct WS from dashboard is preferred)
# =============================================================================

@app.get("/ledger/recent")
async def get_recent_events(limit: int = 20):
    """Get recent ledger events (REST fallback for polling)."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{LEDGER_URL}/entries",
                params={"limit": limit}
            )
            if response.status_code == 200:
                return response.json()
    except Exception as e:
        print(f"[runtime_interface] Error fetching ledger entries: {e}")

    return {"entries": [], "error": "Failed to fetch ledger"}


# =============================================================================
# Health & Info
# =============================================================================

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "runtime_interface"}


@app.get("/info")
async def info():
    return {
        "service": "runtime_interface",
        "version": "1.0.0",
        "capabilities": [
            "system_health_aggregation",
            "natural_language_proposals",
            "structured_proposals",
            "ledger_proxy"
        ],
        "endpoints": {
            "/system/health": "GET - Aggregated system health",
            "/propose_nl": "POST - Natural language proposal",
            "/propose": "POST - Structured proposal",
            "/ledger/recent": "GET - Recent ledger events",
            "/health": "GET - Service health"
        }
    }


@app.on_event("startup")
async def startup_event():
    """Log service startup."""
    print("[runtime_interface] Starting up...")
    print(f"[runtime_interface] Ollama URL: {OLLAMA_URL}")
    print(f"[runtime_interface] Planner URL: {PLANNER_URL}")
    print(f"[runtime_interface] Monitoring {len(SERVICE_HEALTH_MAP)} services for health")
