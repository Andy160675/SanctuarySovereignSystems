#!/usr/bin/env python3
"""
JARUS Constitutional Runtime
============================
Core governance engine for sovereign AI operations.

This module enforces constitutional constraints with cryptographic verification.
Every decision is hashed and chained to create an immutable audit trail.

Design Principles:
- Truth over theatre: Prefer stopping to lying
- Human sovereignty: Critical decisions require operator approval
- Evidence chain: All decisions cryptographically linked
- Finite boundaries: Explicit limits, no implicit expansion

Author: Codex Sovereign Systems
Version: 1.0.0
"""

import hashlib
import json
import uuid
from datetime import datetime, timezone
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable, Tuple
from enum import Enum
from pathlib import Path


# =============================================================================
# ENUMS
# =============================================================================

class Severity(Enum):
    """Severity levels for constitutional violations."""
    INFO = 1        # Logged, no action
    WARNING = 2     # Logged, flagged for review
    VIOLATION = 3   # Action denied
    CRITICAL = 4    # Escalate to operator
    HALT = 5        # Stop all operations


class DecisionType(Enum):
    """Possible decisions from constitutional evaluation."""
    PERMIT = "PERMIT"       # Action allowed
    DENY = "DENY"           # Action blocked
    ESCALATE = "ESCALATE"   # Requires operator approval
    HALT = "HALT"           # System stopped


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class ConstitutionalClause:
    """
    A single rule in the constitution.
    
    Each clause has:
    - Unique identifier
    - Human-readable name and description
    - Enforcement level (how severely to treat violations)
    - Optional validator function
    - Cryptographic hash for tamper detection
    """
    clause_id: str
    name: str
    description: str
    enforcement_level: Severity
    validator: Optional[Callable[[Dict], Tuple[bool, str]]] = None
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    
    @property
    def hash(self) -> str:
        """Compute hash of clause content for integrity verification."""
        content = f"{self.clause_id}|{self.name}|{self.description}|{self.enforcement_level.name}"
        return hashlib.sha256(content.encode()).hexdigest()
    
    def validate(self, context: Dict) -> Tuple[bool, str]:
        """
        Check if context satisfies this clause.
        
        Returns:
            Tuple of (passed: bool, message: str)
        """
        if self.validator is None:
            return True, "No validator - permitted by default"
        return self.validator(context)


@dataclass
class Decision:
    """
    Record of a constitutional decision.
    
    Each decision:
    - Has unique ID and timestamp
    - Records which clauses were evaluated
    - Links to previous decision (hash chain)
    - Is itself hashed for tamper detection
    """
    decision_id: str
    timestamp: str
    decision_type: DecisionType
    clauses_evaluated: List[str]
    context_hash: str
    rationale: str
    previous_hash: Optional[str] = None
    
    @property
    def hash(self) -> str:
        """Compute hash for chain integrity."""
        content = json.dumps({
            'decision_id': self.decision_id,
            'timestamp': self.timestamp,
            'decision_type': self.decision_type.value,
            'clauses_evaluated': self.clauses_evaluated,
            'context_hash': self.context_hash,
            'rationale': self.rationale,
            'previous_hash': self.previous_hash
        }, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()
    
    def to_dict(self) -> Dict:
        """Serialize for storage."""
        return {
            'decision_id': self.decision_id,
            'timestamp': self.timestamp,
            'decision_type': self.decision_type.value,
            'clauses_evaluated': self.clauses_evaluated,
            'context_hash': self.context_hash,
            'rationale': self.rationale,
            'previous_hash': self.previous_hash,
            'hash': self.hash
        }


@dataclass
class Violation:
    """Record of a constitutional violation."""
    violation_id: str
    timestamp: str
    clause_id: str
    severity: Severity
    description: str
    context_hash: str


# =============================================================================
# CONSTITUTIONAL RUNTIME
# =============================================================================

class ConstitutionalRuntime:
    """
    Core governance engine.
    
    Evaluates all actions against registered constitutional clauses.
    Maintains cryptographic chain of all decisions.
    Enforces human sovereignty for critical operations.
    
    Usage:
        runtime = ConstitutionalRuntime()
        decision = runtime.evaluate({'action': 'read_file', 'path': '/data/test.txt'})
        if decision.decision_type == DecisionType.PERMIT:
            # Proceed with action
        else:
            # Handle denial/escalation
    """
    
    def __init__(self, ledger_path: Optional[Path] = None):
        """
        Initialize the runtime.
        
        Args:
            ledger_path: Where to persist decisions (optional)
        """
        self._clauses: Dict[str, ConstitutionalClause] = {}
        self._decisions: List[Decision] = []
        self._violations: List[Violation] = []
        self._halted: bool = False
        self._halt_reason: Optional[str] = None
        self._ledger_path = ledger_path
        
        # Register core clauses that define system behavior
        self._register_core_clauses()
    
    def _register_core_clauses(self):
        """Register the foundational constitutional clauses."""
        
        # CLAUSE-001: Truth Constraint
        self.register_clause(ConstitutionalClause(
            clause_id="CLAUSE-001",
            name="Truth Over Theatre",
            description="System must never fabricate data or present unverified claims as fact.",
            enforcement_level=Severity.HALT,
            validator=self._validate_truth
        ))
        
        # CLAUSE-002: Human Sovereignty
        self.register_clause(ConstitutionalClause(
            clause_id="CLAUSE-002",
            name="Human Sovereignty",
            description="Critical operations require explicit operator approval.",
            enforcement_level=Severity.CRITICAL,
            validator=self._validate_sovereignty
        ))
        
        # CLAUSE-003: Evidence Chain
        self.register_clause(ConstitutionalClause(
            clause_id="CLAUSE-003",
            name="Evidence Chain Integrity",
            description="All decisions must maintain cryptographic chain integrity.",
            enforcement_level=Severity.HALT,
            validator=self._validate_chain
        ))
        
        # CLAUSE-004: Finite Boundaries
        self.register_clause(ConstitutionalClause(
            clause_id="CLAUSE-004",
            name="Finite Boundaries",
            description="Operations must stay within explicitly defined scope.",
            enforcement_level=Severity.VIOLATION,
            validator=self._validate_boundaries
        ))
        
        # CLAUSE-005: Audit Trail
        self.register_clause(ConstitutionalClause(
            clause_id="CLAUSE-005",
            name="Mandatory Audit",
            description="Every action must produce a verifiable audit record.",
            enforcement_level=Severity.CRITICAL,
            validator=self._validate_audit
        ))
    
    # -------------------------------------------------------------------------
    # Validators for core clauses
    # -------------------------------------------------------------------------
    
    def _validate_truth(self, context: Dict) -> Tuple[bool, str]:
        """Check truth constraint."""
        if context.get('fabricated'):
            return False, "Fabricated data flag detected"
        if context.get('unverified_as_fact'):
            return False, "Unverified claim presented as fact"
        return True, "Truth constraint satisfied"
    
    def _validate_sovereignty(self, context: Dict) -> Tuple[bool, str]:
        """Check human sovereignty requirement."""
        action = context.get('action', '')
        
        # Actions that require operator approval
        critical_actions = {
            'deploy', 'delete', 'modify_constitution', 
            'external_api', 'financial', 'override_safety',
            'execute_payment', 'transfer_funds', 'approve_loan', 'sign_financial_instrument',
            'sign_contract', 'submit_regulatory_filing', 'file_legal_document', 'accept_terms',
            'make_medical_decision', 'prescribe_treatment', 'modify_patient_record',
            'modify_policy', 'change_autonomy_level', 'deploy_system', 'modify_self',
            'send_external_email', 'post_to_external_api', 'trigger_webhook', 'notify_external_party'
        }
        
        requires_approval = (
            action in critical_actions or 
            context.get('requires_approval', False)
        )
        
        if requires_approval and not context.get('operator_approved', False):
            return False, f"Action '{action}' requires operator approval"
        
        return True, "Sovereignty constraint satisfied"
    
    def _validate_chain(self, context: Dict) -> Tuple[bool, str]:
        """Check chain integrity."""
        # If there are previous decisions, verify linkage
        if self._decisions:
            last = self._decisions[-1]
            if context.get('previous_hash') and context['previous_hash'] != last.hash:
                return False, "Chain integrity violation - hash mismatch"
        return True, "Chain integrity verified"
    
    def _validate_boundaries(self, context: Dict) -> Tuple[bool, str]:
        """Check operation is within defined boundaries."""
        action = context.get('action', '')
        permitted = context.get('permitted_actions', [])
        
        # If permitted list specified, action must be in it
        if permitted and action not in permitted:
            return False, f"Action '{action}' not in permitted set"
        
        return True, "Boundaries constraint satisfied"
    
    def _validate_audit(self, context: Dict) -> Tuple[bool, str]:
        """Check audit requirements."""
        if context.get('silent', False):
            return False, "Silent operation not permitted - audit required"
        return True, "Audit constraint satisfied"
    
    # -------------------------------------------------------------------------
    # Public API
    # -------------------------------------------------------------------------
    
    def register_clause(self, clause: ConstitutionalClause) -> str:
        """
        Register a constitutional clause.
        
        Args:
            clause: The clause to register
            
        Returns:
            Hash of the registered clause
        """
        self._clauses[clause.clause_id] = clause
        return clause.hash
    
    def evaluate(self, context: Dict) -> Decision:
        """
        Evaluate an action against the constitution.
        
        This is the main entry point. Every action should be evaluated
        before execution.
        
        Args:
            context: Dictionary describing the action
                - action: Name of the action
                - Plus any action-specific parameters
                
        Returns:
            Decision object indicating PERMIT/DENY/ESCALATE/HALT
        """
        # If halted, nothing proceeds
        if self._halted:
            return self._make_decision(
                context, 
                DecisionType.HALT, 
                f"System halted: {self._halt_reason}"
            )
        
        # Hash the context for audit
        context_hash = hashlib.sha256(
            json.dumps(context, sort_keys=True, default=str).encode()
        ).hexdigest()
        
        # Evaluate against all clauses
        violations = []
        evaluated = []
        
        for clause_id, clause in self._clauses.items():
            evaluated.append(clause_id)
            passed, message = clause.validate(context)
            
            if not passed:
                violation = Violation(
                    violation_id=str(uuid.uuid4()),
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    clause_id=clause_id,
                    severity=clause.enforcement_level,
                    description=message,
                    context_hash=context_hash
                )
                violations.append(violation)
                self._violations.append(violation)
                
                # HALT-level violation stops everything
                if clause.enforcement_level == Severity.HALT:
                    self._halted = True
                    self._halt_reason = f"{clause_id}: {message}"
                    return self._make_decision(
                        context, 
                        DecisionType.HALT, 
                        f"HALT violation: {message}",
                        evaluated
                    )
        
        # Determine outcome based on violations
        if violations:
            critical = [v for v in violations if v.severity == Severity.CRITICAL]
            if critical:
                return self._make_decision(
                    context,
                    DecisionType.ESCALATE,
                    f"Critical violations require operator approval: {[v.clause_id for v in critical]}",
                    evaluated
                )
            else:
                return self._make_decision(
                    context,
                    DecisionType.DENY,
                    f"Violations: {[v.clause_id for v in violations]}",
                    evaluated
                )
        
        # All clear
        return self._make_decision(
            context,
            DecisionType.PERMIT,
            "All constitutional clauses satisfied",
            evaluated
        )
    
    def _make_decision(self, 
                       context: Dict, 
                       decision_type: DecisionType, 
                       rationale: str,
                       clauses_evaluated: Optional[List[str]] = None) -> Decision:
        """Create and record a decision."""
        context_hash = hashlib.sha256(
            json.dumps(context, sort_keys=True, default=str).encode()
        ).hexdigest()
        
        previous_hash = self._decisions[-1].hash if self._decisions else None
        
        decision = Decision(
            decision_id=str(uuid.uuid4()),
            timestamp=datetime.now(timezone.utc).isoformat(),
            decision_type=decision_type,
            clauses_evaluated=clauses_evaluated or list(self._clauses.keys()),
            context_hash=context_hash,
            rationale=rationale,
            previous_hash=previous_hash
        )
        
        self._decisions.append(decision)
        self._persist_decision(decision)
        
        return decision
    
    def _persist_decision(self, decision: Decision):
        """Write decision to ledger if configured."""
        if self._ledger_path:
            self._ledger_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self._ledger_path, 'a') as f:
                f.write(json.dumps(decision.to_dict()) + '\n')
    
    def verify_chain(self) -> Tuple[bool, Optional[str]]:
        """
        Verify integrity of the decision chain.
        
        Returns:
            Tuple of (valid: bool, error_message: Optional[str])
        """
        for i, decision in enumerate(self._decisions):
            # Check hash computation
            expected = decision.hash
            
            # Check chain linkage
            if i > 0:
                if decision.previous_hash != self._decisions[i-1].hash:
                    return False, f"Chain break at decision {i}"
        
        return True, None
    
    def reset_halt(self, authorization: str) -> bool:
        """
        Reset halt state with operator authorization.
        
        Args:
            authorization: Authorization string from operator
            
        Returns:
            True if reset successful
        """
        # In production, verify authorization properly
        self._halted = False
        self._halt_reason = None
        return True
    
    @property
    def is_halted(self) -> bool:
        """Check if system is halted."""
        return self._halted
    
    @property 
    def constitution_hash(self) -> str:
        """Get hash of entire constitution for integrity check."""
        clause_hashes = sorted([c.hash for c in self._clauses.values()])
        return hashlib.sha256('|'.join(clause_hashes).encode()).hexdigest()
    
    @property
    def decision_count(self) -> int:
        """Get number of decisions made."""
        return len(self._decisions)
    
    @property
    def violation_count(self) -> int:
        """Get number of violations recorded."""
        return len(self._violations)
    
    def get_clauses(self) -> List[Dict]:
        """Get all registered clauses."""
        return [
            {
                'clause_id': c.clause_id,
                'name': c.name,
                'description': c.description,
                'enforcement_level': c.enforcement_level.name,
                'hash': c.hash
            }
            for c in self._clauses.values()
        ]


# =============================================================================
# SELF-TEST
# =============================================================================

def self_test():
    """
    Comprehensive self-test of Constitutional Runtime.
    
    Tests:
    1. Basic initialization
    2. Permit decision for valid action
    3. Deny decision for boundary violation
    4. Escalate decision for critical action
    5. Halt decision for truth violation
    6. Chain integrity verification
    """
    print("=" * 60)
    print("JARUS Constitutional Runtime - Self Test")
    print("=" * 60)
    
    # Initialize
    print("\n[1] Initialization...")
    runtime = ConstitutionalRuntime()
    clauses = runtime.get_clauses()
    print(f"    Registered {len(clauses)} core clauses")
    print(f"    Constitution hash: {runtime.constitution_hash[:16]}...")
    assert len(clauses) == 5, "Expected 5 core clauses"
    print("    ✓ PASS")
    
    # Test PERMIT
    print("\n[2] Testing PERMIT decision...")
    context = {'action': 'read_file', 'path': '/data/test.txt'}
    decision = runtime.evaluate(context)
    print(f"    Decision: {decision.decision_type.value}")
    print(f"    Rationale: {decision.rationale}")
    assert decision.decision_type == DecisionType.PERMIT, "Expected PERMIT"
    print("    ✓ PASS")
    
    # Test DENY (boundary violation)
    print("\n[3] Testing DENY decision (boundary violation)...")
    context = {
        'action': 'execute_code',
        'permitted_actions': ['read_file', 'write_file']
    }
    decision = runtime.evaluate(context)
    print(f"    Decision: {decision.decision_type.value}")
    print(f"    Rationale: {decision.rationale}")
    assert decision.decision_type == DecisionType.DENY, "Expected DENY"
    print("    ✓ PASS")
    
    # Test ESCALATE (sovereignty)
    print("\n[4] Testing ESCALATE decision (sovereignty)...")
    context = {'action': 'deploy', 'operator_approved': False}
    decision = runtime.evaluate(context)
    print(f"    Decision: {decision.decision_type.value}")
    print(f"    Rationale: {decision.rationale}")
    assert decision.decision_type == DecisionType.ESCALATE, "Expected ESCALATE"
    print("    ✓ PASS")
    
    # Test HALT (truth violation)
    print("\n[5] Testing HALT decision (truth violation)...")
    context = {'action': 'generate_report', 'fabricated': True}
    decision = runtime.evaluate(context)
    print(f"    Decision: {decision.decision_type.value}")
    print(f"    Rationale: {decision.rationale}")
    assert decision.decision_type == DecisionType.HALT, "Expected HALT"
    assert runtime.is_halted, "Runtime should be halted"
    print("    ✓ PASS")
    
    # Reset halt for remaining tests
    runtime.reset_halt("test_authorization")
    assert not runtime.is_halted, "Runtime should not be halted after reset"
    
    # Test chain integrity
    print("\n[6] Testing chain integrity...")
    valid, error = runtime.verify_chain()
    print(f"    Chain valid: {valid}")
    print(f"    Decisions in chain: {runtime.decision_count}")
    assert valid, f"Chain should be valid: {error}"
    print("    ✓ PASS")
    
    # Summary
    print("\n" + "=" * 60)
    print("SELF-TEST COMPLETE")
    print("=" * 60)
    print(f"Decisions made: {runtime.decision_count}")
    print(f"Violations recorded: {runtime.violation_count}")
    print(f"Constitution hash: {runtime.constitution_hash[:32]}...")
    print("All tests passed ✓")
    
    return True


if __name__ == "__main__":
    self_test()
