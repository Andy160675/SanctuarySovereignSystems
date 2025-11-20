import os
import json
import shutil
import hashlib
import time
from pathlib import Path

DRAFTS = Path("Evidence/Analysis/_drafts")
VERIFIED = Path("Evidence/Analysis/_verified")
AUDIT_LOG = Path("Governance/Logs/audit_chain.jsonl")

VERIFIED.mkdir(parents=True, exist_ok=True)

def log_decision(filename, decision):
    entry = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "event": "HUMAN_REVIEW",
        "agent": "admin_sim",
        "data": {"file": filename, "decision": decision},
        "prev_hash": "SIMULATED_HASH"
    }
    with open(AUDIT_LOG, "a") as f:
        f.write(json.dumps(entry) + "\n")

def run_sim():
    drafts = list(DRAFTS.glob("*.json"))
    print(f"🤖 Simulating Human Review for {len(drafts)} drafts...")
    
    # Approve first 13, Reject last 2
    for i, draft in enumerate(drafts):
        if i < 13:
            shutil.move(str(draft), str(VERIFIED / draft.name))
            log_decision(draft.name, "APPROVED")
            print(f"   ✅ Approved: {draft.name}")
        else:
            draft.unlink() # Delete
            log_decision(draft.name, "REJECTED")
            print(f"   ❌ Rejected: {draft.name}")

if __name__ == "__main__":
    run_sim()
