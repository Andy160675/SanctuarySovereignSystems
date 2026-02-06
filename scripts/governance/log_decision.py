#!/usr/bin/env python3
import sys
import json
import hashlib
from pathlib import Path
from datetime import datetime, timezone

LEDGER_PATH = Path("Governance/Logs/audit_chain.jsonl")

def compute_entry_hash(entry: dict, prev_hash: str = "") -> str:
    canonical = json.dumps(entry, sort_keys=True, separators=(',', ':'))
    payload = f"{prev_hash}{canonical}"
    return hashlib.sha256(payload.encode('utf-8')).hexdigest()

def log_decision(summary: str, event_type: str = "ORCHESTRATION_ACTION"):
    LEDGER_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    prev_hash = ""
    if LEDGER_PATH.exists():
        lines = LEDGER_PATH.read_text(encoding="utf-8").strip().splitlines()
        if lines:
            last_entry = json.loads(lines[-1])
            prev_hash = last_entry.get("hash", "")

    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
        "event_type": event_type,
        "summary": summary,
        "prev_hash": prev_hash
    }
    
    entry["hash"] = compute_entry_hash(entry, prev_hash)
    
    with open(LEDGER_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python log_decision.py <summary>")
        sys.exit(1)
    
    log_decision(sys.argv[1])
    print(f"Logged: {sys.argv[1]}")
