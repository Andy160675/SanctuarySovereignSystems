import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any

class DecisionLogger:
    def __init__(self, log_path: str = "logs/decision_log.jsonl"):
        self.log_path = Path(log_path)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

    def log_decision(self, action_id: str, action_type: str, details: Dict[str, Any]):
        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "action_id": action_id,
            "type": action_type,
            "details": details
        }
        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")
