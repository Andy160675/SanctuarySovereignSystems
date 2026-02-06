import unittest
import json
import os
from Governance.sovereign_value_alignment import SovereignGovernance, AlignedAISystem, CitizenAssemblies
from Governance.ledger.decision_ledger import LEDGER_PATH

class TestValueAlignment(unittest.TestCase):
    def setUp(self):
        # Clear ledger for testing if needed, or just note the starting point
        self.initial_size = 0
        if os.path.exists(LEDGER_PATH):
            with open(LEDGER_PATH, 'r', encoding='utf-8') as f:
                self.initial_size = len(f.readlines())

    def test_high_impact_decision(self):
        gov = SovereignGovernance()
        issue = {
            "id": "TEST-HIGH",
            "title": "High Impact Policy",
            "impact_level": "high"
        }
        result = gov.decision_process(issue)
        self.assertEqual(result["decision"], "APPROVED")
        self.assertIn("Consensus reached by 150 participants", result["human_input"])
        
        # Verify ledger entry
        with open(LEDGER_PATH, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            self.assertGreater(len(lines), self.initial_size)
            last_entry = json.loads(lines[-1])
            # The decision is logged as a JSON string inside the 'decision' field
            logged_decision = json.loads(last_entry["decision"])
            self.assertEqual(logged_decision["issue_id"], "TEST-HIGH")

    def test_constitutional_violation(self):
        gov = SovereignGovernance()
        issue = {
            "id": "TEST-VIOLATION",
            "title": "Bad Policy",
            "impact_level": "low",
            "violates_red_line": True
        }
        result = gov.decision_process(issue)
        self.assertEqual(result["decision"], "REJECTED")
        self.assertEqual(result["constitutional_check"], "VIOLATION")

    def test_ai_system_constraints(self):
        ai = AlignedAISystem("test-domain")
        context = {"stakes_level": "high"}
        result = ai.operate({}, context)
        self.assertEqual(result, "ESCALATED_TO_HUMAN")
        
        context = {"stakes_level": "low"}
        result = ai.operate({}, context)
        self.assertEqual(result, "EXECUTED_WITH_AUDIT_TRAIL")

if __name__ == "__main__":
    unittest.main()
