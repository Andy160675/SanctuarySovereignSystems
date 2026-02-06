import unittest
import json
import os

LEDGER_PATH = "Governance/ledger/decisions.jsonl"

class TestLedgerIdentityFields(unittest.TestCase):
    def test_gated_actions_have_identity(self):
        """Verifies that gated actions in the ledger have Phase 9 identity metadata."""
        if not os.path.exists(LEDGER_PATH):
            self.skipTest("Ledger not found")
            
        with open(LEDGER_PATH, 'r', encoding='utf-8') as f:
            for line in f:
                if not line.strip():
                    continue
                entry = json.loads(line)
                
                # If it's a deployment auth or similar gated event
                if entry.get("event") == "DEPLOYMENT_AUTH":
                    self.assertIn("operator", entry, f"Missing operator in {entry}")
                    self.assertIn("scope", entry, f"Missing scope in {entry}")
                    self.assertIn("targets", entry, f"Missing targets in {entry}")
                    self.assertIn("result", entry, f"Missing result in {entry}")

if __name__ == "__main__":
    unittest.main()
