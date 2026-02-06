import json
import hashlib
import os
from datetime import datetime, timezone

LEDGER_PATH = os.path.join("Governance", "ledger", "decisions.jsonl")

class DecisionLedger:
    @staticmethod
    def compute_hash(entry):
        # Ensure we don't hash the hash itself if it's already there
        data = entry.copy()
        data.pop("entry_hash", None)
        payload = json.dumps(data, sort_keys=True, separators=(',', ':'))
        return hashlib.sha256(payload.encode()).hexdigest()

    @staticmethod
    def get_last_hash():
        if not os.path.exists(LEDGER_PATH):
            return None
        try:
            with open(LEDGER_PATH, 'r', encoding='utf-8') as f:
                lines = [l.strip() for l in f if l.strip()]
                if not lines:
                    return None
                last_entry = json.loads(lines[-1])
                return last_entry.get("entry_hash")
        except Exception:
            return None

    @classmethod
    def log(cls, decision, metadata=None):
        timestamp = datetime.now(timezone.utc).isoformat()
        previous_hash = cls.get_last_hash()
        
        entry = {
            "timestamp": timestamp,
            "decision": decision,
            "metadata": metadata or {},
            "previous_hash": previous_hash,
            "node_id": os.environ.get("NODE_ID", "MASTER")
        }
        
        entry["entry_hash"] = cls.compute_hash(entry)
        
        os.makedirs(os.path.dirname(LEDGER_PATH), exist_ok=True)
        with open(LEDGER_PATH, 'a', encoding='utf-8', newline='\n') as f:
            f.write(json.dumps(entry, separators=(',', ':')) + "\n")
        
        return entry["entry_hash"]
