"""
Cross-Domain Synthesis Agent
============================
LLM-driven meta-analyst that consumes data from multiple sector-specific
actuators to synthesize unified, cross-domain risk assessments.

v1.0.0 - Initial release
"""

import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel


app = FastAPI(title="Cross-Domain Synthesis Agent", version="1.0.0")


# =============================================================================
# Configuration
# =============================================================================

ACTUATOR_REGISTRY_URL = os.getenv("ACTUATOR_REGISTRY_URL", "http://actuator_registry:5100")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://ollama:11434")
MODEL_NAME = os.getenv("MODEL_NAME", "llama3.2")
LEDGER_URL = os.getenv("LEDGER_URL", "http://ledger_service:8082")

# Sector to actuator capability mapping
SECTOR_CAPABILITIES = {
    "legal": ["contract_review", "policy_check", "compliance_audit"],
    "financial": ["valuation", "risk_assessment", "cost_analysis"],
    "cyber": ["threat_assessment", "vulnerability_scan", "incident_response"],
    "operational": ["resource_planning", "workflow_optimization"],
}


# =============================================================================
# Models
# =============================================================================

class SynthesisRequest(BaseModel):
    mission_prompt: str
    sectors: List[str]  # e.g., ["legal", "financial", "cyber"]
    context: Optional[Dict[str, Any]] = None


class SectorAnalysis(BaseModel):
    sector: str
    actuator_name: Optional[str] = None
    status: str  # "success", "no_actuator", "error"
    analysis: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class SynthesisReport(BaseModel):
    synthesis_id: str
    timestamp_utc: str
    mission_prompt: str
    sector_analyses: List[SectorAnalysis]
    holistic_assessment: str
    risk_level: str  # LOW, MEDIUM, HIGH, CRITICAL
    confidence: float  # 0.0 to 1.0
    recommendations: List[str]
    cross_domain_conflicts: List[str]


# =============================================================================
# Actuator Discovery and Querying
# =============================================================================

async def find_actuator_for_sector(sector: str) -> Optional[Dict]:
    """Query the actuator registry to find a service for a given sector."""
    capabilities = SECTOR_CAPABILITIES.get(sector, [])
    if not capabilities:
        return None

    async with httpx.AsyncClient(timeout=10.0) as client:
        for capability in capabilities:
            try:
                response = await client.get(
                    f"{ACTUATOR_REGISTRY_URL}/resolve/{sector}/{capability}"
                )
                if response.status_code == 200:
                    return response.json()
            except httpx.RequestError:
                continue

    return None


async def query_actuator(actuator: Dict, mission_prompt: str) -> Dict[str, Any]:
    """Query an actuator for analysis on a mission prompt."""
    endpoint = actuator.get("endpoint", "")
    if not endpoint:
        return {"status": "error", "error": "No endpoint configured"}

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            # Try the /execute endpoint with a generic analysis request
            response = await client.post(
                f"{endpoint}/execute",
                json={
                    "mission_type": "analysis",
                    "payload": {"prompt": mission_prompt}
                }
            )
            if response.status_code == 200:
                return {"status": "success", "data": response.json()}

            # Fallback: try /analyze endpoint
            response = await client.post(
                f"{endpoint}/analyze",
                json={"prompt": mission_prompt}
            )
            if response.status_code == 200:
                return {"status": "success", "data": response.json()}

            return {"status": "error", "error": f"HTTP {response.status_code}"}

        except httpx.RequestError as e:
            return {"status": "error", "error": str(e)}


# =============================================================================
# LLM Synthesis
# =============================================================================

async def synthesize_with_llm(
    mission_prompt: str,
    sector_analyses: List[SectorAnalysis]
) -> Dict[str, Any]:
    """Use LLM to synthesize cross-domain analyses into a unified assessment."""

    # Build the synthesis prompt
    analyses_text = ""
    for sa in sector_analyses:
        if sa.status == "success" and sa.analysis:
            analyses_text += f"\n### {sa.sector.upper()} Analysis (from {sa.actuator_name}):\n"
            analyses_text += json.dumps(sa.analysis, indent=2)
        else:
            analyses_text += f"\n### {sa.sector.upper()}: {sa.status}"
            if sa.error:
                analyses_text += f" - {sa.error}"

    synthesis_prompt = f"""You are a strategic risk analyst for an autonomous governance system.
Your task is to synthesize analyses from multiple specialized domains into a single, unified assessment.

## Mission Prompt
{mission_prompt}

## Sector-Specific Analyses
{analyses_text}

## Your Task
Provide a structured analysis with the following components:

1. HOLISTIC_ASSESSMENT: A concise 2-3 sentence summary of the overall risk profile considering ALL sectors.

2. RISK_LEVEL: Assign exactly one of: LOW, MEDIUM, HIGH, CRITICAL
   - LOW: No significant cross-domain risks, proceed with standard monitoring
   - MEDIUM: Some concerns requiring attention but manageable
   - HIGH: Significant risks that require mitigation before proceeding
   - CRITICAL: Severe risks that could cause system-wide impact

3. CONFIDENCE: A decimal between 0.0 and 1.0 indicating your confidence in this assessment

4. CROSS_DOMAIN_CONFLICTS: List any conflicts or tensions between sector recommendations

5. RECOMMENDATIONS: List 3-5 actionable recommendations considering all domains

Format your response as JSON:
{{
  "holistic_assessment": "...",
  "risk_level": "...",
  "confidence": 0.X,
  "cross_domain_conflicts": ["...", "..."],
  "recommendations": ["...", "...", "..."]
}}"""

    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.post(
                f"{OLLAMA_URL}/api/generate",
                json={
                    "model": MODEL_NAME,
                    "prompt": synthesis_prompt,
                    "stream": False,
                    "options": {"temperature": 0.3}
                }
            )

            if response.status_code != 200:
                return get_fallback_synthesis()

            result = response.json()
            llm_text = result.get("response", "")

            # Try to parse JSON from response
            try:
                # Find JSON block in response
                start = llm_text.find("{")
                end = llm_text.rfind("}") + 1
                if start >= 0 and end > start:
                    return json.loads(llm_text[start:end])
            except json.JSONDecodeError:
                pass

            return get_fallback_synthesis(llm_text)

        except httpx.RequestError:
            return get_fallback_synthesis()


def get_fallback_synthesis(raw_text: str = "") -> Dict[str, Any]:
    """Return a fallback synthesis when LLM parsing fails."""
    return {
        "holistic_assessment": raw_text or "Synthesis unavailable - manual review required",
        "risk_level": "MEDIUM",
        "confidence": 0.5,
        "cross_domain_conflicts": [],
        "recommendations": [
            "Conduct manual review of sector analyses",
            "Verify actuator connectivity",
            "Retry synthesis with updated data"
        ]
    }


# =============================================================================
# Ledger Logging
# =============================================================================

async def log_synthesis_event(report: SynthesisReport) -> None:
    """Log synthesis event to the immutable ledger."""
    async with httpx.AsyncClient(timeout=5.0) as client:
        try:
            await client.post(
                f"{LEDGER_URL}/append",
                json={
                    "event_type": "cross_domain_synthesis",
                    "agent": "synthesis_agent",
                    "timestamp_utc": report.timestamp_utc,
                    "details": {
                        "synthesis_id": report.synthesis_id,
                        "mission_prompt": report.mission_prompt[:200],
                        "sectors": [sa.sector for sa in report.sector_analyses],
                        "risk_level": report.risk_level,
                        "confidence": report.confidence
                    }
                }
            )
        except httpx.RequestError:
            print("[synthesis_agent] Failed to log to ledger")


# =============================================================================
# Core Synthesis Logic
# =============================================================================

async def run_synthesis(request: SynthesisRequest) -> SynthesisReport:
    """Orchestrate the cross-domain synthesis process."""
    import uuid

    synthesis_id = str(uuid.uuid4())[:8]
    timestamp = datetime.now(timezone.utc).isoformat()
    sector_analyses: List[SectorAnalysis] = []

    # 1. Gather analyses from each requested sector
    for sector in request.sectors:
        actuator = await find_actuator_for_sector(sector)

        if not actuator:
            sector_analyses.append(SectorAnalysis(
                sector=sector,
                status="no_actuator",
                error="No actuator registered for this sector"
            ))
            continue

        result = await query_actuator(actuator, request.mission_prompt)

        if result["status"] == "success":
            sector_analyses.append(SectorAnalysis(
                sector=sector,
                actuator_name=actuator.get("name", "unknown"),
                status="success",
                analysis=result.get("data")
            ))
        else:
            sector_analyses.append(SectorAnalysis(
                sector=sector,
                actuator_name=actuator.get("name"),
                status="error",
                error=result.get("error")
            ))

    # 2. Use LLM to synthesize results
    synthesis = await synthesize_with_llm(request.mission_prompt, sector_analyses)

    # 3. Build report
    report = SynthesisReport(
        synthesis_id=synthesis_id,
        timestamp_utc=timestamp,
        mission_prompt=request.mission_prompt,
        sector_analyses=sector_analyses,
        holistic_assessment=synthesis.get("holistic_assessment", ""),
        risk_level=synthesis.get("risk_level", "MEDIUM"),
        confidence=float(synthesis.get("confidence", 0.5)),
        recommendations=synthesis.get("recommendations", []),
        cross_domain_conflicts=synthesis.get("cross_domain_conflicts", [])
    )

    # 4. Log to ledger
    await log_synthesis_event(report)

    return report


# =============================================================================
# API Endpoints
# =============================================================================

@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy", "service": "synthesis_agent"}


@app.post("/synthesize", response_model=SynthesisReport)
async def create_synthesis_report(request: SynthesisRequest):
    """
    Generate a cross-domain synthesis report for a given mission.

    This endpoint:
    1. Queries registered actuators for each requested sector
    2. Aggregates their analyses
    3. Uses an LLM to synthesize a unified risk assessment
    4. Logs the synthesis event to the immutable ledger
    """
    if not request.sectors:
        raise HTTPException(
            status_code=400,
            detail="At least one sector must be specified"
        )

    valid_sectors = set(SECTOR_CAPABILITIES.keys())
    invalid = [s for s in request.sectors if s not in valid_sectors]
    if invalid:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid sectors: {invalid}. Valid sectors: {list(valid_sectors)}"
        )

    report = await run_synthesis(request)
    return report


@app.get("/sectors")
async def list_sectors():
    """List available sectors and their capabilities."""
    return {
        "sectors": SECTOR_CAPABILITIES,
        "description": "Each sector maps to a set of actuator capabilities"
    }


@app.on_event("startup")
async def startup_event():
    """Log service startup."""
    print("[synthesis_agent] Starting up...")
    print(f"[synthesis_agent] Actuator registry: {ACTUATOR_REGISTRY_URL}")
    print(f"[synthesis_agent] LLM: {OLLAMA_URL} ({MODEL_NAME})")
    print("[synthesis_agent] Ready to synthesize cross-domain analyses")
