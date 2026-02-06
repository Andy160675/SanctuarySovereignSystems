import unittest
import json
import subprocess
import os

class TestAuditAPIPermissions(unittest.TestCase):
    def test_audit_api_readonly(self):
        """Verifies that the Audit API (via probe script) only exposes read methods/data."""
        script_path = "scripts/governance/audit_api_probe.py"
        if not os.path.exists(script_path):
            self.skipTest("audit_api_probe.py not found")
            
        result = subprocess.run(["python", script_path], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0)
        
        data = json.loads(result.stdout)
        self.assertEqual(data["status"], "success")
        self.assertIn("proof_bundle", data)
        # Check for NO writeable fields or destructive patterns
        for key in data.keys():
            self.assertNotIn(key.lower(), ["delete", "update", "modify", "write"])

if __name__ == "__main__":
    unittest.main()
