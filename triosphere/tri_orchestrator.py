import time
from typing import Dict, Any, Callable, List
from jarus.core.constitutional_runtime import ConstitutionalRuntime, DecisionType
from jarus.core.evidence_ledger import EvidenceLedger, EvidenceType
from jarus.core.surge_wrapper import SurgeWrapper

class TriOrchestrator:
    """
    Sovereign Triosphere Orchestrator
    ================================
    Manages the three spheres of sovereign execution:
    1. IntentSphere (Evaluation & Logic)
    2. EvidenceSphere (Recording & Proof)
    3. ActionSphere (Execution & Effect)
    
    Enforces the 'Trinity Check': No action without proven intent and recorded evidence.
    """
    
    def __init__(self, runtime: ConstitutionalRuntime, ledger: EvidenceLedger):
        self.runtime = runtime
        self.ledger = ledger
        self.surge = SurgeWrapper(self.runtime, self.ledger)
        self.spheres = {
            "intent": "IntentSphere",
            "evidence": "EvidenceSphere",
            "action": "ActionSphere"
        }
    
    def execute_triosphere_action(self, action_name: str, context: Dict[str, Any], handler: Callable[..., Any]):
        """
        Executes an action across all three spheres using the Surge pattern.
        """
        # SurgeWrapper handles the 'No Receipt, No Action' pattern which 
        # aligns perfectly with the Triosphere requirements.
        
        print(f"[*] Triosphere: Engaging {list(self.spheres.values())} for '{action_name}'")
        
        result = self.surge.execute_sovereign_action(
            action_name=action_name,
            context=context,
            handler=handler
        )
        
        return {
            **result,
            "spheres_engaged": list(self.spheres.values())
        }

if __name__ == "__main__":
    # Internal test/scaffold
    runtime = ConstitutionalRuntime()
    ledger = EvidenceLedger(auto_persist=False)
    orch = TriOrchestrator(runtime, ledger)
    print("TriOrchestrator initialized.")
