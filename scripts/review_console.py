import os
import json
import shutil
import time
import hashlib

DRAFTS = "Evidence/Analysis/_drafts"
VERIFIED = "Evidence/Analysis/_verified"
LEDGER = "Governance/Logs/audit_chain.jsonl"

def log_audit(event, filename):
    """Minimal audit logger to maintain chain integrity during manual review."""
    prev_hash = "0"*64
    if os.path.exists(LEDGER):
        with open(LEDGER, 'r') as f:
            lines = f.readlines()
            if lines: prev_hash = json.loads(lines[-1]).get("hash", "0"*64)
    
    payload = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "event": event,
        "agent": "HUMAN_REVIEWER",
        "data": {"file": filename},
        "prev_hash": prev_hash
    }
    current_hash = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
    payload["hash"] = current_hash
    
    with open(LEDGER, "a") as f:
        f.write(json.dumps(payload) + "\n")
    return current_hash

def review():
    # Ensure directories exist
    os.makedirs(DRAFTS, exist_ok=True)
    os.makedirs(VERIFIED, exist_ok=True)

    files = [f for f in os.listdir(DRAFTS) if f.endswith('.json')]
    if not files:
        print("✅ No pending drafts.")
        return

    print(f"🔍 Found {len(files)} drafts pending review.\n")
    
    for f in files:
        path = os.path.join(DRAFTS, f)
        try:
            with open(path, 'r') as json_file:
                data = json.load(json_file)
        except Exception as e:
            print(f"⚠️  Error reading {f}: {e}")
            continue
            
        print(f"--- DOC: {f} ---")
        print(f"Claim: {data.get('claim')}")
        print(f"Conf:  {data.get('_governance', {}).get('confidence')}")
        
        cmd = input("   [A]pprove / [R]eject / [S]kip? > ").lower()
        
        if cmd == 'a':
            shutil.move(path, os.path.join(VERIFIED, f))
            log_decision(f, "APPROVED")
            print("   ✅ Promoted to Verified.")
        elif cmd == 'r':
            os.remove(path)
            log_decision(f, "REJECTED")
            print("   ❌ Rejected and Deleted.")
        else:
            print("   ⏩ Skipped.")
        print("-" * 30)

if __name__ == "__main__":
    review()
