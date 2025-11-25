#!/usr/bin/env python3
"""
Sovereign System - Trinity Backend
===================================
Three-agent orchestrator with HTTP-based service communication.

Agents:
  - InvestigatorAgent → Truth Engine (8002)
  - VerifierAgent     → Sovereign Core (8001)
  - GuardianAgent     → Enforcement API (8003)

Run:
  pip install fastapi uvicorn httpx
  python trinity_backend.py

Endpoints:
  POST /api/trinity/run_case  → Full investigation pipeline
  GET  /health                → Backend health

Usage:
  curl -X POST http://localhost:8600/api/trinity/run_case \
    -H "Content-Type: application/json" \
    -d '{"case_id": "CASE-TEST-001", "query": "evidence"}'
"""

import httpx
import asyncio
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# Import SVC for embedded version control
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from svc import commit_run, get_history, verify_chain, get_stats

# =============================================================================
# CONFIGURATION
# =============================================================================

SERVICE_URLS = {
    "truth": "http://localhost:8002",
    "core": "http://localhost:8001",
    "enforce": "http://localhost:8003",
    "models": "http://localhost:8004",
    "aggregated": "http://localhost:8502"
}

# LLM endpoint (on aggregated backend for simplicity)
LLM_ANALYZE_URL = "http://localhost:8502/api/llm/analyze"

# =============================================================================
# AGENT DEFINITIONS
# =============================================================================

@dataclass
class AgentResult:
    """Standard result from any agent."""
    agent: str
    success: bool
    data: Dict[str, Any]
    timestamp: str
    error: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)


class InvestigatorAgent:
    """
    Investigator Agent - Searches Truth Engine for evidence.

    Responsibilities:
    - Query truth/search endpoint
    - Extract evidence paths and hashes
    - Return findings for verification
    """

    def __init__(self, truth_url: str = SERVICE_URLS["aggregated"]):
        self.truth_url = truth_url
        self.name = "InvestigatorAgent"

    async def investigate(self, query: str, case_id: str) -> AgentResult:
        """Search for evidence related to a case."""
        timestamp = datetime.now(timezone.utc).isoformat()

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{self.truth_url}/truth/search",
                    json={"query": f"{case_id} {query}"}
                )
                response.raise_for_status()
                data = response.json()

                # Extract evidence with hashes
                evidence_items = []
                for result in data.get("results", []):
                    if result.get("evidence_path") and result.get("event_hash"):
                        evidence_items.append({
                            "id": result["id"],
                            "path": result["evidence_path"],
                            "hash": result["event_hash"],
                            "score": result["score"]
                        })

                return AgentResult(
                    agent=self.name,
                    success=True,
                    data={
                        "query": query,
                        "case_id": case_id,
                        "evidence_found": len(evidence_items),
                        "evidence": evidence_items,
                        "search_time_ms": data.get("search_time_ms", 0)
                    },
                    timestamp=timestamp
                )

        except Exception as e:
            return AgentResult(
                agent=self.name,
                success=False,
                data={"query": query, "case_id": case_id},
                timestamp=timestamp,
                error=str(e)
            )


class VerifierAgent:
    """
    Verifier Agent - Validates evidence integrity via hash verification.

    Responsibilities:
    - Take evidence paths and expected hashes from Investigator
    - Call verify_hash endpoint on Core
    - Report match/mismatch status
    """

    def __init__(self, core_url: str = SERVICE_URLS["aggregated"]):
        self.core_url = core_url
        self.name = "VerifierAgent"

    async def verify(self, evidence_items: list) -> AgentResult:
        """Verify integrity of evidence items."""
        timestamp = datetime.now(timezone.utc).isoformat()

        if not evidence_items:
            return AgentResult(
                agent=self.name,
                success=True,
                data={"verified": 0, "results": [], "message": "No evidence to verify"},
                timestamp=timestamp
            )

        results = []
        verified_count = 0
        tampered_count = 0

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                for item in evidence_items:
                    try:
                        response = await client.post(
                            f"{self.core_url}/api/core/verify_hash",
                            json={
                                "evidence_path": item["path"],
                                "expected_hash": item["hash"]
                            }
                        )
                        response.raise_for_status()
                        verify_result = response.json()

                        if verify_result.get("match"):
                            verified_count += 1
                            status = "verified"
                        else:
                            tampered_count += 1
                            status = "TAMPERED"

                        results.append({
                            "id": item["id"],
                            "status": status,
                            "match": verify_result.get("match"),
                            "actual_hash": verify_result.get("actual"),
                            "expected_hash": item["hash"]
                        })

                    except Exception as e:
                        results.append({
                            "id": item["id"],
                            "status": "error",
                            "error": str(e)
                        })

            return AgentResult(
                agent=self.name,
                success=True,
                data={
                    "verified": verified_count,
                    "tampered": tampered_count,
                    "total": len(evidence_items),
                    "results": results,
                    "integrity_status": "COMPROMISED" if tampered_count > 0 else "INTACT"
                },
                timestamp=timestamp
            )

        except Exception as e:
            return AgentResult(
                agent=self.name,
                success=False,
                data={"evidence_count": len(evidence_items)},
                timestamp=timestamp,
                error=str(e)
            )


class GuardianAgent:
    """
    Guardian Agent - Takes enforcement action based on verification results.

    Responsibilities:
    - Receive verification status from Verifier
    - Decide on enforcement action (flag, quarantine, alert)
    - Log action to enforcement API
    """

    def __init__(self, enforce_url: str = SERVICE_URLS["aggregated"]):
        self.enforce_url = enforce_url
        self.name = "GuardianAgent"

    async def enforce(self, verification_result: Dict[str, Any], case_id: str) -> AgentResult:
        """Take enforcement action based on verification."""
        timestamp = datetime.now(timezone.utc).isoformat()

        integrity_status = verification_result.get("integrity_status", "UNKNOWN")
        tampered_count = verification_result.get("tampered", 0)

        # Decide action based on integrity
        if integrity_status == "COMPROMISED":
            action = "quarantine"
            severity = "critical"
            message = f"Evidence tampering detected: {tampered_count} file(s) modified"
        elif integrity_status == "INTACT":
            action = "log"
            severity = "info"
            message = "All evidence verified intact"
        else:
            action = "flag"
            severity = "warning"
            message = "Verification status unclear - flagging for review"

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{self.enforce_url}/enforce/action",
                    json={
                        "action": action,
                        "case_id": case_id,
                        "severity": severity,
                        "reason": message
                    }
                )
                response.raise_for_status()
                enforce_result = response.json()

                return AgentResult(
                    agent=self.name,
                    success=True,
                    data={
                        "action_taken": action,
                        "severity": severity,
                        "message": message,
                        "reference": enforce_result.get("reference"),
                        "case_id": case_id,
                        "integrity_status": integrity_status
                    },
                    timestamp=timestamp
                )

        except Exception as e:
            return AgentResult(
                agent=self.name,
                success=False,
                data={"action_attempted": action, "case_id": case_id},
                timestamp=timestamp,
                error=str(e)
            )


class DollAgent:
    """
    LLM Russian-doll Agent - Wraps the whole Trinity run into a nested analysis.

    Responsibilities:
    - Receive run summary from orchestrator
    - Call LLM analyze endpoint for nested interpretation
    - Return inner summary + outer commentary (two-layer reflection)
    """

    def __init__(self, llm_url: str = LLM_ANALYZE_URL):
        self.llm_url = llm_url
        self.name = "DollAgent"

    async def analyze(
        self,
        run_id: str,
        case_id: str,
        evidence_count: int,
        mismatch_count: int
    ) -> AgentResult:
        """Generate LLM Russian-doll analysis of the run."""
        timestamp = datetime.now(timezone.utc).isoformat()

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    self.llm_url,
                    json={
                        "run_id": run_id,
                        "case_id": case_id,
                        "stats": {
                            "evidence_count": evidence_count,
                            "mismatch_count": mismatch_count
                        },
                        "prompt": (
                            "Summarise this integrity run and provide a second-layer "
                            "reflection on risk and system behaviour."
                        )
                    }
                )
                response.raise_for_status()
                data = response.json()

                return AgentResult(
                    agent=self.name,
                    success=True,
                    data={
                        "inner_summary": data.get("inner_summary", ""),
                        "risk_lens": data.get("risk_lens", "unknown"),
                        "outer_commentary": data.get("outer_commentary", ""),
                        "meta": data.get("meta", {})
                    },
                    timestamp=timestamp
                )

        except Exception as e:
            return AgentResult(
                agent=self.name,
                success=False,
                data={"run_id": run_id, "case_id": case_id},
                timestamp=timestamp,
                error=str(e)
            )


# =============================================================================
# TRINITY ORCHESTRATOR
# =============================================================================

class TrinityOrchestrator:
    """
    Orchestrates the four agents in sequence:
    Investigator → Verifier → Guardian → Doll (LLM)
    """

    def __init__(self):
        self.investigator = InvestigatorAgent()
        self.verifier = VerifierAgent()
        self.guardian = GuardianAgent()
        self.doll = DollAgent()

    async def run_case(self, case_id: str, query: str) -> Dict[str, Any]:
        """Execute full investigation pipeline."""
        pipeline_start = datetime.now(timezone.utc)

        # Phase 1: Investigation
        investigation = await self.investigator.investigate(query, case_id)

        if not investigation.success:
            return {
                "success": False,
                "case_id": case_id,
                "error": "Investigation failed",
                "investigation": investigation.to_dict(),
                "pipeline_duration_ms": self._duration_ms(pipeline_start)
            }

        # Phase 2: Verification
        evidence_items = investigation.data.get("evidence", [])
        verification = await self.verifier.verify(evidence_items)

        # Phase 3: Enforcement (always runs, even if verification had issues)
        enforcement = await self.guardian.enforce(
            verification.data if verification.success else {"integrity_status": "UNKNOWN"},
            case_id
        )

        # Phase 4: LLM Russian-doll analysis
        import uuid
        run_id = str(uuid.uuid4())[:8]
        evidence_count = investigation.data.get("evidence_found", 0)
        mismatch_count = verification.data.get("tampered", 0) if verification.success else 0

        llm_analysis = await self.doll.analyze(
            run_id=run_id,
            case_id=case_id,
            evidence_count=evidence_count,
            mismatch_count=mismatch_count
        )

        # Phase 5: SVC Commit - Embed this run into the sovereign lineage chain
        pipeline_duration = self._duration_ms(pipeline_start)
        integrity_status = verification.data.get("integrity_status", "UNKNOWN")
        action_taken = enforcement.data.get("action_taken", "none")
        risk_lens = llm_analysis.data.get("risk_lens", "unknown") if llm_analysis.success else "error"

        svc_commit = commit_run(
            run_id=run_id,
            case_id=case_id,
            query=query,
            evidence_count=evidence_count,
            mismatch_count=mismatch_count,
            integrity_status=integrity_status,
            action_taken=action_taken,
            risk_lens=risk_lens,
            llm_analysis=llm_analysis.data if llm_analysis.success else None,
            pipeline_duration_ms=pipeline_duration,
            extra_metadata={
                "investigation_success": investigation.success,
                "verification_success": verification.success,
                "enforcement_success": enforcement.success,
                "llm_success": llm_analysis.success
            }
        )

        return {
            "success": True,
            "case_id": case_id,
            "query": query,
            "run_id": run_id,
            "pipeline": {
                "investigation": investigation.to_dict(),
                "verification": verification.to_dict(),
                "enforcement": enforcement.to_dict(),
                "llm_analysis": llm_analysis.to_dict()
            },
            "summary": {
                "evidence_found": evidence_count,
                "integrity_status": verification.data.get("integrity_status", "UNKNOWN"),
                "action_taken": enforcement.data.get("action_taken", "none"),
                "risk_lens": llm_analysis.data.get("risk_lens", "unknown") if llm_analysis.success else "error"
            },
            "llm_analysis": {
                "inner_summary": llm_analysis.data.get("inner_summary", ""),
                "risk_lens": llm_analysis.data.get("risk_lens", "unknown"),
                "outer_commentary": llm_analysis.data.get("outer_commentary", "")
            } if llm_analysis.success else None,
            "svc": {
                "commit_hash": svc_commit.get("commit_hash"),
                "parent_commit": svc_commit.get("parent_commit"),
                "commit_id": svc_commit.get("commit_id")
            },
            "pipeline_duration_ms": pipeline_duration
        }

    def _duration_ms(self, start: datetime) -> int:
        return int((datetime.now(timezone.utc) - start).total_seconds() * 1000)


# =============================================================================
# FASTAPI APPLICATION
# =============================================================================

app = FastAPI(
    title="Sovereign Trinity Backend",
    version="1.0.0",
    description="Three-agent orchestrator for evidence investigation and verification"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

orchestrator = TrinityOrchestrator()


class RunCaseRequest(BaseModel):
    case_id: str
    query: str = "evidence"


@app.post("/api/trinity/run_case")
async def run_trinity_case(request: RunCaseRequest):
    """Execute full Trinity pipeline: Investigate → Verify → Enforce."""
    result = await orchestrator.run_case(request.case_id, request.query)
    return result


# =============================================================================
# SVC ENDPOINTS - Sovereign Version Control
# =============================================================================

@app.get("/api/trinity/svc/history")
def svc_history(limit: int = 20):
    """Get SVC commit history."""
    commits = get_history(limit=limit)
    return {
        "count": len(commits),
        "commits": commits
    }


@app.get("/api/trinity/svc/stats")
def svc_stats():
    """Get SVC statistics."""
    return get_stats()


@app.get("/api/trinity/svc/verify")
def svc_verify():
    """Verify integrity of the SVC commit chain."""
    return verify_chain()


@app.get("/api/trinity/svc/head")
def svc_head():
    """Get the latest commit."""
    commits = get_history(limit=1)
    if commits:
        return {"head": commits[0]}
    return {"head": None, "message": "No commits yet"}


@app.get("/health")
def health():
    """Trinity backend health check."""
    svc_info = get_stats()
    return {
        "status": "healthy",
        "service": "Trinity Backend",
        "version": "1.2.0-svc",
        "agents": ["InvestigatorAgent", "VerifierAgent", "GuardianAgent", "DollAgent"],
        "svc": {
            "total_commits": svc_info.get("total_commits", 0),
            "chain_valid": svc_info.get("chain_valid", True)
        },
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@app.get("/")
def root():
    return {
        "service": "Sovereign Trinity Backend",
        "version": "1.2.0-svc",
        "endpoints": [
            "/health",
            "/api/trinity/run_case",
            "/api/trinity/svc/history",
            "/api/trinity/svc/stats",
            "/api/trinity/svc/verify",
            "/api/trinity/svc/head"
        ],
        "agents": {
            "Investigator": "Searches Truth Engine for evidence",
            "Verifier": "Validates evidence integrity via hash",
            "Guardian": "Takes enforcement action",
            "Doll": "LLM Russian-doll analysis (inner/outer reflection)"
        },
        "svc": "Sovereign Version Control - Every run becomes an immutable, chained commit"
    }


# =============================================================================
# RUNNER
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("  SOVEREIGN TRINITY BACKEND v1.2.0-svc")
    print("  Four-Agent Orchestrator + Sovereign Version Control")
    print("=" * 60)
    print()
    print("Agents:")
    print("  - InvestigatorAgent -> Truth Engine")
    print("  - VerifierAgent     -> Sovereign Core")
    print("  - GuardianAgent     -> Enforcement API")
    print("  - DollAgent         -> LLM Analysis (Russian Doll)")
    print()
    print("SVC (Sovereign Version Control):")
    print("  Every run is hashed, chained, and committed to lineage.")
    print()
    print("Starting on port 8600...")
    print()
    print("Test with:")
    print('  curl -X POST http://localhost:8600/api/trinity/run_case \\')
    print('    -H "Content-Type: application/json" \\')
    print('    -d \'{"case_id": "CASE-TEST-001", "query": "evidence"}\'')
    print()
    print("SVC endpoints:")
    print("  GET /api/trinity/svc/history  - View commit log")
    print("  GET /api/trinity/svc/stats    - Chain statistics")
    print("  GET /api/trinity/svc/verify   - Verify chain integrity")
    print("  GET /api/trinity/svc/head     - Latest commit")
    print()

    uvicorn.run(app, host="0.0.0.0", port=8600, log_level="info")
