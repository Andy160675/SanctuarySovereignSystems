import unittest
import json
import os

class TestPolicyMappingIntegrity(unittest.TestCase):
    def test_compliance_map_resolution(self):
        """Verifies that all mapped controls in COMPLIANCE_MAP.json resolve to valid evidence."""
        map_path = "evidence/COMPLIANCE_MAP.json"
        if not os.path.exists(map_path):
            self.skipTest("Compliance map not found. Run generate_compliance_map.py first.")
            
        with open(map_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        for mapping in data.get("mappings", []):
            artifact = mapping.get("artifact")
            if mapping.get("status") == "VERIFIED":
                self.assertTrue(os.path.exists(artifact), f"Artifact {artifact} reported as verified but missing")
            else:
                self.assertFalse(os.path.exists(artifact), f"Artifact {artifact} reported as missing but exists")

if __name__ == "__main__":
    unittest.main()
