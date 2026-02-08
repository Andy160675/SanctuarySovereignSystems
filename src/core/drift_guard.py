"""
Sovereign Constitution Drift Guard v1.0
Monitors kernel invariants and alerts on constitutional drift.
"""

from typing import Dict, List, Any
from .evidence.api import get_global_evidence_chain
from sovereign_engine.core.phase0_constitution import Constitution

class DriftGuard:
    """Monitors constitutional integrity and invariant stability."""
    
    def __init__(self, config_path: str = "sovereign_engine/configs/constitution.json", version: str = "1.0.0"):
        self.version = version
        self.config_path = config_path
        self.evidence = get_global_evidence_chain()
        self.constitution = Constitution(config_path)
        self.baseline_hash = self._calculate_baseline()

    def _calculate_baseline(self) -> str:
        """Calculate initial hash of constitutional ground truth."""
        import hashlib
        self.constitution.load()
        with open(self.config_path, "rb") as f:
            return hashlib.sha256(f.read()).hexdigest()

    def check_drift(self) -> Dict[str, Any]:
        """Verify current state against baseline."""
        import hashlib
        
        current_hash = ""
        try:
            with open(self.config_path, "rb") as f:
                current_hash = hashlib.sha256(f.read()).hexdigest()
        except Exception as e:
            return {"drift": True, "error": str(e)}

        drift_detected = current_hash != self.baseline_hash
        
        # Run invariant tests
        self.constitution.load()
        self.constitution.validate()  # Ensure validated before running tests
        results = self.constitution.run_invariant_tests()
        
        status = {
            "drift_detected": drift_detected,
            "baseline_hash": self.baseline_hash,
            "current_hash": current_hash,
            "invariants_passed": results.all_passed,
            "failed_count": results.failed
        }
        
        # Log to evidence
        if drift_detected or not results.all_passed:
            self.evidence.append(
                "drift_alert",
                status,
                f"drift-guard/{self.version}"
            )
        
        return status

    def monitor_kernel(self) -> List[str]:
        """Full kernel health check."""
        # 1. Check file drift
        drift = self.check_drift()
        alerts = []
        
        if drift["drift_detected"]:
            alerts.append(f"CONSTITUTION DRIFT: {drift['current_hash'][:8]} != {drift['baseline_hash'][:8]}")
        
        if not drift["invariants_passed"]:
            alerts.append(f"INVARIANT BREACH: {drift['failed_count']} invariants failed")
            
        return alerts
