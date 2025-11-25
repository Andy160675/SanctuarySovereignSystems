import time
import sys
import os
from datetime import datetime

# Add current directory to path so we can import modules
sys.path.append(os.getcwd())

from scout.scout import Scout
from executor.executor import Executor
from boardroom.boardroom import Boardroom
from core.governance import ConstitutionalViolationFlag

def print_header(title):
    print(f"\n{'='*60}")
    print(f" {title}")
    print(f"{'='*60}")

def print_log(agent, message, status="INFO"):
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] [{agent:<10}] {status}: {message}")

def run_stack():
    print_header("SOVEREIGN GOVERNANCE STACK - LOCAL RUNTIME")
    print_log("SYSTEM", "Initializing Sovereign Stack v1.0...")
    
    # 1. Initialize Agents
    try:
        scout = Scout()
        print_log("SCOUT", "Agent initialized. Daily limit: 3", "READY")
        
        executor = Executor()
        print_log("EXECUTOR", "Agent initialized. Cost ceiling: 35.0", "READY")
        
        board = Boardroom(ledger_path="boardroom_ledger.jsonl")
        print_log("BOARDROOM", "Agent initialized. Ledger: boardroom_ledger.jsonl", "READY")
        
    except Exception as e:
        print_log("SYSTEM", f"Initialization failed: {e}", "ERROR")
        return

    print_log("SYSTEM", "All agents online. Starting governance loop...", "SUCCESS")
    time.sleep(1)

    # 2. Define a Trial (The "Input")
    idea = {
        "purpose": "optimize_search_latency",
        "capability": "safe_operational_improvement",
        "environment": "sandbox_v3",
        "models_used": ["gpt-5.1-mini"],
        "data_access_mode": "logs_only",
        "flags": ["safe_operational_improvement"],
    }
    
    print_header("PHASE 1: SCOUT PROPOSAL")
    print_log("SCOUT", f"Analyzing idea: {idea['purpose']}")
    time.sleep(0.5)
    
    # 3. Scout Phase
    trial, scout_cvfs = scout.propose_trial(
        idea=idea,
        confidence=0.98,
        cost_estimate=12.5,
    )
    
    if scout_cvfs:
        for cvf in scout_cvfs:
            print_log("SCOUT", f"CVF Raised: {cvf.code} ({cvf.severity})", "WARNING")
    else:
        print_log("SCOUT", "Proposal validated. No constitutional violations.", "PASS")

    print_log("SCOUT", f"Handing off Trial {trial.trial_id[:8]}... to Executor")
    time.sleep(1)

    # 4. Executor Phase
    print_header("PHASE 2: EXECUTOR RUN")
    print_log("EXECUTOR", "Validating execution constraints...")
    
    trial, exec_cvfs = executor.run_trial(trial)
    
    if exec_cvfs:
        for cvf in exec_cvfs:
            print_log("EXECUTOR", f"CVF Raised: {cvf.code} ({cvf.severity})", "WARNING")
            if cvf.severity == "CRITICAL":
                print_log("EXECUTOR", "CRITICAL VIOLATION - HALTING EXECUTION", "FAIL")
                return
    
    if trial.results.get("success"):
        duration = trial.results["metrics"].get("simulated_duration_seconds")
        print_log("EXECUTOR", f"Execution successful. Duration: {duration}s", "SUCCESS")
    else:
        print_log("EXECUTOR", "Execution failed.", "FAIL")

    time.sleep(1)

    # 5. Boardroom Phase
    print_header("PHASE 3: BOARDROOM ADJUDICATION")
    print_log("BOARDROOM", "Reviewing trial evidence and CVFs...")
    
    all_cvfs = scout_cvfs + exec_cvfs
    decision, br_cvfs = board.decide(trial, all_cvfs)
    
    if br_cvfs:
        for cvf in br_cvfs:
            print_log("BOARDROOM", f"CVF Raised: {cvf.code} ({cvf.severity})", "WARNING")

    print_log("BOARDROOM", f"Final Verdict: {decision.upper()}", "DECISION")
    
    # 6. Ledger Status
    print_header("SYSTEM STATUS")
    print_log("LEDGER", f"Transaction recorded in {board.ledger_path}", "SAVED")
    print_log("SYSTEM", "Governance loop complete.", "DONE")

if __name__ == "__main__":
    run_stack()
