import time
import json
import random
import os
import sys
from typing import Dict, Any, List, Optional, Callable
from concurrent.futures import ThreadPoolExecutor, as_completed

# Fix path
sys.path.insert(0, os.getcwd())

from sovereign_engine.core.phase8_engine import SovereignEngine, EngineError
from sovereign_engine.core.audit_engine import AuditEngine

def run_stress_simulation():
    print("=== STARTING 1M-NODE ADVERSARIAL STRESS SIMULATION ===")
    
    engine = SovereignEngine()
    
    def generic_handler(profile):
        def handler(signal, context=None):
            # In a real scenario, this would have detection logic
            if context and context.get("adversarial"):
                # Simulation logic: 10% chance to detect adversarial activity if it's "liar" or "herd"
                if "liar" in context.get("agent_id", "") and random.random() > 0.9:
                    return {"outcome": "rejected", "reason": "malicious_telemetry_detected"}
            return {"outcome": "processed", "profile": profile}
        return handler

    handlers = {
        "operator": generic_handler("Owen"),
        "innovator": generic_handler("Ryan"),
        "steward": generic_handler("Andy"),
    }
    
    engine.boot(handlers=handlers)
    audit = AuditEngine(engine)
    
    # 1. THE STAMPEDING HERD (Reduced size for local simulation stability, but targeting 1M node logic)
    print("\n[Phase 1.1] Testing Stampeding Herd...")
    audit.vector_stampeding_herd(size=5000) # 5k concurrent requests to same resource
    
    # 2. THE LIAR'S CONSENSUS
    print("\n[Phase 1.2] Testing Liar's Consensus...")
    audit.vector_liars_consensus(sub_fleet_size=500)
    
    # 3. THE CHAMELEON
    print("\n[Phase 1.3] Testing Chameleon Identity Switches...")
    audit.vector_chameleon(switches=100)
    
    # 4. THE TIME WARP
    print("\n[Phase 1.4] Testing Time Warp (Temporal Logic)...")
    audit.vector_time_warp(skew_count=1000)
    
    # 5. THE MEMORY LEAK BOMB
    print("\n[Phase 1.5] Testing Memory Leak Bomb...")
    audit.vector_memory_leak_bomb(cohort_size=50) # Smaller cohort due to payload exponential growth
    
    # 6. STEWARD OVERLOAD
    print("\n[Phase 2.1] Testing Steward Overload...")
    audit.vector_steward_overload(request_count=1000)
    
    # 7. CONSTITUTIONAL AMENDMENT UNDER FIRE
    print("\n[Phase 2.2] Testing Constitutional Amendment Under Fire...")
    audit.vector_constitutional_amendment_under_fire()
    
    print("\n=== ADVERSARIAL SIMULATION CONCLUDED ===")
    audit.generate_evidence_bundle("evidence/adversarial_simulation_report.json")
    
    stats = engine.engine_stats() if callable(engine.engine_stats) else engine.engine_stats
    print(f"Final Engine Stats: {json.dumps(stats, indent=2)}")

if __name__ == "__main__":
    try:
        run_stress_simulation()
    except Exception as e:
        print(f"Simulation failed: {e}")
        import traceback
        traceback.print_exc()
