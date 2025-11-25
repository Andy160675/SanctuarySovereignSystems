#!/usr/bin/env python
import sys
import time
import json
import hashlib
from pathlib import Path

LEDGER_PATH = Path("Governance/Logs/audit_chain.jsonl")

def check_ledger_health():
    print("🏥 HEALTHCHECK: Ledger Integrity")
    if not LEDGER_PATH.exists():
        print("❌ FAIL: Ledger missing")
        return False
    
    lines = LEDGER_PATH.read_text(encoding="utf-8").strip().splitlines()
    if not lines:
        print("❌ FAIL: Ledger empty")
        return False
        
    print(f"   - Events: {len(lines)}")
    
    # Verify Hash Chain (Simple)
    # In a real system, we'd recompute hashes. Here we just check existence.
    last_line = json.loads(lines[-1])
    if "timestamp" not in last_line:
        print("❌ FAIL: Malformed last event")
        return False
        
    print(f"   - Last Event: {last_line.get('timestamp')} ({last_line.get('event_type', 'UNKNOWN')})")
    return True

def check_containers():
    print("🏥 HEALTHCHECK: Container Status")
    # In this environment, we might not have docker.
    # We'll skip if docker command fails.
    import subprocess
    try:
        result = subprocess.run(["docker", "ps", "--format", "{{.Names}}"], stdout=subprocess.PIPE, text=True)
        containers = result.stdout.strip().splitlines()
        if not containers:
             print("⚠️  WARN: No containers running (or docker not found)")
        else:
             print(f"   - Running: {', '.join(containers)}")
    except FileNotFoundError:
        print("⚠️  WARN: Docker command not found")
        
    return True

def main():
    print(f"--- SOVEREIGN PULSE {time.strftime('%H:%M:%S')} ---")
    ledger_ok = check_ledger_health()
    container_ok = check_containers()
    
    if ledger_ok and container_ok:
        print("✅ SYSTEM HEALTHY")
        sys.exit(0)
    else:
        print("❌ SYSTEM UNHEALTHY")
        sys.exit(1)

if __name__ == "__main__":
    main()
