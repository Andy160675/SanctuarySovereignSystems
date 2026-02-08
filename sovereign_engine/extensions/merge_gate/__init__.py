"""
Merge Gate - Constitutional PR/merge enforcement pipeline.
S3-EXT-007: Governance enforcement bolt-on.
"""

import json
import subprocess
import sys
from typing import Dict, List, Tuple
from pathlib import Path

class MergeGate:
    def __init__(self, vault_path: str = "./vault"):
        from sovereign_engine.extensions.evidence_vault import EvidenceVault
        self.vault = EvidenceVault(vault_path)
        self.checklist = self._load_checklist()
    
    def validate_merge(self, pr_number: str, branch: str) -> Dict:
        """Validate a merge against the constitutional checklist."""
        results = {
            "pr": pr_number,
            "branch": branch,
            "timestamp": self._get_timestamp(),
            "checks": {},
            "overall": "pending"
        }
        
        # Run checklist validations
        for check_id, check in self.checklist.items():
            check_result = self._run_check(check_id, check)
            results["checks"][check_id] = check_result
        
        # Determine overall status
        all_passed = all(c["passed"] for c in results["checks"].values())
        results["overall"] = "approved" if all_passed else "rejected"
        
        # Store evidence
        evidence_id = self.vault.store_evidence(
            "merge_validation",
            results,
            {"pr": pr_number, "branch": branch}
        )
        
        results["evidence_id"] = evidence_id
        return results
    
    def _run_check(self, check_id: str, check: Dict) -> Dict:
        """Run a single checklist validation."""
        check_type = check.get("type", "command")
        
        try:
            if check_type == "command":
                result = subprocess.run(
                    check["command"],
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=check.get("timeout", 30)
                )
                passed = result.returncode == 0
                output = result.stdout.strip()
            elif check_type == "python":
                # Safer eval context
                global_ctx = {"__builtins__": None}
                local_ctx = {"passed": False, "output": ""}
                exec(check["code"], global_ctx, local_ctx)
                passed = local_ctx.get("passed", False)
                output = local_ctx.get("output", "")
            elif check_type == "file_check":
                passed, output = self._check_file(
                    check["path"],
                    check.get("pattern"),
                    check.get("should_exist", True)
                )
            else:
                passed, output = False, f"Unknown check type: {check_type}"
            
            return {
                "passed": passed,
                "output": output,
                "timestamp": self._get_timestamp()
            }
            
        except Exception as e:
            return {
                "passed": False,
                "output": str(e),
                "timestamp": self._get_timestamp()
            }
    
    def _check_file(self, path: str, pattern: str = None, 
                   should_exist: bool = True) -> Tuple[bool, str]:
        """Check file existence or content."""
        file_path = Path(path)
        
        exists = False
        # Handle glob patterns if needed, but here we assume direct path or simple existence
        try:
            # Simple check for existence first
            exists = file_path.exists()
        except:
            # Handle glob if it looks like one
            if "*" in path:
                import glob
                exists = len(glob.glob(path)) > 0
        
        if not exists:
            return (not should_exist, f"File {path} {'exists' if exists else 'does not exist'}")
        
        if pattern:
            if file_path.is_file():
                with open(file_path, 'r') as f:
                    content = f.read()
                    found = pattern in content
                    return (found, f"Pattern {'found' if found else 'not found'} in {path}")
            else:
                return (False, f"{path} is a directory, cannot check pattern")
        
        return (True, f"File {path} exists")
    
    def _load_checklist(self) -> Dict:
        """Load the merge checklist."""
        checklist_path = Path(__file__).parent / "checklist.json"
        
        if checklist_path.exists():
            with open(checklist_path, 'r') as f:
                return json.load(f)
        
        # Default constitutional checklist
        return {
            "kernel_tests": {
                "name": "Kernel Invariant Tests",
                "type": "command",
                "command": f"{sys.executable} -m sovereign_engine.tests.run_all",
                "description": "All 74 kernel tests must pass"
            },
            "no_kernel_mods": {
                "name": "No Kernel Modifications",
                "type": "file_check",
                "path": ".github/CODEOWNERS",
                "pattern": "/sovereign_engine/core/",
                "description": "CODEOWNERS must protect kernel paths"
            },
            "evidence_generated": {
                "name": "Evidence Generated",
                "type": "file_check",
                "path": "evidence/*",
                "should_exist": True,
                "description": "Evidence directory must exist"
            },
            "sitrep_present": {
                "name": "SITREP Present",
                "type": "file_check",
                "path": "docs/procedures/",
                "pattern": "SITREP",
                "description": "SITREP documentation must exist"
            }
        }
    
    def _get_timestamp(self):
        from datetime import datetime
        return datetime.now().isoformat()

# GitHub integration helper
def validate_github_pr(pr_url: str, vault_path: str = "./vault") -> Dict:
    """Validate a GitHub PR using Merge Gate."""
    import re
    
    # Extract PR number from URL
    match = re.search(r'pull/(\d+)', pr_url)
    if not match:
        return {"error": "Invalid PR URL"}
    
    pr_number = match.group(1)
    
    # Simulate PR data
    pr_data = {
        "url": pr_url,
        "number": pr_number,
        "title": f"PR #{pr_number}",
        "author": "github_user",
        "branch": f"pr-{pr_number}"
    }
    
    # Run validation
    merge_gate = MergeGate(vault_path)
    results = merge_gate.validate_merge(pr_number, f"pr-{pr_number}")
    
    # Integrate with Slack if available
    try:
        from sovereign_engine.extensions.connectors.slack import SlackConnector
        slack = SlackConnector()
        
        if slack.webhook_url:
            status = "approved" if results["overall"] == "approved" else "rejected"
            message = f"PR #{pr_number} {status} by Merge Gate"
            slack.send_alert(
                message=message,
                severity="info" if status == "approved" else "warning",
                context={"evidence_id": results.get("evidence_id")}
            )
    except ImportError:
        pass
    
    return results
