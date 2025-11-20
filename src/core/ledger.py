import os
import json
import time
from pathlib import Path

class SovereignLedger:
    def __init__(self):
        self.log_path = Path("Governance/Logs/audit_chain.jsonl")
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

    def record_event(self, event_type: str, agent: str, data: dict):
        entry = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "event_type": event_type,
            "agent": agent,
            "data": data
        }
        
        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
        
        print(f"📜 Ledger Recorded: {event_type} | {agent}")
