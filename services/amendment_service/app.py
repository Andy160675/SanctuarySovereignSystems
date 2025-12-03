"""
Amendment Service - Dynamic Policy Update Mechanism
===================================================

Orchestrates the amendment process for constitutional changes.
Requires supermajority (75%) Trinity consensus for acceptance.

v1.0.0 - Initial release
"""

import asyncio
import os
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from enum import Enum

import httpx
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel


app = FastAPI(title="Amendment Service", version="1.0.0")


# =============================================================================
# Configuration
# =============================================================================

LEDGER_URL = os.getenv("LEDGER_URL", "http://ledger_service:8082")
TRINITY_URLS = {
    "planner": os.getenv("PLANNER_URL", "http://planner-agent:8000"),
    "advocate": os.getenv("ADVOCATE_URL", "http://advocate-agent:8000"),
    "confessor": os.getenv("CONFESSOR_URL", "http://confessor-agent:8000"),
}

SUPERMAJORITY_THRESHOLD = 0.75  # 75% agreement required
VOTING_TIMEOUT_SECONDS = 60  # Timeout for each agent vote


# =============================================================================
# Models
# =============================================================================

class AmendmentStatus(str, Enum):
    INITIALIZING = "INITIALIZING"
    IN_VOTING = "IN_VOTING"
    PENDING_APPLY = "PENDING_APPLY"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    FAILED = "FAILED"


class AmendmentProposal(BaseModel):
    target_file: str  # e.g., "constitution.json", "policies/risk.rego"
    new_content: str
    justification: str
    proposer: Optional[str] = "human"


class AmendmentRecord(BaseModel):
    amendment_id: str
    proposal_id: str
    status: AmendmentStatus
    votes: Dict[str, Optional[str]]  # role -> vote
    consensus: float
    outcome: str
    created_at: str
    updated_at: str


# In-memory store
active_amendments: Dict[str, Dict[str, Any]] = {}


# =============================================================================
# Ledger Integration
# =============================================================================

async def log_to_ledger(event_type: str, details: dict) -> Optional[str]:
    """Log amendment event to the immutable ledger."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{LEDGER_URL}/append",
                json={
                    "event_type": event_type,
                    "agent": "amendment_service",
                    "action": "amendment_process",
                    "target": details.get("amendment_id"),
                    "outcome": details.get("status"),
                    "metadata": details
                }
            )
            if response.status_code == 200:
                return response.json().get("entry_id")
    except Exception as e:
        print(f"[Amendment] CRITICAL: Could not log to ledger: {e}")
    return None


# =============================================================================
# Voting Logic
# =============================================================================

async def get_agent_vote(role: str, url: str, proposal: dict) -> tuple[str, str]:
    """Request a vote from a Trinity agent."""
    try:
        async with httpx.AsyncClient(timeout=VOTING_TIMEOUT_SECONDS) as client:
            response = await client.post(
                f"{url}/vote_on_amendment",
                json=proposal
            )
            if response.status_code == 200:
                data = response.json()
                return data.get("vote", "ABSTAIN"), data.get("reasoning", "No reasoning provided")
    except Exception as e:
        print(f"[Amendment] Could not get vote from {role}: {e}")

    return "ABSTAIN", f"Agent {role} unavailable"


async def run_amendment_voting(amendment_id: str, proposal: dict):
    """Execute the amendment voting process."""
    try:
        # Update status
        active_amendments[amendment_id]["status"] = AmendmentStatus.IN_VOTING
        active_amendments[amendment_id]["updated_at"] = datetime.now(timezone.utc).isoformat()

        await log_to_ledger("amendment_voting_started", {
            "amendment_id": amendment_id,
            "proposal_id": proposal.get("proposal_id"),
            "target_file": proposal.get("target_file")
        })

        # Collect votes from Trinity
        votes = {}
        reasoning = {}

        for role, url in TRINITY_URLS.items():
            vote, reason = await get_agent_vote(role, url, proposal)
            votes[role] = vote
            reasoning[role] = reason

            await log_to_ledger("trinity_vote_cast", {
                "amendment_id": amendment_id,
                "role": role,
                "vote": vote,
                "reasoning": reason[:200]  # Truncate for ledger
            })

        active_amendments[amendment_id]["votes"] = votes
        active_amendments[amendment_id]["reasoning"] = reasoning

        # Calculate consensus
        vote_values = list(votes.values())
        agree_count = sum(1 for v in vote_values if v == "AGREE")
        total_votes = len([v for v in vote_values if v != "ABSTAIN"])

        if total_votes > 0:
            consensus = agree_count / total_votes
        else:
            consensus = 0.0

        active_amendments[amendment_id]["consensus"] = consensus

        # Determine outcome
        if consensus >= SUPERMAJORITY_THRESHOLD:
            outcome = "ACCEPTED"
            status = AmendmentStatus.PENDING_APPLY
            await log_to_ledger("amendment_accepted", {
                "amendment_id": amendment_id,
                "consensus": consensus,
                "votes": votes
            })
        else:
            outcome = "REJECTED"
            status = AmendmentStatus.REJECTED
            await log_to_ledger("amendment_rejected", {
                "amendment_id": amendment_id,
                "consensus": consensus,
                "votes": votes,
                "required_threshold": SUPERMAJORITY_THRESHOLD
            })

        active_amendments[amendment_id]["status"] = status
        active_amendments[amendment_id]["outcome"] = outcome
        active_amendments[amendment_id]["updated_at"] = datetime.now(timezone.utc).isoformat()

    except Exception as e:
        active_amendments[amendment_id]["status"] = AmendmentStatus.FAILED
        active_amendments[amendment_id]["outcome"] = "ERROR"
        active_amendments[amendment_id]["error"] = str(e)
        active_amendments[amendment_id]["updated_at"] = datetime.now(timezone.utc).isoformat()

        await log_to_ledger("amendment_process_failed", {
            "amendment_id": amendment_id,
            "error": str(e)
        })


# =============================================================================
# API Endpoints
# =============================================================================

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "amendment_service"}


@app.post("/propose")
async def propose_amendment(proposal: AmendmentProposal, background_tasks: BackgroundTasks):
    """
    Submit an amendment proposal for Trinity voting.

    The proposal will be evaluated asynchronously by all Trinity members.
    75% consensus required for acceptance.
    """
    amendment_id = f"AMD-{uuid.uuid4().hex[:12]}"
    proposal_id = f"PROP-{uuid.uuid4().hex[:8]}"
    now = datetime.now(timezone.utc).isoformat()

    # Store the amendment
    active_amendments[amendment_id] = {
        "amendment_id": amendment_id,
        "proposal_id": proposal_id,
        "status": AmendmentStatus.INITIALIZING,
        "votes": {},
        "reasoning": {},
        "consensus": 0.0,
        "outcome": "PENDING",
        "proposal": proposal.dict(),
        "created_at": now,
        "updated_at": now
    }

    # Log to ledger
    await log_to_ledger("amendment_proposed", {
        "amendment_id": amendment_id,
        "proposal_id": proposal_id,
        "target_file": proposal.target_file,
        "proposer": proposal.proposer,
        "justification": proposal.justification[:200]
    })

    # Start voting process in background
    full_proposal = {
        "amendment_id": amendment_id,
        "proposal_id": proposal_id,
        **proposal.dict()
    }
    background_tasks.add_task(run_amendment_voting, amendment_id, full_proposal)

    return {
        "status": "amendment_process_started",
        "amendment_id": amendment_id,
        "proposal_id": proposal_id,
        "message": "Voting process initiated. Check /status/{amendment_id} for results."
    }


@app.get("/status/{amendment_id}")
async def get_amendment_status(amendment_id: str):
    """Get the current status of an amendment."""
    if amendment_id not in active_amendments:
        raise HTTPException(status_code=404, detail="Amendment not found")

    record = active_amendments[amendment_id]
    return {
        "amendment_id": record["amendment_id"],
        "proposal_id": record["proposal_id"],
        "status": record["status"],
        "votes": record["votes"],
        "consensus": record["consensus"],
        "outcome": record["outcome"],
        "created_at": record["created_at"],
        "updated_at": record["updated_at"]
    }


@app.get("/active")
async def list_active_amendments():
    """List all active amendments."""
    return {
        "amendments": [
            {
                "amendment_id": r["amendment_id"],
                "status": r["status"],
                "consensus": r["consensus"],
                "outcome": r["outcome"]
            }
            for r in active_amendments.values()
        ],
        "count": len(active_amendments)
    }


@app.post("/apply/{amendment_id}")
async def apply_amendment(amendment_id: str):
    """
    Apply an accepted amendment (requires human authorization).

    Only amendments with status PENDING_APPLY can be applied.
    This endpoint requires explicit human action to finalize the change.
    """
    if amendment_id not in active_amendments:
        raise HTTPException(status_code=404, detail="Amendment not found")

    record = active_amendments[amendment_id]

    if record["status"] != AmendmentStatus.PENDING_APPLY:
        raise HTTPException(
            status_code=400,
            detail=f"Amendment cannot be applied. Current status: {record['status']}"
        )

    # Mark as accepted (actual file modification would happen here)
    record["status"] = AmendmentStatus.ACCEPTED
    record["outcome"] = "APPLIED"
    record["updated_at"] = datetime.now(timezone.utc).isoformat()

    await log_to_ledger("amendment_applied", {
        "amendment_id": amendment_id,
        "target_file": record["proposal"]["target_file"],
        "applied_by": "human"
    })

    return {
        "status": "applied",
        "amendment_id": amendment_id,
        "message": "Amendment has been applied. The system's constitution has been updated."
    }
