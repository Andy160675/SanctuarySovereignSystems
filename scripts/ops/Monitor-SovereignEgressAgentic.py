import json
import time
import subprocess
from pathlib import Path
import os
import sys
from pathlib import Path

# Ensure we can import from the root
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from boardroom_13_agentic import RoleAgent, persist_audit, wire_recorder_and_archivist
from src.boardroom.roles import ROLES

VIOLATION_LOG = Path("validation/egress_violations.jsonl")
CHECKPOINT_FILE = Path("DATA/_work/egress_monitor_checkpoint.txt")

def get_last_processed_line():
    if CHECKPOINT_FILE.exists():
        try:
            return int(CHECKPOINT_FILE.read_text().strip())
        except:
            return 0
    return 0

def save_checkpoint(line_count):
    CHECKPOINT_FILE.parent.mkdir(parents=True, exist_ok=True)
    CHECKPOINT_FILE.write_text(str(line_count))

def monitor_egress():
    print("--- BOARDROOM-13: Egress Signal Monitor Active ---")
    agents = [RoleAgent(r) for r in ROLES]
    
    while True:
        if not VIOLATION_LOG.exists():
            time.sleep(10)
            continue
            
        with open(VIOLATION_LOG, "r", encoding="utf-8") as f:
            lines = f.readlines()
            
        last_line = get_last_processed_line()
        current_count = len(lines)
        
        if current_count > last_line:
            # Process new violations
            new_violations = lines[last_line:]
            for line in new_violations:
                try:
                    v = json.loads(line)
                    topic = f"Egress Violation Detected: {v.get('Process')} -> {v.get('Remote')}"
                    context = json.dumps(v)
                    
                    print(f"\n[SIGNAL] {topic}")
                    
                    outputs = []
                    for agent in agents:
                        out = agent.evaluate(topic, context)
                        outputs.append(out)
                    
                    session_id = f"egress-{int(time.time())}"
                    snapshot_path = persist_audit(topic, outputs, session_id)
                    wire_recorder_and_archivist(outputs, snapshot_path)
                    
                    # Log high-signal consensus to console
                    actions = [o["action"] for o in outputs if o.get("action") and not str(o["action"]).startswith("NO_ACTION")]
                    if actions:
                        print(f"  [BOARDROOM] Consensus Action Proposed: {max(set(actions), key=actions.count)}")
                    
                except Exception as e:
                    print(f"Error processing violation: {e}")
            
            save_checkpoint(current_count)
            
        time.sleep(30)

if __name__ == "__main__":
    try:
        monitor_egress()
    except KeyboardInterrupt:
        print("\nMonitor stopped.")
