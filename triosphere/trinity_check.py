import sys
import os
from pathlib import Path

# Ensure JARUS can be imported
root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if root_path not in sys.path:
    sys.path.insert(0, root_path)

from triosphere.tri_orchestrator import TriOrchestrator
from jarus.core.constitutional_runtime import ConstitutionalRuntime
from jarus.core.evidence_ledger import EvidenceLedger, ChainStatus

def run_trinity_check():
    """
    Verifies that an action successfully traverses the Triosphere:
    1. IntentSphere (Evaluation)
    2. EvidenceSphere (Receipt)
    3. ActionSphere (Result)
    """
    print("=" * 60)
    print("TRIOSPHERE: TRINITY CHECK")
    print("=" * 60)
    
    runtime = ConstitutionalRuntime()
    ledger = EvidenceLedger(auto_persist=False)
    orchestrator = TriOrchestrator(runtime, ledger)
    
    # Define an action
    action_name = "mission_critical_update"
    context = {
        "action": action_name,
        "operator": "TriAdmin",
        "priority": "HIGH"
    }
    
    # Define the ActionSphere logic
    execution_record = {"status": "pending"}
    def action_handler():
        print(f"  [ActionSphere] Executing: {action_name}")
        execution_record["status"] = "executed"
        return {"code": 0, "message": "Mission Accomplished"}
        
    print(f"\n[Step 1] Triggering Triosphere Action: {action_name}...")
    
    try:
        tri_result = orchestrator.execute_triosphere_action(action_name, context, action_handler)
        
        print("\n[Step 2] ActionSphere Result:")
        print(f"  Status: {tri_result['status']}")
        print(f"  Result: {tri_result['result']}")
        print(f"  Spheres Engaged: {tri_result['spheres_engaged']}")
        
        # Verify the Trinity (Three Spheres)
        print("\n[Step 3] Verifying Trinity Invariants...")
        
        # 1. Intent Check
        assert tri_result["decision"]["decision_type"] == "PERMIT"
        print("  [OK] IntentSphere: Authority Proven")
        
        # 2. Evidence Check
        entries = ledger.get_entries()
        # Genesis + Action (Intent) + Action (Result)
        assert len(entries) >= 3
        assert any("Surge-Authorized" in e.summary for e in entries)
        assert any("Action Complete" in e.summary for e in entries)
        print("  [OK] EvidenceSphere: Cryptographic Proof Recorded")
        
        # 3. Action Check
        assert execution_record["status"] == "executed"
        print("  [OK] ActionSphere: Effect Verified")
        
        print("\n[RESULT] TRINITY CHECK PASSED [OK]")
        print("All spheres aligned. Sovereignty maintained.")
        return True
        
    except Exception as e:
        print(f"\n[RESULT] TRINITY CHECK FAILED [X]")
        print(f"Error: {str(e)}")
        return False

if __name__ == "__main__":
    success = run_trinity_check()
    sys.exit(0 if success else 1)
