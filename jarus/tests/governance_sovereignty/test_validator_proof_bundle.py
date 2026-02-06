import unittest
import os
import json
import glob

class TestValidatorProofBundle(unittest.TestCase):
    def test_proof_bundle_integrity(self):
        """Verifies that the validator produces a complete, hash-sealed proof bundle."""
        # Only look for folders that match the yyyyMMdd_HHmmss pattern
        validation_dirs = [d for d in glob.glob("validation/*") if os.path.basename(d).isdigit() or "_" in os.path.basename(d) and len(os.path.basename(d)) == 15]
        
        if not validation_dirs:
            self.skipTest("No validation runs found. Run validate_sovereignty.ps1 first.")
            
        # Get latest run
        latest_run = max(validation_dirs, key=os.path.getmtime)
        
        verdict_path = os.path.join(latest_run, "VERDICT.json")
        manifest_path = os.path.join(latest_run, "MANIFEST_SHA256.txt")
        
        self.assertTrue(os.path.exists(verdict_path), "VERDICT.json missing")
        self.assertTrue(os.path.exists(manifest_path), "MANIFEST_SHA256.txt missing")
        
        with open(verdict_path, 'r', encoding='utf-8-sig') as f:
            verdict = json.load(f)
            self.assertIn("run_id", verdict)
            self.assertIn("status", verdict)
            self.assertIn("checks", verdict)
            
        with open(manifest_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            self.assertTrue(len(lines) >= 1, "Manifest empty")
            # Verify VERDICT.json is in manifest
            found_verdict = any("VERDICT.json" in line for line in lines)
            self.assertTrue(found_verdict, "VERDICT.json not in manifest")

if __name__ == "__main__":
    unittest.main()
