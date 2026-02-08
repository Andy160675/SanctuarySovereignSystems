"""
Sovereign Governance Pack v1.0
Unified API for Governance Core Pack.
"""

from typing import Dict, Any, List
from .evidence.api import get_global_evidence_chain, EvidenceChain
from .policy_compiler import PolicyCompiler
from .merge_gate import MergeGate
from .drift_guard import DriftGuard

class GovernancePack:
    """Unified entry point for Governance Core Pack."""
    
    def __init__(self, version: str = "1.0.0"):
        self.version = version
        self.evidence: EvidenceChain = get_global_evidence_chain()
        self.policy_compiler = PolicyCompiler()
        self.merge_gate = MergeGate()
        self.drift_guard = DriftGuard()

    def validate_proposal(self, proposal: Dict[str, Any]) -> Dict[str, Any]:
        """Complete validation of a governance proposal."""
        # 1. Check for constitutional drift first
        alerts = self.drift_guard.monitor_kernel()
        if alerts:
            return {
                "passed": False,
                "reason": "Constitutional drift detected. Action blocked.",
                "alerts": alerts
            }
        
        # 2. Run merge gate validation if it's a code-related proposal
        if proposal.get("type") in ["merge", "pr"]:
            return self.merge_gate.validate_merge_signal(proposal)
        
        # 3. Default policy validation
        policy_name = proposal.get("policy", "default")
        result = self.policy_compiler.validate(policy_name, proposal.get("context", {}))
        
        return {
            "passed": result.passed,
            "violations": result.violations,
            "metadata": result.metadata
        }

    def get_audit_trail(self) -> List[Dict[str, Any]]:
        """Retrieve the immutable audit trail."""
        return [r.to_dict() for r in self.evidence.chain]

    def verify_integrity(self) -> bool:
        """Verify the integrity of the entire evidence chain."""
        return self.evidence.verify_chain()
