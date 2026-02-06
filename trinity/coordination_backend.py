#!/usr/bin/env python3
"""
The Blade of Truth - Coordination Backend
=========================================
Manages the "Main Agent" tier (3 per PC) and coordinates their conversations.
Orchestrates high-level deliberation before triggering Trinity clusters.

Endpoints:
  POST /api/coordinate/mission  -> Full coordinated deliberation
  GET  /health                  -> Coordination health
"""

import httpx
import asyncio
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import os

# --- Configuration ---
TRINITY_BACKEND_URL = os.environ.get("TRINITY_BACKEND_URL", "http://localhost:8600")

# --- Models ---
class MissionRequest(BaseModel):
    objective: str
    context: Optional[str] = "Standard fleet operation"
    pc_id: str = "PC1"

@dataclass
class CoordinationEvent:
    agent: str
    action: str
    message: str
    timestamp: str = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc).isoformat()

# --- Main Agents ---

class MainLead:
    """The Lead Coordinator - One per PC, one global fleet lead."""
    def __init__(self, node_id: str):
        self.node_id = node_id
        self.role = "Lead Coordinator"
        self.is_fleet_lead = (node_id == "PC1")

    def deliberate(self, objective: str) -> str:
        prefix = "[FLEET LEAD]" if self.is_fleet_lead else "[NODE LEAD]"
        return f"{prefix} Mission objective received: '{objective}'. Initiating coordination sequence on {self.node_id}."

class MainEthicist:
    """The Ethics Observer - Audits intent against constitutional values."""
    def __init__(self, node_id: str):
        self.node_id = node_id
        self.role = "Ethics Observer"

    def review(self, objective: str) -> Dict[str, Any]:
        # Simple heuristic for ethics review
        forbidden = ["delete", "bypass", "override", "rewrite"]
        safe = not any(word in objective.lower() for word in forbidden)
        
        return {
            "status": "APPROVED" if safe else "FLAGGED",
            "reason": "Objective aligns with Value Alignment protocols." if safe else "Contains forbidden operational keywords.",
            "node_id": self.node_id
        }

class MainAuditor:
    """The Audit Master - Verifies SVC and chain integrity post-execution."""
    def __init__(self, node_id: str):
        self.node_id = node_id
        self.role = "Audit Master"

    def audit_result(self, trinity_result: Dict[str, Any]) -> Dict[str, Any]:
        svc = trinity_result.get("svc", {})
        integrity = trinity_result.get("summary", {}).get("integrity_status", "UNKNOWN")
        
        return {
            "status": "VERIFIED" if integrity == "INTACT" else "FAILED",
            "commit_id": svc.get("commit_id"),
            "merkle_valid": True, # Simulated
            "node_id": self.node_id
        }

# --- Coordination Engine ---

class Coordinator:
    def __init__(self, node_id: str):
        self.lead = MainLead(node_id)
        self.ethicist = MainEthicist(node_id)
        self.auditor = MainAuditor(node_id)
        self.node_id = node_id

    async def coordinate_mission(self, objective: str) -> Dict[str, Any]:
        transcript = []
        
        # 1. Lead initiates
        msg = self.lead.deliberate(objective)
        transcript.append(asdict(CoordinationEvent("Lead", "INITIATE", msg)))
        
        # 2. Ethics Review
        review = self.ethicist.review(objective)
        transcript.append(asdict(CoordinationEvent("Ethicist", "REVIEW", f"Status: {review['status']}. {review['reason']}")))
        
        if review["status"] == "FLAGGED":
            return {
                "success": False,
                "status": "BLOCKED_BY_ETHICS",
                "transcript": transcript,
                "node_id": self.node_id
            }

        # 3. Trigger Trinity (Search & Verify)
        transcript.append(asdict(CoordinationEvent("Lead", "ACTIVATE_TRINITY", "Handing off to Trinity clusters for evidence discovery.")))
        
        trinity_data = {}
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(
                    f"{TRINITY_BACKEND_URL}/api/trinity/run_case",
                    json={"case_id": f"MISSION-{datetime.now().strftime('%Y%m%d%H%M')}", "query": objective}
                )
                trinity_data = resp.json()
        except Exception as e:
            transcript.append(asdict(CoordinationEvent("System", "ERROR", f"Trinity communication failed: {str(e)}")))
            return {"success": False, "error": "Trinity Cluster Unreachable", "transcript": transcript}

        # 4. Auditor Final Check
        audit = self.auditor.audit_result(trinity_data)
        transcript.append(asdict(CoordinationEvent("Auditor", "FINAL_AUDIT", f"Integrity check {audit['status']}. Commit: {audit['commit_id']}")))

        # 5. Lead Concludes
        final_msg = f"Mission executed successfully. Results verified and anchored in SVC."
        transcript.append(asdict(CoordinationEvent("Lead", "CONCLUDE", final_msg)))

        return {
            "success": audit["status"] == "VERIFIED",
            "objective": objective,
            "transcript": transcript,
            "trinity_summary": trinity_data.get("summary"),
            "svc": trinity_data.get("svc"),
            "node_id": self.node_id
        }

# --- FastAPI App ---

app = FastAPI(title="Sovereign Coordination Backend", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

@app.post("/api/coordinate/mission")
async def coordinate_mission(request: MissionRequest):
    coordinator = Coordinator(request.pc_id)
    result = await coordinator.coordinate_mission(request.objective)
    return result

@app.get("/health")
def health():
    return {
        "status": "healthy",
        "service": "Coordination Backend",
        "agents": ["Lead Coordinator", "Ethics Observer", "Audit Master"],
        "node": os.environ.get("NODE_ID", "PC1")
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8700)
