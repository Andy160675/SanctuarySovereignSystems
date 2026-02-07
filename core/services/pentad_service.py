import sys
import time
import json
import os
from pathlib import Path

class PentadCoreService:
    """Base class for Pentad core services (Constitutional Court, Orchestrator, etc.)"""
    def __init__(self, service_name, head_id, role):
        self.service_name = service_name
        self.head_id = head_id
        self.role = role
        self.status = "initializing"
        self.log_dir = Path("logs/services")
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.log_file = self.log_dir / f"{service_name}.log"

    def log(self, message):
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        entry = f"[{timestamp}] [{self.service_name}] {message}\n"
        with open(self.log_file, "a") as f:
            f.write(entry)
        print(entry.strip())

    def run(self):
        self.status = "operational"
        self.log(f"Service started on {self.head_id} as {self.role}")
        try:
            while True:
                # Placeholder for service-specific logic
                time.sleep(60)
                self.log("Heartbeat: Active")
        except KeyboardInterrupt:
            self.status = "stopped"
            self.log("Service stopped by operator.")

if __name__ == "__main__":
    # Example usage: python pentad_service.py constitutional-court pc-a constitutional
    if len(sys.argv) < 4:
        print("Usage: python pentad_service.py <name> <head> <role>")
        sys.exit(1)
    
    svc = PentadCoreService(sys.argv[1], sys.argv[2], sys.argv[3])
    svc.run()
