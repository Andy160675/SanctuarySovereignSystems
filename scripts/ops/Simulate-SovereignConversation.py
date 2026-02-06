#!/usr/bin/env python3
import sys
import json
from pathlib import Path
from typing import List, Dict, Any

# Ensure we can import from the root
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    from src.boardroom.roles import ROLES
    from boardroom_13_agentic import RoleAgent, persist_audit, wire_recorder_and_archivist
except ImportError as e:
    print(f"Import error: {e}")
    sys.exit(1)

def simulate_conversation(topic: str):
    print(f"--- Simulating Sovereign Conversation on Topic: '{topic}' ---")
    
    # Initialize agents
    agents = [RoleAgent(r) for r in ROLES]
    context = "User requested a simulation of themselves or Manus to continue the conversation."
    
    # Run first pass of evaluations
    outputs: List[Dict[str, Any]] = []
    for agent in agents:
        out = agent.evaluate(topic, context)
        outputs.append(out)
        
    # Process through boardroom logic
    session_id = f"sim-{topic[:10].replace(' ', '_')}-{int(__import__('time').time())}"
    
    # We use a slightly different persistence for simulation to avoid polluting real audit if preferred,
    # but for now we follow the existing pattern.
    snapshot_path = persist_audit(topic, outputs, session_id)
    wire_recorder_and_archivist(outputs, snapshot_path)
    
    # Format and display the simulation
    for o in outputs:
        role = o['role_key'].upper()
        verdict = o['verdict']
        print(f"[{role}] {verdict}")
        
    # Check for actions/conflicts
    actions = [o["action"] for o in outputs if o.get("action") and not str(o["action"]).startswith("NO_ACTION")]
    if actions:
        freq = {}
        for a in actions:
            freq[a] = freq.get(a, 0) + 1
        most_common = max(freq.items(), key=lambda x: x[1])[0]
        print(f"\n[CHAIR] Consensus Action: {most_common}")
    else:
        print("\n[CHAIR] No immediate action required. Observation mode active.")

if __name__ == "__main__":
    default_topic = "Integration of Sovereign DNS and Egress Monitoring on the 10GbE Fleet"
    topic = sys.argv[1] if len(sys.argv) > 1 else default_topic
    simulate_conversation(topic)
