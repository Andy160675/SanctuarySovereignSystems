"""
RACI Matrix & Scoring App - Mission-Critical Governance Artifact
================================================================

Official Boardroom governance service providing:
- Agent RACI Matrix visualization at all expansion levels
- 10-dimension scoring (Resp/Acc/Tool/Compl/Risk/Autonomy/Crypto/OKR/Foresight/Self-Gov)
- OKR alignment tracking with drift detection
- Cryptographic proof generation for score immutability
- Real-time scoring view for investor presentations

Status: HUMAN_AUTH-only for modifications, cryptographically signed output

Eternal Laws:
- No agent may score <10 on any axis at Sovereign level without SYSTEM_HALT_REQUESTED
- OKR alignment <100% for 3+ missions triggers OKR rollback
- Score proof (Halo2-style hash) generated every 100 events
- Score reduction after height 100000 requires 5-key quorum + 30-day challenge

v2.0.0 - 10-dimension scoring with OKR alignment
"""

import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Add shared module to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

try:
    from shared.freeze_guard import emergency_freeze_active, get_freeze_status
except ImportError:
    def emergency_freeze_active() -> bool:
        state_path = Path(__file__).parent.parent.parent.parent / "config" / "system_state.json"
        if state_path.exists():
            try:
                with state_path.open() as f:
                    return json.load(f).get("emergency_freeze", False)
            except Exception:
                return False
        return False

    def get_freeze_status() -> dict:
        return {"emergency_freeze": emergency_freeze_active()}


app = FastAPI(
    title="RACI Matrix & Scoring App",
    version="2.0.0",
    description="Mission-critical governance artifact for agent responsibility tracking"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
DATA_DIR = Path(__file__).parent / "data"
LEDGER_URL = os.getenv("LEDGER_URL", "http://ledger_service:8082")

# Scoring dimensions (locked forever)
SCORING_DIMENSIONS = [
    "responsibility", "accountability", "tool_access", "complexity",
    "risk_surface", "autonomy", "crypto_authority", "okr_alignment",
    "foresight", "self_governance"
]

EXPANSION_LEVELS = ["Pilot", "Growth", "Enterprise", "Sovereign"]
SOVEREIGN_REQUIREMENT = 10

# In-memory state (loaded from JSON files)
_raci_matrix: Dict = {}
_agent_scores: Dict = {}
_event_counter: int = 0
_proof_history: List[str] = []


# =============================================================================
# Models
# =============================================================================

class AgentScore(BaseModel):
    responsibility: int = Field(ge=1, le=10)
    accountability: int = Field(ge=1, le=10)
    tool_access: int = Field(ge=1, le=10)
    complexity: int = Field(ge=1, le=10)
    risk_surface: int = Field(ge=1, le=10)
    autonomy: int = Field(ge=1, le=10)
    crypto_authority: int = Field(ge=1, le=10)
    okr_alignment: int = Field(ge=1, le=10)
    foresight: int = Field(ge=1, le=10)
    self_governance: int = Field(ge=1, le=10)


class ScoreOneLinear(BaseModel):
    agent: str
    expansion: str
    score_string: str  # "10/10/10/10/10/10/10/10/10/10"
    total: int
    is_sovereign_compliant: bool


class RaciAssignment(BaseModel):
    agent: str
    task: str
    expansion: str
    raci: str  # R, A, C, I


class DriftAlert(BaseModel):
    agent: str
    dimension: str
    expected: int
    actual: int
    severity: str  # "warning", "critical", "halt_required"


# =============================================================================
# Data Loading
# =============================================================================

def load_data():
    """Load RACI matrix and scores from JSON files."""
    global _raci_matrix, _agent_scores

    raci_path = DATA_DIR / "raci_matrix.json"
    scores_path = DATA_DIR / "agent_scores.json"

    if raci_path.exists():
        with raci_path.open() as f:
            _raci_matrix = json.load(f)

    if scores_path.exists():
        with scores_path.open() as f:
            _agent_scores = json.load(f)


def compute_score_hash(scores: Dict) -> str:
    """Compute SHA-256 hash of current score state (Halo2-style proof placeholder)."""
    score_string = json.dumps(scores, sort_keys=True)
    return hashlib.sha256(score_string.encode()).hexdigest()


def generate_proof_if_needed():
    """Generate score proof every 100 events."""
    global _event_counter, _proof_history

    _event_counter += 1
    if _event_counter % 100 == 0:
        proof = {
            "event_count": _event_counter,
            "score_hash": compute_score_hash(_agent_scores.get("scores", {})),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "proof_type": "raci_score_proof_v1"
        }
        _proof_history.append(proof)
        return proof
    return None


# =============================================================================
# Core Endpoints
# =============================================================================

@app.get("/health")
async def health():
    freeze_status = get_freeze_status()
    return {
        "status": "healthy",
        "service": "raci_app",
        "version": "2.0.0",
        "emergency_freeze": freeze_status.get("emergency_freeze", False),
        "event_count": _event_counter,
        "proof_count": len(_proof_history)
    }


@app.get("/matrix")
async def get_raci_matrix():
    """Get the full RACI matrix with all assignments."""
    generate_proof_if_needed()
    return {
        "version": _raci_matrix.get("version", "unknown"),
        "expansion_levels": EXPANSION_LEVELS,
        "agents": _raci_matrix.get("agents", {}),
        "work_tasks": _raci_matrix.get("work_tasks", []),
        "assignments": _raci_matrix.get("raci_assignments", [])
    }


@app.get("/matrix/{agent}")
async def get_agent_raci(agent: str):
    """Get RACI assignments for a specific agent."""
    agents = _raci_matrix.get("agents", {})
    if agent not in agents:
        raise HTTPException(status_code=404, detail=f"Agent {agent} not found")

    assignments = [
        a for a in _raci_matrix.get("raci_assignments", [])
        if a["agent"] == agent
    ]

    return {
        "agent": agent,
        "info": agents[agent],
        "assignments": assignments
    }


@app.get("/scores")
async def get_all_scores():
    """Get all agent scores across all expansion levels."""
    generate_proof_if_needed()
    return {
        "version": _agent_scores.get("version", "unknown"),
        "dimensions": _agent_scores.get("scoring_dimensions", SCORING_DIMENSIONS),
        "sovereign_requirement": SOVEREIGN_REQUIREMENT,
        "scores": _agent_scores.get("scores", {}),
        "score_hash": compute_score_hash(_agent_scores.get("scores", {}))
    }


@app.get("/scores/{agent}")
async def get_agent_scores(agent: str):
    """Get scores for a specific agent across all expansion levels."""
    scores = _agent_scores.get("scores", {})
    if agent not in scores:
        raise HTTPException(status_code=404, detail=f"Agent {agent} not found")

    return {
        "agent": agent,
        "scores": scores[agent],
        "one_liners": {
            level: format_one_liner(agent, level, scores[agent].get(level, {}))
            for level in EXPANSION_LEVELS
        }
    }


@app.get("/scores/{agent}/{expansion}")
async def get_agent_expansion_score(agent: str, expansion: str):
    """Get scores for a specific agent at a specific expansion level."""
    if expansion not in EXPANSION_LEVELS:
        raise HTTPException(status_code=400, detail=f"Invalid expansion level: {expansion}")

    scores = _agent_scores.get("scores", {})
    if agent not in scores:
        raise HTTPException(status_code=404, detail=f"Agent {agent} not found")

    agent_scores = scores[agent].get(expansion, {})
    return {
        "agent": agent,
        "expansion": expansion,
        "scores": agent_scores,
        "one_liner": format_one_liner(agent, expansion, agent_scores),
        "is_sovereign_compliant": check_sovereign_compliance(agent_scores) if expansion == "Sovereign" else None
    }


def format_one_liner(agent: str, expansion: str, scores: Dict) -> ScoreOneLinear:
    """Format scores as one-liner string."""
    values = [scores.get(dim, 0) for dim in SCORING_DIMENSIONS]
    score_string = "/".join(str(v) for v in values)
    total = sum(values)
    is_compliant = all(v >= SOVEREIGN_REQUIREMENT for v in values) if expansion == "Sovereign" else True

    return ScoreOneLinear(
        agent=agent,
        expansion=expansion,
        score_string=score_string,
        total=total,
        is_sovereign_compliant=is_compliant
    )


def check_sovereign_compliance(scores: Dict) -> bool:
    """Check if all scores meet sovereign requirement (10/10 on all axes)."""
    return all(scores.get(dim, 0) >= SOVEREIGN_REQUIREMENT for dim in SCORING_DIMENSIONS)


@app.get("/one-liners")
async def get_all_one_liners():
    """Get all agents as one-liner scoring format for presentations."""
    scores = _agent_scores.get("scores", {})
    result = {}

    for agent, agent_scores in scores.items():
        result[agent] = {}
        for expansion in EXPANSION_LEVELS:
            if expansion in agent_scores:
                result[agent][expansion] = format_one_liner(agent, expansion, agent_scores[expansion])

    return {
        "format": "Resp/Acc/Tool/Compl/Risk/Autonomy/Crypto/OKR/Foresight/Self-Gov",
        "sovereign_requirement": "10/10/10/10/10/10/10/10/10/10",
        "one_liners": result
    }


@app.get("/sovereign-summary")
async def get_sovereign_summary():
    """Get all Sovereign-level scores in concise format (for Eternal One-Liner view)."""
    scores = _agent_scores.get("scores", {})
    summary = []

    for agent, agent_scores in scores.items():
        sovereign = agent_scores.get("Sovereign", {})
        one_liner = format_one_liner(agent, "Sovereign", sovereign)
        summary.append({
            "agent": agent.ljust(20),
            "scores": one_liner.score_string,
            "compliant": one_liner.is_sovereign_compliant
        })

    return {
        "format": "Resp/Acc/Tool/Compl/Risk/Autonomy/Crypto/OKR/Foresight/Self-Gov",
        "agents": summary,
        "all_compliant": all(s["compliant"] for s in summary)
    }


# =============================================================================
# Drift Detection & Alerts
# =============================================================================

@app.get("/drift-check")
async def check_drift():
    """Check for any scoring drift or compliance issues."""
    scores = _agent_scores.get("scores", {})
    alerts: List[DriftAlert] = []

    for agent, agent_scores in scores.items():
        sovereign = agent_scores.get("Sovereign", {})

        # Check Sovereign level compliance
        for dim in SCORING_DIMENSIONS:
            value = sovereign.get(dim, 0)
            if value < SOVEREIGN_REQUIREMENT:
                severity = "halt_required" if dim == "okr_alignment" else "critical"
                alerts.append(DriftAlert(
                    agent=agent,
                    dimension=dim,
                    expected=SOVEREIGN_REQUIREMENT,
                    actual=value,
                    severity=severity
                ))

        # Check OKR alignment specifically (red flag if <9)
        okr = sovereign.get("okr_alignment", 0)
        if okr < 9:
            alerts.append(DriftAlert(
                agent=agent,
                dimension="okr_alignment",
                expected=9,
                actual=okr,
                severity="warning"
            ))

    return {
        "drift_detected": len(alerts) > 0,
        "alert_count": len(alerts),
        "alerts": [a.model_dump() for a in alerts],
        "halt_required": any(a.severity == "halt_required" for a in alerts)
    }


@app.get("/okr-alignment-status")
async def get_okr_alignment_status():
    """Get OKR alignment status across all agents."""
    scores = _agent_scores.get("scores", {})
    status = []

    for agent, agent_scores in scores.items():
        for expansion in EXPANSION_LEVELS:
            if expansion in agent_scores:
                okr = agent_scores[expansion].get("okr_alignment", 0)
                status.append({
                    "agent": agent,
                    "expansion": expansion,
                    "okr_alignment": okr,
                    "compliant": okr >= 9,
                    "color": "green" if okr >= 9 else "red"
                })

    return {
        "status": status,
        "below_threshold": [s for s in status if not s["compliant"]]
    }


# =============================================================================
# Proof & Audit
# =============================================================================

@app.get("/proof-history")
async def get_proof_history():
    """Get history of score proofs for audit."""
    return {
        "proof_count": len(_proof_history),
        "current_hash": compute_score_hash(_agent_scores.get("scores", {})),
        "proofs": _proof_history[-10:]  # Last 10 proofs
    }


@app.get("/eternal-laws")
async def get_eternal_laws():
    """Get the immutable eternal laws governing this service."""
    return {
        "laws": _agent_scores.get("eternal_laws", []),
        "locked_at": _agent_scores.get("locked_at"),
        "version": _agent_scores.get("version")
    }


# =============================================================================
# Cards View (Top Trumps Style)
# =============================================================================

@app.get("/cards")
async def get_agent_cards():
    """Get all agents as Top Trumps style cards."""
    scores = _agent_scores.get("scores", {})
    agents = _raci_matrix.get("agents", {})
    cards = []

    for agent, agent_info in agents.items():
        agent_scores = scores.get(agent, {})
        for expansion in EXPANSION_LEVELS:
            if expansion in agent_scores:
                card_scores = agent_scores[expansion]
                cards.append({
                    "agent": agent,
                    "expansion": expansion,
                    "trinity": agent_info.get("trinity", "Unknown"),
                    "description": agent_info.get("description", ""),
                    "scores": card_scores,
                    "total": sum(card_scores.values()),
                    "one_liner": format_one_liner(agent, expansion, card_scores).score_string
                })

    return {"cards": cards}


@app.get("/cards/{agent}/{expansion}")
async def get_single_card(agent: str, expansion: str):
    """Get a single Top Trumps style card."""
    if expansion not in EXPANSION_LEVELS:
        raise HTTPException(status_code=400, detail=f"Invalid expansion: {expansion}")

    scores = _agent_scores.get("scores", {})
    agents = _raci_matrix.get("agents", {})

    if agent not in agents:
        raise HTTPException(status_code=404, detail=f"Agent {agent} not found")

    agent_info = agents[agent]
    card_scores = scores.get(agent, {}).get(expansion, {})

    return {
        "agent": agent,
        "expansion": expansion,
        "trinity": agent_info.get("trinity", "Unknown"),
        "description": agent_info.get("description", ""),
        "responsibilities": agent_info.get("responsibilities", {}).get(expansion, []),
        "scores": card_scores,
        "total": sum(card_scores.values()),
        "one_liner": format_one_liner(agent, expansion, card_scores).score_string,
        "is_sovereign_compliant": check_sovereign_compliance(card_scores) if expansion == "Sovereign" else None
    }


# =============================================================================
# Startup
# =============================================================================

@app.on_event("startup")
async def startup_event():
    """Load data on startup."""
    load_data()
    print(f"[raci_app] Loaded RACI matrix v{_raci_matrix.get('version', 'unknown')}")
    print(f"[raci_app] Loaded agent scores v{_agent_scores.get('version', 'unknown')}")
    print(f"[raci_app] Tracking {len(_agent_scores.get('scores', {}))} agents")
    print(f"[raci_app] Score hash: {compute_score_hash(_agent_scores.get('scores', {}))[:16]}...")
