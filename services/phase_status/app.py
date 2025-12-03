"""
Phase Status API
================
Provides real-time phase status, governance state, and claims validation
for the Sovereign System dashboard and external consumers.

v1.0.0 - Initial release
"""

import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

import yaml
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel


app = FastAPI(title="Phase Status API", version="1.0.0")


# =============================================================================
# Configuration
# =============================================================================

# In Docker, governance files are mounted at /governance
GOVERNANCE_ROOT = Path(os.getenv("GOVERNANCE_ROOT", "/governance"))
ARTIFACTS_ROOT = Path(os.getenv("ARTIFACTS_ROOT", "/artifacts"))
CLAIMS_ROOT = Path(os.getenv("CLAIMS_ROOT", "/claims"))

# Cache configuration
CACHE_TTL_SECONDS = 30
_status_cache: Dict = {"data": None, "timestamp": 0}


# =============================================================================
# Models
# =============================================================================

class PhaseInfo(BaseModel):
    phase_number: int
    name: str
    description: str
    allowed_capabilities: List[str]
    forbidden_capabilities: List[str]
    exit_tests: List[str]


class GovernanceStatus(BaseModel):
    constitution_version: str
    active_phase: int
    core_principles_count: int
    trinity_agents: List[str]
    kill_switch_enabled: bool


class ClaimsStatus(BaseModel):
    total_claims: int
    verified_count: int
    prohibited_count: int
    invalid_count: int
    verified: List[str]
    invalid: List[Dict]


class ExitTestStatus(BaseModel):
    name: str
    status: str  # "pass" | "fail" | "pending"
    last_run: Optional[str] = None


class SystemStatus(BaseModel):
    active_phase: int
    phase_info: Optional[PhaseInfo]
    governance: Optional[GovernanceStatus]
    claims: Optional[ClaimsStatus]
    exit_tests: List[ExitTestStatus]
    last_updated: str


# =============================================================================
# Data Loading
# =============================================================================

def load_active_phase() -> int:
    """Load the active phase number."""
    phase_file = GOVERNANCE_ROOT / "ACTIVE_PHASE"
    if phase_file.exists():
        return int(phase_file.read_text().strip())
    return 0


def load_phase_info(phase_num: int) -> Optional[PhaseInfo]:
    """Load phase definition."""
    phase_file = GOVERNANCE_ROOT / "phases" / f"phase{phase_num}.yaml"
    if not phase_file.exists():
        return None

    try:
        data = yaml.safe_load(phase_file.read_text())
        return PhaseInfo(
            phase_number=data.get("phase", phase_num),
            name=data.get("name", f"Phase {phase_num}"),
            description=data.get("description", ""),
            allowed_capabilities=data.get("allowed_capabilities", []),
            forbidden_capabilities=data.get("forbidden_capabilities", []),
            exit_tests=data.get("automated_exit_tests", []),
        )
    except Exception:
        return None


def load_governance_status() -> Optional[GovernanceStatus]:
    """Load governance configuration status."""
    config_file = GOVERNANCE_ROOT / "governance_config.yaml"
    if not config_file.exists():
        return None

    try:
        data = yaml.safe_load(config_file.read_text())
        return GovernanceStatus(
            constitution_version=data.get("constitution_version", "unknown"),
            active_phase=data.get("phases", {}).get("active", 0),
            core_principles_count=len(data.get("core_principles", [])),
            trinity_agents=data.get("trinity", {}).get("agents", []),
            kill_switch_enabled=data.get("kill_switch", {}).get("enabled", False),
        )
    except Exception:
        return None


def load_claims_status() -> Optional[ClaimsStatus]:
    """Load claims validation report."""
    report_file = ARTIFACTS_ROOT / "claims_report.json"
    if not report_file.exists():
        # Try to generate from claims.yaml
        claims_file = CLAIMS_ROOT / "claims.yaml"
        if claims_file.exists():
            return ClaimsStatus(
                total_claims=0,
                verified_count=0,
                prohibited_count=0,
                invalid_count=0,
                verified=[],
                invalid=[],
            )
        return None

    try:
        data = json.loads(report_file.read_text())
        return ClaimsStatus(
            total_claims=data.get("total_claims", 0),
            verified_count=data.get("verified_count", 0),
            prohibited_count=data.get("prohibited_count", 0),
            invalid_count=data.get("invalid_count", 0),
            verified=data.get("verified", []),
            invalid=data.get("invalid", []),
        )
    except Exception:
        return None


def get_exit_test_statuses(phase_info: Optional[PhaseInfo]) -> List[ExitTestStatus]:
    """Get status of exit tests for current phase."""
    if not phase_info:
        return []

    statuses = []
    for test_name in phase_info.exit_tests:
        # Check if test script exists
        # For now, mark as "pending" if no execution record
        statuses.append(ExitTestStatus(
            name=test_name,
            status="pending",
            last_run=None,
        ))

    return statuses


# =============================================================================
# API Endpoints
# =============================================================================

@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy", "service": "phase_status"}


@app.get("/status", response_model=SystemStatus)
async def get_status():
    """
    Get comprehensive system status with caching.
    """
    now = time.time()
    if _status_cache["data"] and (now - _status_cache["timestamp"] < CACHE_TTL_SECONDS):
        return _status_cache["data"]

    try:
        active_phase = load_active_phase()
        phase_info = load_phase_info(active_phase)
        governance = load_governance_status()
        claims = load_claims_status()
        exit_tests = get_exit_test_statuses(phase_info)

        status = SystemStatus(
            active_phase=active_phase,
            phase_info=phase_info,
            governance=governance,
            claims=claims,
            exit_tests=exit_tests,
            last_updated=datetime.now(timezone.utc).isoformat(),
        )

        _status_cache["data"] = status
        _status_cache["timestamp"] = now

        return status

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load status: {e}")


@app.get("/phase/{phase_num}", response_model=PhaseInfo)
async def get_phase(phase_num: int):
    """Get details of a specific phase."""
    phase_info = load_phase_info(phase_num)
    if not phase_info:
        raise HTTPException(status_code=404, detail=f"Phase {phase_num} not found")
    return phase_info


@app.get("/governance", response_model=GovernanceStatus)
async def get_governance():
    """Get governance configuration status."""
    governance = load_governance_status()
    if not governance:
        raise HTTPException(status_code=404, detail="Governance config not found")
    return governance


@app.get("/claims", response_model=ClaimsStatus)
async def get_claims():
    """Get claims validation status."""
    claims = load_claims_status()
    if not claims:
        raise HTTPException(status_code=404, detail="Claims report not found")
    return claims


@app.get("/capabilities")
async def get_capabilities():
    """Get allowed and forbidden capabilities for current phase."""
    active_phase = load_active_phase()
    phase_info = load_phase_info(active_phase)

    if not phase_info:
        raise HTTPException(status_code=404, detail="Phase info not found")

    return {
        "active_phase": active_phase,
        "allowed": phase_info.allowed_capabilities,
        "forbidden": phase_info.forbidden_capabilities,
    }


@app.on_event("startup")
async def startup_event():
    """Log service startup."""
    print("[phase_status] Starting up...")
    print(f"[phase_status] Governance root: {GOVERNANCE_ROOT}")
    print(f"[phase_status] Artifacts root: {ARTIFACTS_ROOT}")
    print(f"[phase_status] Claims root: {CLAIMS_ROOT}")
    print("[phase_status] Ready to serve phase status requests")
