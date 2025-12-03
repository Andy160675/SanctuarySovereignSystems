"""
Evidence Writer - Structured evidence collection for agent actions
Links to ledger for immutable audit trail
"""

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Evidence Writer", version="1.0.0")

EVIDENCE_PATH = Path(os.environ.get("EVIDENCE_PATH", "/evidence"))
LEDGER_URL = os.environ.get("LEDGER_URL", "http://ledger_service:8082/append")

# Ensure evidence directory exists
EVIDENCE_PATH.mkdir(parents=True, exist_ok=True)


class EvidenceEntry(BaseModel):
    event_type: str
    agent: str
    action: str
    target: Optional[str] = None
    outcome: str
    jurisdiction: Optional[str] = None
    data: Optional[dict] = None


class EvidenceResponse(BaseModel):
    success: bool
    evidence_id: str
    hash: str
    ledger_id: Optional[str] = None
    timestamp: str


def compute_hash(data: str) -> str:
    """Compute SHA-256 hash of data."""
    return hashlib.sha256(data.encode()).hexdigest()


async def log_to_ledger(entry: EvidenceEntry, evidence_id: str) -> Optional[str]:
    """Log event to ledger service."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(
                LEDGER_URL,
                json={
                    "event_type": entry.event_type,
                    "agent": entry.agent,
                    "action": entry.action,
                    "target": entry.target,
                    "outcome": entry.outcome,
                    "metadata": {
                        "evidence_id": evidence_id,
                        "jurisdiction": entry.jurisdiction,
                    }
                }
            )
            if response.status_code == 200:
                return response.json().get("entry_id")
    except Exception as e:
        print(f"Failed to log to ledger: {e}")
    return None


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "evidence_writer"}


@app.post("/log", response_model=EvidenceResponse)
async def log_evidence(entry: EvidenceEntry):
    """Log an evidence entry and forward to ledger."""
    timestamp = datetime.now(timezone.utc)
    evidence_id = f"E-{timestamp.strftime('%Y%m%d%H%M%S%f')}-{entry.agent}"

    # Build evidence record
    evidence_record = {
        "id": evidence_id,
        "timestamp": timestamp.isoformat(),
        "event_type": entry.event_type,
        "agent": entry.agent,
        "action": entry.action,
        "target": entry.target,
        "outcome": entry.outcome,
        "jurisdiction": entry.jurisdiction,
        "data": entry.data or {},
    }

    # Compute hash
    record_json = json.dumps(evidence_record, sort_keys=True)
    evidence_hash = compute_hash(record_json)
    evidence_record["hash"] = evidence_hash

    # Write to evidence file (one file per day)
    date_str = timestamp.strftime("%Y-%m-%d")
    evidence_file = EVIDENCE_PATH / f"evidence-{date_str}.jsonl"

    with open(evidence_file, "a") as f:
        f.write(json.dumps(evidence_record) + "\n")

    # Log to ledger
    ledger_id = await log_to_ledger(entry, evidence_id)

    return EvidenceResponse(
        success=True,
        evidence_id=evidence_id,
        hash=evidence_hash,
        ledger_id=ledger_id,
        timestamp=timestamp.isoformat()
    )


@app.get("/entries")
async def get_entries(date: Optional[str] = None, limit: int = 100):
    """Get evidence entries, optionally filtered by date."""
    if date:
        evidence_file = EVIDENCE_PATH / f"evidence-{date}.jsonl"
        if not evidence_file.exists():
            return {"entries": [], "total": 0}
        files = [evidence_file]
    else:
        files = sorted(EVIDENCE_PATH.glob("evidence-*.jsonl"), reverse=True)

    entries = []
    for f in files:
        with open(f, "r") as file:
            for line in file:
                if line.strip():
                    try:
                        entries.append(json.loads(line))
                        if len(entries) >= limit:
                            break
                    except json.JSONDecodeError:
                        continue
        if len(entries) >= limit:
            break

    return {"entries": entries[:limit], "total": len(entries)}
