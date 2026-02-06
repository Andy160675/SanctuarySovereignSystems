import unittest
import json
import subprocess
import os
import hashlib

class TestProofPackVerify(unittest.TestCase):
    def test_pack_independent_validation(self):
        """Verifies that a pack retrieved via the Audit API can be independently validated."""
        script_path = "scripts/governance/audit_api_probe.py"
        if not os.path.exists(script_path):
            self.skipTest("audit_api_probe.py not found")
            
        result = subprocess.run(["python", script_path], capture_output=True, text=True)
        data = json.loads(result.stdout)
        
        bundle = data.get("proof_bundle")
        if not bundle:
            self.skipTest("No bundle in response")
            
        manifest_content = bundle.get("manifest")
        self.assertIsNotNone(manifest_content)
        
        # Verify that VERDICT.json hash in manifest matches actual file hash
        bundle_location = bundle.get("bundle_location")
        verdict_path = os.path.join(bundle_location, "VERDICT.json")
        
        with open(verdict_path, 'rb') as f:
            actual_hash = hashlib.sha256(f.read()).hexdigest().upper()
            
        # Manifest format: HASH  FILENAME
        found = False
        for line in manifest_content.splitlines():
            line = line.strip('\ufeff')
            if "VERDICT.json" in line:
                manifest_hash = line.split()[0]
                self.assertEqual(actual_hash, manifest_hash)
                found = True
        self.assertTrue(found, "VERDICT.json not found in manifest")

if __name__ == "__main__":
    unittest.main()
