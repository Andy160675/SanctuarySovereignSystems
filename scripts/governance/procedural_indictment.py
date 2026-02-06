import json
import hashlib
import time
from datetime import datetime, timezone
import os

class ProceduralIndictmentEngine:
    """
    The quiet engine that never raises its voice.
    Indicts by procedure, not accusation.
    """
    
    def __init__(self, ledger_integration=True):
        self.voice_decibels = 0  # Never raises voice
        self.evidence_chain = []
        self.ledger_integration = ledger_integration
        self.ledger = None
        if self.ledger_integration:
            # Ensure root is in path for imports
            root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
            if root_path not in os.sys.path:
                os.sys.path.append(root_path)
            
            try:
                from Governance.ledger.decision_ledger import DecisionLedger
                self.ledger = DecisionLedger
            except ImportError:
                try:
                    from governance.ledger.decision_ledger import DecisionLedger
                    self.ledger = DecisionLedger
                except ImportError:
                    self.ledger = None
    
    def _process_action(self, actor, action, context):
        """Process action without emotion, only evidence (PRIVATE CORE)"""
        
        # Step 1: Constitutional check (quiet)
        constitutional_check = self._constitutional_evaluation(action)
        
        # Step 2: Generate evidence (quiet)
        evidence = {
            'timestamp': self._cryptographic_timestamp(),
            'actor': actor,
            'action': action,
            'context': context,
            'pre_state_hash': self._capture_state(),
            'constitutional_check': constitutional_check,
            'evidence_type': 'procedural_recording',
            'emotional_tone': 0.0  # Zero emotional content
        }
        
        # Step 3: Execute action
        result = self._execute_action(action)
        
        # Step 4: Record post-state
        evidence['post_state_hash'] = self._capture_state()
        evidence['result'] = result
        
        # Step 5: Generate proof
        evidence_hash = self._generate_hash(evidence)
        evidence['evidence_hash'] = evidence_hash
        
        # Add to chain
        self.evidence_chain.append(evidence)
        
        # Integrate with DecisionLedger if enabled
        if self.ledger:
            self.ledger.log(
                decision=f"Processed action for {actor}",
                metadata={
                    "evidence_hash": evidence_hash,
                    "constitutional_result": constitutional_check['result'],
                    "action_type": action if isinstance(action, str) else action.get('type', 'unknown')
                }
            )
        
        # Return: No verdict, only evidence
        return {
            'status': 'action_processed',
            'evidence_hash': evidence_hash,
            'voice_raised': False,
            'emotional_content': 0.0,
            'constitutional_check_result': constitutional_check['result'],
            'corrective_path': constitutional_check.get('corrective_path', None)
        }

    def process_action(self, actor, action, context):
        """DEPRECATED: Use jarus.core.surge_wrapper.SurgeWrapper instead."""
        # For backward compatibility during migration, we route to private method
        # but in production this would be removed or raised.
        return self._process_action(actor, action, context)
    
    def _constitutional_evaluation(self, action):
        """Evaluate against constitution without judgment"""
        violations = []
        
        # Normalize action to dict if it's a string
        action_data = action if isinstance(action, dict) else {"type": action}
        
        # Check 1: Grounding in physical reality
        if not action_data.get('physical_grounding'):
            violations.append({
                'code': 'C001',
                'description': 'Action lacks physical grounding',
                'severity': 'procedural',
                'not_emotional': True
            })
        
        # Check 2: Quantification requirement
        if not action_data.get('measurements'):
            violations.append({
                'code': 'C002',
                'description': 'Action lacks quantitative measurements',
                'severity': 'procedural',
                'not_emotional': True
            })
        
        # Check 3: Audit trail requirement
        if not action_data.get('audit_path'):
            violations.append({
                'code': 'C003',
                'description': 'Action lacks audit trail provision',
                'severity': 'procedural',
                'not_emotional': True
            })
        
        return {
            'violations': violations,
            'result': 'constitutional' if not violations else 'requires_correction',
            'corrective_path': self._generate_corrective_path(violations, action) if violations else None
        }

    def _cryptographic_timestamp(self):
        """Returns ISO 8601 UTC timestamp"""
        return datetime.now(timezone.utc).isoformat()

    def _capture_state(self):
        """Captures a pseudo-hash of current system state for recording"""
        # In a real system this might hash files, environment, etc.
        # For the demo, we use a deterministic value or hash of known params.
        state_data = "system_stable_0dB"
        return hashlib.sha256(state_data.encode()).hexdigest()

    def _execute_action(self, action):
        """Simulates action execution"""
        return {"execution": "success", "observed_impact": "minimal"}

    def _generate_hash(self, data):
        """Generates SHA256 hash of dict data"""
        encoded = json.dumps(data, sort_keys=True).encode()
        return f"SHA256:{hashlib.sha256(encoded).hexdigest()}"

    def _generate_corrective_path(self, violations, action=None):
        """Maps violations to corrective protocol paths"""
        if not violations:
            return None
        
        # Determine specific protocol based on action if available
        if action:
            action_type = action if isinstance(action, str) else action.get('type', '')
            if 'unauthorized' in action_type or 'access' in action_type:
                return '/correction/unauthorized_access_protocol'
            if 'alarm' in action_type:
                return '/correction/false_alarm_protocol'
        
        # Fallback to general codes
        codes = [v['code'] for v in violations]
        if 'C001' in codes or 'C002' in codes:
            return '/correction/quantification_protocol'
        return '/correction/general_procedural_protocol'

if __name__ == "__main__":
    # Self-test if run directly
    engine = ProceduralIndictmentEngine(ledger_integration=False)
    test_action = {
        "type": "file_access",
        "physical_grounding": True,
        "measurements": {"size": 1024},
        "audit_path": "logs/access.log"
    }
    result = engine.process_action("TestActor", test_action, {"context": "unit_test"})
    print(json.dumps(result, indent=4))
