#!/usr/bin/env python3
"""
Sovereign System - Mock Services (Phase 5E)
============================================
Simulates all backend services for demo/testing with LOCAL SUBSTRATE VERIFICATION.

Single process runs:
- Aggregated health endpoint on 8502 (for Boardroom UI)
- Individual service mocks on 8001-8005 (for direct testing)
- Evidence tree with SHA-256 hash verification (tamper detection)

Run:
  pip install fastapi uvicorn
  python mock_services.py

Then start Boardroom:
  cd boardroom && streamlit run boardroom_app.py --server.port 8501

Phase 5E Features:
- Evidence store at ./evidence_store/CASE-TEST-001/
- SHA-256 hash computation for tamper detection
- /api/core/verify_hash endpoint for integrity checks
- /api/truth/search returns evidence_path + event_hash
"""
import random
import threading
import time
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# =============================================================================
# SERVICE DEFINITIONS
# =============================================================================

SERVICES = {
    "core": {"port": 8001, "name": "Sovereign Core", "latency_range": (8, 25)},
    "truth": {"port": 8002, "name": "Truth Engine", "latency_range": (10, 35)},
    "enforce": {"port": 8003, "name": "Enforcement API", "latency_range": (5, 20)},
    "models": {"port": 8004, "name": "Models / Ollama", "latency_range": (15, 50)},
    "rag_index": {"port": 8005, "name": "RAG Index", "latency_range": (12, 40)},
}

# Track uptime
START_TIME = datetime.utcnow()

# =============================================================================
# PHASE 5E: EVIDENCE STORE & HASH VERIFICATION
# =============================================================================

ROOT = Path(__file__).parent.resolve()
EVIDENCE_ROOT = ROOT / "evidence_store"
CASE_ID = "CASE-TEST-001"
CASE_DIR = EVIDENCE_ROOT / CASE_ID
MOCK_FILE = CASE_DIR / "mock-event-1.jsonl"

# Deterministic mock event content
MOCK_EVENT = {
    "id": "mock-event-1",
    "case_id": CASE_ID,
    "ts": datetime.now(timezone.utc).isoformat(),
    "type": "evidence",
    "payload": {
        "text": "This is a tamper-test artifact. Change this file to see mismatch behavior."
    }
}


def hash_file(filepath: Path) -> str:
    """Compute SHA-256 hash of a file."""
    h = hashlib.sha256()
    with filepath.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def ensure_evidence() -> str:
    """
    Ensure evidence_store/CASE-TEST-001/mock-event-1.jsonl exists
    and return its SHA256 checksum (hex).
    """
    CASE_DIR.mkdir(parents=True, exist_ok=True)

    # Only write if doesn't exist (preserve tamper tests)
    if not MOCK_FILE.exists():
        with MOCK_FILE.open("w", encoding="utf-8") as f:
            f.write(json.dumps(MOCK_EVENT, sort_keys=True) + "\n")

    return hash_file(MOCK_FILE)


# Create evidence and get checksum at module import
EVIDENCE_CHECKSUM = ensure_evidence()


# Pydantic models for API requests
class VerifyHashRequest(BaseModel):
    evidence_path: str
    expected_hash: str


class TruthSearchRequest(BaseModel):
    query: str
    limit: Optional[int] = 10


def get_uptime_seconds() -> float:
    return (datetime.utcnow() - START_TIME).total_seconds()


# =============================================================================
# INDIVIDUAL SERVICE APPS
# =============================================================================

def create_service_app(service_key: str, service_config: Dict) -> FastAPI:
    """Create a FastAPI app for a single mock service."""
    app = FastAPI(title=service_config["name"], version="1.0.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get(f"/health/{service_key}")
    def health():
        low, high = service_config["latency_range"]
        return {
            "status": "healthy",
            "latency_ms": random.randint(low, high),
            "version": "1.0.0",
            "uptime_s": get_uptime_seconds(),
            "details": {
                "service": service_config["name"],
                "port": service_config["port"]
            }
        }

    @app.get("/")
    def root():
        return {"service": service_config["name"], "status": "ok"}

    return app


# =============================================================================
# AGGREGATED BACKEND (Port 8502)
# =============================================================================

aggregated_app = FastAPI(title="Sovereign Aggregated Backend", version="1.0.0")

aggregated_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@aggregated_app.get("/health")
def aggregated_health():
    """Return aggregated health status for all services."""
    services_status = {}
    for key, config in SERVICES.items():
        low, high = config["latency_range"]
        services_status[config["name"]] = {
            "status": "healthy",
            "endpoint": f"http://localhost:{config['port']}",
            "latency_ms": random.randint(low, high)
        }

    return {
        "overall_status": "healthy",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "uptime_s": get_uptime_seconds(),
        "checks": {
            "env_file": {
                "status": "pass",
                "message": ".env file configured correctly"
            },
            "services_running": {
                "status": "pass",
                "message": f"All {len(SERVICES)} core services running"
            },
            "ollama_model": {
                "status": "pass",
                "message": "llama3.2:latest available"
            },
            "truth_index": {
                "status": "pass",
                "message": "1,247 documents indexed"
            }
        },
        "services": services_status
    }


@aggregated_app.post("/actions/index_truth")
def index_truth(payload: Dict[str, Any] = None):
    """Trigger truth indexer (mock)."""
    return {
        "status": "success",
        "message": "Indexer triggered successfully",
        "job_id": f"IDX-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
        "documents_queued": random.randint(25, 100),
        "estimated_time_s": random.randint(15, 60)
    }


@aggregated_app.post("/core/analyze")
def core_analyze(payload: Dict[str, Any] = None):
    """Mock core analysis endpoint."""
    text = payload.get("text", "") if payload else ""
    return {
        "status": "success",
        "risk_level": random.choice(["low", "medium", "high"]),
        "violations": [],
        "policies_checked": 12,
        "analysis_time_ms": random.randint(50, 200),
        "text_length": len(text)
    }


@aggregated_app.post("/truth/search")
def truth_search(payload: Dict[str, Any] = None):
    """Mock truth search endpoint - returns evidence with hash for verification."""
    query = payload.get("query", "") if payload else ""

    # Include the real evidence file in results when query matches
    results = []
    if query and (CASE_ID.lower() in query.lower() or "evidence" in query.lower() or "test" in query.lower()):
        # Return real evidence with verifiable hash
        results.append({
            "id": "mock-event-1",
            "score": 0.99,
            "snippet": MOCK_EVENT["payload"]["text"],
            "source": "evidence_store",
            "evidence_path": str(MOCK_FILE.resolve()),
            "event_hash": EVIDENCE_CHECKSUM,
            "timestamp": MOCK_EVENT["ts"]
        })

    # Add some random mock results
    for i in range(random.randint(2, 5)):
        results.append({
            "id": f"DOC-{i:04d}",
            "score": round(random.uniform(0.7, 0.95), 3),
            "snippet": f"Sample result {i} matching '{query[:20]}...'",
            "source": random.choice(["policy", "knowledge"]),
            "evidence_path": None,
            "event_hash": None
        })

    return {
        "status": "success",
        "query": query,
        "results": results,
        "total_matches": len(results),
        "search_time_ms": random.randint(15, 80)
    }


@aggregated_app.post("/api/core/verify_hash")
def verify_hash(request: VerifyHashRequest):
    """Phase 5E: Verify evidence file hash - tamper detection endpoint."""
    evidence_path = request.evidence_path
    expected_hash = request.expected_hash

    p = Path(evidence_path)
    if not p.exists():
        return {
            "ok": False,
            "error": "file not found",
            "path": str(p),
            "match": False
        }

    actual_hash = hash_file(p)
    match = (actual_hash == expected_hash)

    return {
        "ok": True,
        "match": match,
        "actual": actual_hash,
        "expected": expected_hash,
        "path": str(p),
        "verified_at": datetime.utcnow().isoformat() + "Z"
    }


@aggregated_app.get("/api/evidence/info")
def evidence_info():
    """Return info about the evidence store for UI display."""
    return {
        "evidence_root": str(EVIDENCE_ROOT),
        "case_id": CASE_ID,
        "mock_file": str(MOCK_FILE.resolve()),
        "current_hash": hash_file(MOCK_FILE) if MOCK_FILE.exists() else None,
        "original_hash": EVIDENCE_CHECKSUM,
        "tampered": hash_file(MOCK_FILE) != EVIDENCE_CHECKSUM if MOCK_FILE.exists() else None
    }


@aggregated_app.post("/enforce/action")
def enforce_action(payload: Dict[str, Any] = None):
    """Mock enforcement action endpoint."""
    action = payload.get("action", "flag") if payload else "flag"
    return {
        "status": "success",
        "action": action,
        "reference": f"ENF-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
        "executed_at": datetime.utcnow().isoformat() + "Z",
        "details": {
            "action_type": action,
            "reversible": action != "redact"
        }
    }


# =============================================================================
# PHASE 5E+: LLM RUSSIAN DOLL ENDPOINT (for DollAgent)
# =============================================================================

class LlmAnalyzeRequest(BaseModel):
    run_id: str = "unknown-run"
    case_id: str = "unknown-case"
    stats: Optional[Dict[str, Any]] = None
    prompt: Optional[str] = None


@aggregated_app.post("/api/llm/analyze")
def llm_analyze(request: LlmAnalyzeRequest):
    """
    Mock LLM "Russian doll" analysis endpoint.

    Expects JSON:
      {
        "run_id": "...",
        "case_id": "...",
        "stats": { "evidence_count": int, "mismatch_count": int },
        "prompt": "free text"
      }

    Returns nested analysis:
      inner_summary, risk_lens, outer_commentary, meta
    """
    run_id = request.run_id
    case_id = request.case_id
    stats = request.stats or {}
    evidence_count = int(stats.get("evidence_count", 0))
    mismatch_count = int(stats.get("mismatch_count", 0))

    # Simple deterministic "LLM" logic for PoC
    if mismatch_count == 0:
        risk_lens = "low"
    elif mismatch_count == 1:
        risk_lens = "medium"
    else:
        risk_lens = "high"

    inner_summary = (
        f"Run {run_id} for case {case_id}: "
        f"{evidence_count} evidence item(s), {mismatch_count} mismatch(es). "
        f"Integrity posture appears {risk_lens} risk."
    )

    outer_commentary = (
        "Second-layer reflection: The system successfully coordinated Investigator, "
        "Verifier, Guardian, and the LLM layer. "
        "Tamper detection is working and enforcement is triggered only on mismatches."
    )

    return {
        "inner_summary": inner_summary,
        "risk_lens": risk_lens,
        "outer_commentary": outer_commentary,
        "meta": {
            "version": "llm-mock-0.1",
            "note": "Russian-doll style, two-layer analysis mock."
        }
    }


@aggregated_app.get("/")
def root():
    return {
        "service": "Sovereign Aggregated Backend",
        "version": "1.0.0-phase5e",
        "status": "ok",
        "phase": "5E - Local Substrate Verification",
        "endpoints": [
            "/health",
            "/actions/index_truth",
            "/core/analyze",
            "/truth/search",
            "/enforce/action",
            "/api/core/verify_hash",
            "/api/evidence/info",
            "/api/llm/analyze"
        ],
        "evidence_store": str(EVIDENCE_ROOT),
        "current_evidence_hash": EVIDENCE_CHECKSUM
    }


# =============================================================================
# RUNNER
# =============================================================================

def run_service(app: FastAPI, port: int, name: str):
    """Run a single service in a thread."""
    print(f"  Starting {name} on port {port}...")
    config = uvicorn.Config(app, host="0.0.0.0", port=port, log_level="warning")
    server = uvicorn.Server(config)
    server.run()


def main():
    print("=" * 60)
    print("  SOVEREIGN MOCK SERVICES - PHASE 5E")
    print("  Local Substrate Verification Demo")
    print("=" * 60)
    print()
    print(f"Evidence store: {EVIDENCE_ROOT}")
    print(f"Mock evidence:  {MOCK_FILE}")
    print(f"Initial hash:   {EVIDENCE_CHECKSUM}")
    print()
    print("Starting services...")
    print()

    # Start individual service mocks in threads
    threads = []
    for key, config in SERVICES.items():
        app = create_service_app(key, config)
        t = threading.Thread(
            target=run_service,
            args=(app, config["port"], config["name"]),
            daemon=True
        )
        t.start()
        threads.append(t)
        time.sleep(0.2)  # Stagger startup

    print()
    print("Individual services running:")
    for key, config in SERVICES.items():
        print(f"  - {config['name']}: http://localhost:{config['port']}/health/{key}")

    print()
    print("Starting aggregated backend on port 8502...")
    print()
    print("=" * 60)
    print("  ALL SERVICES READY - PHASE 5E ACTIVE")
    print("=" * 60)
    print()
    print("Aggregated health: http://localhost:8502/health")
    print("Verify hash:       http://localhost:8502/api/core/verify_hash")
    print("Evidence info:     http://localhost:8502/api/evidence/info")
    print()
    print("TAMPER TEST:")
    print(f"  1. Edit: {MOCK_FILE}")
    print("  2. POST /api/core/verify_hash with original hash")
    print("  3. Response will show match: false (tamper detected)")
    print()
    print("Now start Boardroom UI:")
    print("  cd boardroom")
    print("  streamlit run boardroom_app.py --server.port 8501")
    print()
    print("Then open: http://localhost:8501")
    print()
    print("Press Ctrl+C to stop all services.")
    print()

    # Run aggregated backend in main thread (blocking)
    uvicorn.run(aggregated_app, host="0.0.0.0", port=8502, log_level="info")


if __name__ == "__main__":
    main()
