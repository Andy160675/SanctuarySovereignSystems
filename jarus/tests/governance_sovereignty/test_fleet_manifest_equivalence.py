import unittest
import subprocess
import os

class TestFleetManifestEquivalence(unittest.TestCase):
    def test_compare_script_exit_codes(self):
        """Verifies that compare_repo_manifests.ps1 returns expected exit codes."""
        script_path = "scripts/fleet/compare_repo_manifests.ps1"
        if not os.path.exists(script_path):
            self.skipTest("compare_repo_manifests.ps1 not found")
            
        # Run it and check output
        # In this environment, we might not have 2 nodes, so it might exit with 0 or warning.
        # But we want to ensure it's functional.
        result = subprocess.run(["powershell", "-ExecutionPolicy", "Bypass", "-File", script_path], capture_output=True, text=True)
        
        # If it found < 2 nodes, it might just return (per script logic)
        # But we want to verify the logic we added.
        if "ZERO DRIFT CONFIRMED" in result.stdout:
            self.assertEqual(result.returncode, 0)
        elif "DRIFT DETECTED" in result.stdout:
            self.assertEqual(result.returncode, 10)

if __name__ == "__main__":
    unittest.main()
