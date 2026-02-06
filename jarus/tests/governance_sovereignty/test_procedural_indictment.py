import unittest
import os
import sys
import json

# Add scripts directory to path to import engine
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../scripts/governance')))
from procedural_indictment import ProceduralIndictmentEngine

class TestProceduralIndictment(unittest.TestCase):
    def setUp(self):
        self.engine = ProceduralIndictmentEngine(ledger_integration=False)

    def test_quiet_action_processing(self):
        action = {
            "type": "file_access",
            "physical_grounding": True,
            "measurements": {"size": 1024},
            "audit_path": "logs/access.log"
        }
        result = self.engine.process_action("TestActor", action, {"context": "unit_test"})
        
        self.assertEqual(result['status'], 'action_processed')
        self.assertFalse(result['voice_raised'])
        self.assertEqual(result['emotional_content'], 0.0)
        self.assertEqual(result['constitutional_check_result'], 'constitutional')
        self.assertIn('SHA256:', result['evidence_hash'])

    def test_constitutional_violations(self):
        # Action missing all requirements
        action = {"type": "unauthorized_probe"}
        result = self.engine.process_action("Attacker", action, {"context": "violation_test"})
        
        self.assertEqual(result['constitutional_check_result'], 'requires_correction')
        self.assertIsNotNone(result['corrective_path'])
        self.assertFalse(result['voice_raised'])
        
        # Verify specific violations are recorded in the engine's chain
        evidence = self.engine.evidence_chain[-1]
        violations = evidence['constitutional_check']['violations']
        codes = [v['code'] for v in violations]
        self.assertIn('C001', codes)
        self.assertIn('C002', codes)
        self.assertIn('C003', codes)

    def test_evidence_integrity(self):
        action = {"type": "probe"}
        result = self.engine.process_action("Actor", action, {})
        evidence_hash = result['evidence_hash']
        
        evidence = self.engine.evidence_chain[-1]
        # Re-calculate hash to verify
        evidence_copy = evidence.copy()
        received_hash = evidence_copy.pop('evidence_hash', None)
        
        encoded = json.dumps(evidence_copy, sort_keys=True).encode()
        import hashlib
        calculated_hash = f"SHA256:{hashlib.sha256(encoded).hexdigest()}"
        
        self.assertEqual(evidence_hash, calculated_hash)

if __name__ == '__main__':
    unittest.main()
