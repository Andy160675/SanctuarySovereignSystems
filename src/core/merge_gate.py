"""
Sovereign Merge Gate v1.0
Enforces constitutional rules on PR/Merge signals.
"""

import subprocess
import sys
from typing import Dict, Any, List
from .evidence.api import get_global_evidence_chain
from .policy_compiler import PolicyCompiler

class MergeGate:
    """Governance gate for PRs and Merges."""
    
    def __init__(self, version: str = "1.0.0"):
        self.version = version
        self.evidence = get_global_evidence_chain()
        self.compiler = PolicyCompiler()
        self._load_default_policies()

    def _load_default_policies(self):
        """Load baseline merge policies."""
        self.compiler.load_policy("strict_merge", {
            "rules": [
                {"field": "kernel_tests", "operator": "eq", "value": "passed"},
                {"field": "codeowners_protected", "operator": "eq", "value": True},
                {"field": "authority", "operator": "in", "value": ["innovator", "steward"]}
            ]
        })

    def validate_merge_signal(self, signal: Dict[str, Any]) -> Dict[str, Any]:
        """Validate a merge request signal."""
        # 1. Run Kernel Invariants (Phase 8 integration)
        kernel_passed = self._run_kernel_tests()
        
        # 2. Check CODEOWNERS protection
        protected = self._check_codeowners()
        
        # 3. Build validation context
        context = {
            "kernel_tests": "passed" if kernel_passed else "failed",
            "codeowners_protected": protected,
            "authority": signal.get("authority", "unknown"),
            "signal_id": signal.get("id", "unknown")
        }
        
        # 4. Execute policy check
        result = self.compiler.validate("strict_merge", context)
        
        # 5. Log to Evidence Chain
        self.evidence.append(
            "merge_validation",
            {
                "signal": signal,
                "context": context,
                "passed": result.passed,
                "violations": result.violations
            },
            f"merge-gate/{self.version}"
        )
        
        return {
            "passed": result.passed,
            "violations": result.violations,
            "kernel_tests": kernel_passed,
            "codeowners": protected
        }

    def _run_kernel_tests(self) -> bool:
        """Execute the 74 kernel invariant tests."""
        try:
            # In a real environment, this would import and run the test suite
            # Here we simulate the call to the kernel runner
            result = subprocess.run(
                [sys.executable, "-m", "sovereign_engine.tests.run_all"],
                capture_output=True, text=True
            )
            return "74/74 tests passed" in result.stdout
        except Exception:
            return False

    def _check_codeowners(self) -> bool:
        """Verify CODEOWNERS protection for kernel paths."""
        try:
            with open("CODEOWNERS", "r") as f:
                content = f.read()
                # Ensure kernel core is protected
                return "/sovereign_engine/core/" in content
        except FileNotFoundError:
            return False
