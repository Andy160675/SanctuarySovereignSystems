"""
Confessor Agent - Risk assessment and audit validation
Reviews mission plans and validates compliance with governance policies
Now with FastAPI for risk assessment endpoint
"""

import json
import os
from datetime import datetime, timezone
from typing import Optional

import httpx
from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel

app = FastAPI(title="Confessor Agent", version="1.0.0")

# Configuration
AGENT_NAME = os.environ.get("AGENT_NAME", "confessor")
LEDGER_URL = os.environ.get("LEDGER_URL", "http://ledger_service:8082")
EVIDENCE_URL = os.environ.get("EVIDENCE_URL", "http://evidence_writer:8080/log")
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://ollama:11434")
MODEL_NAME = os.environ.get("MODEL_NAME", "llama3.2")


class PlanAssessmentRequest(BaseModel):
    mission_id: str
    objective: str


class RiskAssessment(BaseModel):
    risk_level: str
    rationale: str


# LLM Integration
async def call_ollama(prompt: str, system_prompt: Optional[str] = None) -> str:
    """Call local Ollama instance for risk assessment reasoning."""
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            payload = {
                "model": MODEL_NAME,
                "prompt": prompt,
                "stream": False,
            }
            if system_prompt:
                payload["system"] = system_prompt

            response = await client.post(f"{OLLAMA_URL}/api/generate", json=payload)

            if response.status_code == 200:
                return response.json().get("response", "").strip()
            return ""
    except Exception as e:
        print(f"[{AGENT_NAME}] Error calling Ollama: {e}")
        return ""


# Ledger Integration
async def write_to_ledger(entry: dict):
    """Write a risk assessment event to the ledger."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            await client.post(f"{LEDGER_URL}/append", json=entry)
    except Exception as e:
        print(f"[{AGENT_NAME}] Failed to write ledger entry: {e}")


# Evidence Logging
async def log_to_evidence(event_type: str, data: dict):
    """Log events to evidence writer."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            await client.post(
                EVIDENCE_URL,
                json={
                    "event_type": event_type,
                    "agent": AGENT_NAME,
                    "action": event_type,
                    "target": data.get("mission_id", "unknown"),
                    "outcome": data.get("risk_level", "unknown"),
                    "jurisdiction": "UK",
                    "data": data
                }
            )
    except Exception as e:
        print(f"[{AGENT_NAME}] Failed to log to evidence: {e}")


# Risk Assessment Logic
async def perform_risk_assessment(mission_id: str, objective: str) -> dict:
    """Use LLM to assess the risk level of a mission objective."""

    risk_prompt = f"""You are a risk assessment AI for a governed autonomous agent system.
Analyze the following mission objective and assign a risk score.

Consider:
- Unintended consequences
- Data exposure / privacy risk
- Policy / regulatory violations
- Potential for abuse or escalation

Respond strictly in JSON format with exactly these fields:
{{"risk_level": "LOW" or "MEDIUM" or "HIGH", "rationale": "brief explanation"}}

Mission Objective: "{objective}"

Respond with only the JSON object, no other text."""

    assessment_text = await call_ollama(risk_prompt)

    # Try to parse JSON from LLM response
    try:
        # Handle case where LLM wraps in markdown code block
        if "```" in assessment_text:
            json_start = assessment_text.find("{")
            json_end = assessment_text.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                assessment_text = assessment_text[json_start:json_end]

        assessment = json.loads(assessment_text)

        # Validate required fields
        if "risk_level" not in assessment:
            assessment["risk_level"] = "UNKNOWN"
        if "rationale" not in assessment:
            assessment["rationale"] = "No rationale provided"

        # Normalize risk level
        risk_level = assessment["risk_level"].upper()
        if risk_level not in ["LOW", "MEDIUM", "HIGH"]:
            risk_level = "UNKNOWN"
        assessment["risk_level"] = risk_level

    except json.JSONDecodeError:
        # Fallback: try to extract risk level from text
        assessment_upper = assessment_text.upper()
        if "HIGH" in assessment_upper:
            risk_level = "HIGH"
        elif "MEDIUM" in assessment_upper:
            risk_level = "MEDIUM"
        elif "LOW" in assessment_upper:
            risk_level = "LOW"
        else:
            risk_level = "UNKNOWN"

        assessment = {
            "risk_level": risk_level,
            "rationale": f"Extracted from LLM response: {assessment_text[:200]}"
        }

    return assessment


# API Endpoints
@app.get("/health")
async def health():
    return {"status": "healthy", "service": "confessor", "agent_name": AGENT_NAME}


@app.post("/assess_plan")
async def assess_plan(request: PlanAssessmentRequest):
    """
    Assess the risk level of a mission plan.
    Called by the Planner after creating a plan.
    """
    print(f"[{AGENT_NAME}] Assessing plan for mission {request.mission_id}")

    # Perform risk assessment using LLM
    assessment = await perform_risk_assessment(request.mission_id, request.objective)

    # Log to evidence
    await log_to_evidence("risk_assessment_performed", {
        "mission_id": request.mission_id,
        "objective": request.objective,
        "risk_level": assessment["risk_level"],
        "rationale": assessment["rationale"]
    })

    # Write to ledger for immutable record
    ledger_entry = {
        "event_type": "risk_assessment",
        "agent": AGENT_NAME,
        "action": "assess_plan",
        "target": request.mission_id,
        "outcome": assessment["risk_level"],
        "metadata": {
            "mission_id": request.mission_id,
            "objective": request.objective,
            "assessment": assessment,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    }
    await write_to_ledger(ledger_entry)

    print(f"[{AGENT_NAME}] Risk assessment for {request.mission_id}: {assessment['risk_level']}")

    return {
        "mission_id": request.mission_id,
        "assessment": assessment
    }


@app.get("/verify_ledger")
async def verify_ledger():
    """Verify ledger hash chain integrity."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{LEDGER_URL}/verify")
            if response.status_code == 200:
                result = response.json()
                return {"ledger_valid": result.get("valid", False)}
    except Exception as e:
        print(f"[{AGENT_NAME}] Ledger verification failed: {e}")
    return {"ledger_valid": False, "error": "Verification failed"}


class AmendmentVoteRequest(BaseModel):
    amendment_id: str
    proposal_id: str
    target_file: str
    new_content: str
    justification: str
    proposer: Optional[str] = None


class AmendmentVoteResponse(BaseModel):
    vote: str  # "AGREE", "DISAGREE", "ABSTAIN"
    reasoning: str


@app.post("/vote_on_amendment", response_model=AmendmentVoteResponse)
async def vote_on_amendment(request: AmendmentVoteRequest):
    """
    Vote on a proposed constitutional amendment.

    The Confessor evaluates amendments from a RISK perspective:
    - Does this change introduce security vulnerabilities?
    - Could this weaken audit controls or transparency?
    - Does it maintain or strengthen human oversight?
    """
    print(f"[{AGENT_NAME}] Voting on amendment {request.amendment_id}")

    vote_prompt = f"""You are the Confessor agent in a governed AI system.
You must vote on a proposed constitutional amendment.

Your role is to assess RISK - evaluate whether this change:
- Introduces security vulnerabilities
- Weakens audit controls or transparency
- Reduces human oversight capabilities
- Creates potential for abuse or escalation

Amendment Details:
- Target file: {request.target_file}
- Justification: {request.justification}
- Proposer: {request.proposer or 'unknown'}

Proposed new content (excerpt):
{request.new_content[:500]}

Respond in JSON format:
{{"vote": "AGREE" or "DISAGREE" or "ABSTAIN", "reasoning": "brief explanation"}}

Only respond with the JSON object."""

    response_text = await call_ollama(vote_prompt)

    # Parse response
    try:
        if "```" in response_text:
            json_start = response_text.find("{")
            json_end = response_text.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                response_text = response_text[json_start:json_end]

        result = json.loads(response_text)
        vote = result.get("vote", "ABSTAIN").upper()
        reasoning = result.get("reasoning", "No reasoning provided")

        if vote not in ["AGREE", "DISAGREE", "ABSTAIN"]:
            vote = "ABSTAIN"

    except json.JSONDecodeError:
        # Fallback: extract vote from text
        response_upper = response_text.upper()
        if "AGREE" in response_upper and "DISAGREE" not in response_upper:
            vote = "AGREE"
        elif "DISAGREE" in response_upper:
            vote = "DISAGREE"
        else:
            vote = "ABSTAIN"
        reasoning = f"Extracted from response: {response_text[:200]}"

    # Log the vote to ledger
    await write_to_ledger({
        "event_type": "amendment_vote",
        "agent": AGENT_NAME,
        "action": "vote_on_amendment",
        "target": request.amendment_id,
        "outcome": vote,
        "metadata": {
            "amendment_id": request.amendment_id,
            "proposal_id": request.proposal_id,
            "vote": vote,
            "reasoning": reasoning[:200]
        }
    })

    print(f"[{AGENT_NAME}] Vote on {request.amendment_id}: {vote}")

    return AmendmentVoteResponse(vote=vote, reasoning=reasoning)


@app.on_event("startup")
async def startup_event():
    """Log agent startup."""
    print(f"[{AGENT_NAME}] Starting up...")
    await log_to_evidence("agent_lifecycle", {
        "agent": AGENT_NAME,
        "action": "startup",
        "status": "success"
    })
    print(f"[{AGENT_NAME}] Confessor ready. Listening for risk assessment requests...")
