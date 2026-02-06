import json
import time
import hashlib
import os
import socket
from typing import Dict, Any

class TelemetryEmitter:
    def __init__(self, nas_path: str, head_name: str):
        self.nas_path = nas_path
        self.head_name = head_name
        self.hostname = socket.gethostname()
        self.log_dir = os.path.join(nas_path, "04_LOGS", "telemetry", head_name)
        os.makedirs(self.log_dir, exist_ok=True)
        
        self.current_date = time.strftime("%Y-%m-%d")
        self.log_file = os.path.join(self.log_dir, f"{self.current_date}.ndjson")

    def emit(self, component: str, op: str, latency_ms: float, queue_depth: int = 0, result: str = "success", payload: Dict[str, Any] = None):
        event = {
            "ts": time.time(),
            "host": self.hostname,
            "head": self.head_name,
            "component": component,
            "op": op,
            "latency_ms": latency_ms,
            "queue_depth": queue_depth,
            "result": result,
            "deployment_id": os.getenv("SOVEREIGN_DEPLOYMENT_ID", "default")
        }
        if payload:
            event["payload"] = payload
            
        # Calculate evidence hash for the event itself
        event_str = json.dumps(event, sort_keys=True)
        event["evidence_hash"] = hashlib.sha256(event_str.encode()).hexdigest()
        
        with open(self.log_file, "a") as f:
            f.write(json.dumps(event) + "\n")

if __name__ == "__main__":
    # Test emission
    emitter = TelemetryEmitter("C:\\Users\\user\\IdeaProjects\\sovereign-system\\NAS", "PC3_HEART")
    emitter.emit("test_component", "ping", 1.23, 0, "success")
    print("Test telemetry emitted.")
