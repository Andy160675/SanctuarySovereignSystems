import time
import json
import random
from typing import Dict, Any, List
from sovereign_engine.core.phase8_engine import SovereignEngine, EngineError

# Configuration for the agents as defined in sovereign_dashboard.jsx
AGENTS = [
    {"id": "LEGAL", "role": "Legal Compliance", "color": "#ff6b6b", "icon": "⚖️"},
    {"id": "FINANCE", "role": "Financial Oversight", "color": "#ffd93d", "icon": "💰"},
    {"id": "SECURITY", "role": "Security Operations", "color": "#ff8c42", "icon": "🔒"},
    {"id": "ETHICS", "role": "Ethics & Governance", "color": "#6bcb77", "icon": "🏛️"},
    {"id": "TECH", "role": "Technical Architecture", "color": "#4d96ff", "icon": "⚙️"},
    {"id": "OPS", "role": "Operations", "color": "#9b72cf", "icon": "📋"},
    {"id": "RISK", "role": "Risk Assessment", "color": "#ff6b8a", "icon": "⚠️"},
    {"id": "AUDIT", "role": "Audit & Evidence", "color": "#45b7d1", "icon": "📊"},
    {"id": "COMMS", "role": "Communications", "color": "#96ceb4", "icon": "📡"},
    {"id": "HR", "role": "Human Resources", "color": "#dda0dd", "icon": "👥"},
    {"id": "STRAT", "role": "Strategy", "color": "#f0e68c", "icon": "🎯"},
    {"id": "INNOV", "role": "Innovation", "color": "#87ceeb", "icon": "💡"},
    {"id": "COORD", "role": "Coordinator (Chair)", "color": "#00ffc8", "icon": "👑"},
]

def agent_handler(agent: Dict[str, Any]):
    def handler(signal, context=None):
        print(f"    [{agent['id']}] Processing signal: {signal.type} - {signal.payload[:60]}...")
        # Simulate processing time
        # time.sleep(0.01)
        return {
            "outcome": "processed",
            "agent": agent["id"],
            "role": agent["role"],
            "decision": "approve" if random.random() > 0.05 else "escalate"
        }
    return handler

def run_pdca_loop_100():
    print("Initializing Sovereign Recursion Engine...")
    engine = SovereignEngine()
    
    # Register handlers for each authority level
    # We deploy all agents by assigning them to different signal paths or rounds
    handlers = {}
    
    # Simple mapping: distribute agents across the 3 authority levels
    handlers["operator"] = agent_handler(random.choice([a for a in AGENTS if a["id"] in ["OPS", "TECH", "COMMS", "HR"]]))
    handlers["innovator"] = agent_handler(random.choice([a for a in AGENTS if a["id"] in ["INNOV", "STRAT", "FINANCE", "RISK"]]))
    handlers["steward"] = agent_handler(random.choice([a for a in AGENTS if a["id"] in ["COORD", "LEGAL", "SECURITY", "ETHICS", "AUDIT"]]))
    
    # Explicitly log agent deployment
    print(f"Deploying agents: {[a['id'] for a in AGENTS]}")
    print(f"Orchestrating handlers across {len(handlers)} authority tiers.")

    print("Booting engine...")
    engine.boot(handlers=handlers)
    print("Engine booted successfully.")

    for i in range(1, 101):
        print(f"\n--- Starting Cycle {i}/100 ---")
        
        # 1. SITREP (Situation Report)
        print(f"Cycle {i}: SITREP")
        engine.submit_and_process(
            type="query",
            domain="operational",
            authority="operator",
            payload=f"SITREP for Cycle {i}: System state nominal, monitoring environmental variables."
        )

        # 2. PDCA - PLAN
        print(f"Cycle {i}: PDCA - PLAN")
        engine.submit_and_process(
            type="command",
            domain="governance",
            authority="innovator",
            payload=f"PLAN for Cycle {i}: Optimizing resource allocation for next iteration."
        )

        # 3. SWOT Analysis
        print(f"Cycle {i}: SWOT")
        engine.submit_and_process(
            type="query",
            domain="governance",
            authority="innovator",
            payload=f"SWOT Analysis for Cycle {i}: Strengths: High throughput. Weaknesses: Latency jitter. Opportunities: New extension. Threats: Integrity breach."
        )

        # 4. PDCA - DO, CHECK, ACT (As a sequence or combined)
        # We'll do them as separate signals to emphasize the process
        
        print(f"Cycle {i}: PDCA - DO")
        engine.submit_and_process(
            type="command",
            domain="operational",
            authority="operator",
            payload=f"DO for Cycle {i}: Executing planned optimization."
        )

        print(f"Cycle {i}: PDCA - CHECK")
        engine.submit_and_process(
            type="query",
            domain="operational",
            authority="operator",
            payload=f"CHECK for Cycle {i}: Verifying optimization results against baseline."
        )

        print(f"Cycle {i}: PDCA - ACT")
        engine.submit_and_process(
            type="command",
            domain="governance",
            authority="steward",
            payload=f"ACT for Cycle {i}: Adjusting constitutional parameters based on check results."
        )

    print("\n--- All 100 cycles completed ---")
    stats = engine.engine_stats
    print(f"Final Engine Stats: {json.dumps(stats, indent=2)}")

if __name__ == "__main__":
    try:
        run_pdca_loop_100()
    except EngineError as e:
        print(f"Engine Error: {e}")
    except Exception as e:
        print(f"Unexpected Error: {e}")
