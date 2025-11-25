#!/usr/bin/env python3
"""
Mock Backend for Boardroom Demo - Returns healthy status for all services.

Run:
  pip install fastapi uvicorn
  uvicorn mock_backend:app --host 0.0.0.0 --port 8502 --reload

Then start Streamlit:
  streamlit run boardroom_app.py --server.port 8501
"""
import random
from datetime import datetime
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Sovereign Mock Backend", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def aggregated_health():
    """Return aggregated health status for all services."""
    return {
        "overall_status": "healthy",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "checks": {
            "env_file": {
                "status": "pass",
                "message": ".env file configured correctly"
            },
            "services_running": {
                "status": "pass",
                "message": "All 5 core services running"
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
        "services": {
            "Core": {
                "status": "healthy",
                "endpoint": "http://localhost:8001",
                "latency_ms": random.randint(8, 25)
            },
            "Truth Engine": {
                "status": "healthy",
                "endpoint": "http://localhost:8002",
                "latency_ms": random.randint(10, 35)
            },
            "Enforce": {
                "status": "healthy",
                "endpoint": "http://localhost:8003",
                "latency_ms": random.randint(5, 20)
            },
            "Models": {
                "status": "healthy",
                "endpoint": "http://localhost:8004",
                "latency_ms": random.randint(15, 50)
            },
            "RAG Index": {
                "status": "healthy",
                "endpoint": "http://localhost:8005",
                "latency_ms": random.randint(12, 40)
            }
        }
    }


@app.post("/actions/index_truth")
def index_truth(payload: dict = None):
    """Trigger truth indexer (mock)."""
    return {
        "status": "success",
        "message": "Indexer triggered successfully",
        "job_id": f"IDX-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
        "documents_queued": 50,
        "estimated_time_s": 30
    }


@app.get("/")
def root():
    return {"status": "ok", "service": "Sovereign Mock Backend", "version": "1.0.0"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8502)
