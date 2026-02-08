import time
import json
import random
import sys
import os
from typing import Dict, Any, List, Callable
from concurrent.futures import ThreadPoolExecutor, as_completed

# Fix path
sys.path.insert(0, os.getcwd())

from sovereign_engine.core.phase8_engine import SovereignEngine, EngineError

# --- Cognitive Profiles Configuration ---
PROFILES = {
    "Owen": {"allocation": 0.30, "role": "Task Execution", "authority": "operator"},
    "Ceri": {"allocation": 0.20, "role": "Workload Management", "authority": "operator"},
    "Ryan": {"allocation": 0.15, "role": "Confidence Calibration", "authority": "innovator"},
    "Mitch": {"allocation": 0.15, "role": "Preparation Processing", "authority": "operator"},
    "Steven": {"allocation": 0.10, "role": "Administrative", "authority": "operator"},
    "Andy": {"allocation": 0.10, "role": "Architectural Coherence", "authority": "steward"},
}

class ScaledDeployment:
    def __init__(self, agent_count: int, stage_id: int):
        self.agent_count = agent_count
        self.stage_id = stage_id
        self.engine = SovereignEngine()
        self.results = []
        self.start_time = 0
        self.end_time = 0

    def mock_handler(self, profile_name: str):
        def handler(signal, context=None):
            # Simulate work proportional to fleet scale (slight jitter)
            # time.sleep(random.uniform(0.001, 0.005))
            return {
                "outcome": "processed",
                "profile": profile_name,
                "decision": "approve" if random.random() > 0.01 else "escalate"
            }
        return handler

    def boot_engine(self):
        handlers = {
            "operator": self.mock_handler("Owen"), # Simple mapping for the test
            "innovator": self.mock_handler("Ryan"),
            "steward": self.mock_handler("Andy"),
        }
        self.engine.boot(handlers=handlers)

    def run_agent_cycle(self, agent_id: int, profile_name: str):
        profile = PROFILES[profile_name]
        try:
            outcome = self.engine.submit_and_process(
                type="command" if random.random() > 0.5 else "query",
                domain="operational" if profile["authority"] == "operator" else "governance",
                authority=profile["authority"],
                payload=f"Agent {agent_id} ({profile_name}) executing workload.",
                context={"agent_id": agent_id, "profile": profile_name}
            )
            return True, outcome
        except Exception as e:
            return False, str(e)

    def execute(self):
        print(f"--- STAGE {self.stage_id}: Deploying {self.agent_count} Agents ---")
        self.boot_engine()
        self.start_time = time.time()
        
        # Distribution
        workload = []
        for profile_name, config in PROFILES.items():
            count = int(self.agent_count * config["allocation"])
            workload.extend([profile_name] * count)
        
        # Adjust for rounding
        while len(workload) < self.agent_count:
            workload.append("Owen")
            
        random.shuffle(workload)

        # Using ThreadPool to simulate concurrent agent activity
        success_count = 0
        failure_count = 0
        
        # Limit concurrency to avoid overloading the local machine during simulation
        max_workers = min(100, os.cpu_count() * 10)
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(self.run_agent_cycle, i, workload[i]) for i in range(self.agent_count)]
            for future in as_completed(futures):
                success, _ = future.result()
                if success:
                    success_count += 1
                else:
                    failure_count += 1

        self.end_time = time.time()
        duration = self.end_time - self.start_time
        pass_rate = (success_count / self.agent_count) * 100
        
        print(f"Stage {self.stage_id} Complete in {duration:.2f}s")
        print(f"Pass Rate: {pass_rate:.2f}% ({success_count}/{self.agent_count})")
        
        stats = self.engine.engine_stats
        print(f"Engine Stats: {json.dumps(stats, indent=2)}")
        
        return {
            "stage": self.stage_id,
            "agent_count": self.agent_count,
            "duration": duration,
            "pass_rate": pass_rate,
            "success_count": success_count,
            "failure_count": failure_count,
            "engine_stats": stats
        }

def run_campaign():
    stages = [
        {"count": 1000, "threshold": 95},
        {"count": 5000, "threshold": 98},
        {"count": 10000, "threshold": 97},
        {"count": 25000, "threshold": 95},
        {"count": 50000, "threshold": 93},
        {"count": 100000, "threshold": 90},
    ]

    report = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "stages": []
    }

    for i, stage_cfg in enumerate(stages, 1):
        deployer = ScaledDeployment(stage_cfg["count"], i)
        result = deployer.execute()
        report["stages"].append(result)
        
        if result["pass_rate"] < stage_cfg["threshold"]:
            print(f"CRITICAL: Stage {i} failed to meet threshold {stage_cfg['threshold']}%")
            break
        
        # Evidence generation for the stage
        os.makedirs("evidence/deployments", exist_ok=True)
        evidence_file = f"evidence/deployments/stage_{i}.json"
        with open(evidence_file, "w") as f:
            json.dump(result, f, indent=2)
            
        print(f"Evidence for Stage {i} generated: {evidence_file}")
        
        # Halt for manual review if this was a real gated process
        # print("Awaiting manual go/no-go... (auto-proceeding for simulation)")

    with open("evidence/deployments/full_campaign_report.json", "w") as f:
        json.dump(report, f, indent=2)

if __name__ == "__main__":
    run_campaign()
