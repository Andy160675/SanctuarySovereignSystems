import json
import hashlib
import os
import sys
from pathlib import Path

# Ensure we can import from root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.router import SovereignRouter

LOG_PATH = Path(r"c:\sovereign-system\Governance\Logs\audit_chain.jsonl")

def generate_test_traffic():
    """Generates 3 rapid-fire events to build a chain."""
    print("⚡ Generating test traffic...")
    router = SovereignRouter("evidence") # Ensure 'evidence' is in your router config
    
    for i in range(1, 4):
        router.process(
            filename=f"smoke_test_{i}.json",
            data={"test_run": i},
            confidence=0.9 + (i/100), # Varying confidence
            estimated_cost=0.01
        )
    print("   3 Events logged.")

def verify_chain_integrity():
    """Re-calculates every hash to ensure the chain is unbroken."""
    print("\n🔍 Auditing Ledger Integrity...")
    
    if not LOG_PATH.exists():
        print("❌ No log found!")
        return

    with open(LOG_PATH, 'r') as f:
        lines = f.readlines()

    previous_hash = "0" * 64 # Genesis Hash expectation
    errors = 0

    for index, line in enumerate(lines):
        entry = json.loads(line)
        stored_hash = entry.pop("hash") # Remove hash to verify calculation
        
        # 1. Check Linkage
        if entry["prev_hash"] != previous_hash:
            print(f"   🚨 BROKEN CHAIN at Line {index+1}")
            print(f"      Expected Prev: {previous_hash[:16]}...")
            print(f"      Found Prev:    {entry['prev_hash'][:16]}...")
            errors += 1
            
        # 2. Check Content Integrity
        # Re-serialize exactly as the router did (sort_keys=True)
        payload_str = json.dumps(entry, sort_keys=True)
        calculated_hash = hashlib.sha256(payload_str.encode()).hexdigest()
        
        if calculated_hash != stored_hash:
            print(f"   🚨 TAMPER DETECTED at Line {index+1}")
            print(f"      Calculated: {calculated_hash[:16]}...")
            print(f"      Stored:     {stored_hash[:16]}...")
            errors += 1

        # Update tracker
        previous_hash = stored_hash

    if errors == 0:
        print(f"✅ AUDIT PASSED. {len(lines)} entries verified. Chain is unbroken.")
    else:
        print(f"❌ AUDIT FAILED. {errors} integrity violations found.")

if __name__ == "__main__":
    # Ensure environment is set for the router
    os.environ["TRACK"] = "insider"
    
    # 1. Create Data
    try:
        generate_test_traffic()
    except Exception as e:
        print(f"Setup failed: {e}")
        print("Did you add 'evidence' to AGENT_CONFIG in router.py?")
        exit(1)

    # 2. Verify Data
    verify_chain_integrity()