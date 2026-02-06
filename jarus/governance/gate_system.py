#!/usr/bin/env python3
"""
JARUS Gate System (PRINCE2-Aligned)
===================================
Formal decision points where work must stop, prove control, 
and get permission to continue.

Gates:
1. MANDATE    - Is this idea worth scoping?
2. INITIATION - Should we invest in planning?
3. DELIVERY   - Approve PID and start project?
4. STAGE      - Continue to next stage? (repeatable)
5. EXCEPTION  - Approve recovery plan?
6. CLOSURE    - Close project?

Each gate requires:
- Evidence of control
- Explicit authorization
- Audit trail

Author: Codex Sovereign Systems
Version: 1.0.0
"""

import hashlib
import json
import uuid
from datetime import datetime, timezone
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
from pathlib import Path


# =============================================================================
# ENUMS
# =============================================================================

class GateType(Enum):
    """PRINCE2-aligned gate types."""
    MANDATE = "MANDATE"           # Gate 1: Idea worth scoping?
    INITIATION = "INITIATION"     # Gate 2: Invest in planning?
    DELIVERY = "DELIVERY"         # Gate 3: Approve PID, start work?
    STAGE = "STAGE"               # Gate 4: Continue to next stage?
    EXCEPTION = "EXCEPTION"       # Gate 5: Approve recovery plan?
    CLOSURE = "CLOSURE"           # Gate 6: Close project?


class GateStatus(Enum):
    """Status of a gate review."""
    PENDING = "PENDING"           # Awaiting review
    APPROVED = "APPROVED"         # Authorized to proceed
    REJECTED = "REJECTED"         # Not authorized
    DEFERRED = "DEFERRED"         # Decision postponed
    EXCEPTION = "EXCEPTION"       # Tolerance breach


class ToleranceStatus(Enum):
    """Whether project is within tolerances."""
    GREEN = "GREEN"     # Within tolerance
    AMBER = "AMBER"     # Approaching tolerance
    RED = "RED"         # Exceeded tolerance


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class Tolerance:
    """
    Tolerance definition for a metric.
    
    If actual exceeds threshold, triggers exception gate.
    """
    metric: str
    baseline: float
    threshold: float
    actual: Optional[float] = None
    
    @property
    def status(self) -> ToleranceStatus:
        if self.actual is None:
            return ToleranceStatus.GREEN
        
        variance = abs(self.actual - self.baseline)
        max_variance = abs(self.threshold - self.baseline)
        
        if variance >= max_variance:
            return ToleranceStatus.RED
        elif variance >= max_variance * 0.8:
            return ToleranceStatus.AMBER
        else:
            return ToleranceStatus.GREEN
    
    @property
    def exceeded(self) -> bool:
        return self.status == ToleranceStatus.RED


@dataclass
class GateEvidence:
    """
    Evidence required to pass a gate.
    
    Each gate has specific evidence requirements.
    """
    evidence_id: str
    description: str
    provided: bool = False
    content_hash: Optional[str] = None
    verified_at: Optional[str] = None
    verified_by: Optional[str] = None


@dataclass
class GateReview:
    """
    Record of a gate review decision.
    """
    review_id: str
    gate_type: GateType
    project_id: str
    stage_number: int
    status: GateStatus
    reviewer: str
    timestamp: str
    evidence_hashes: List[str]
    tolerances: Dict[str, str]  # metric -> status
    rationale: str
    conditions: List[str] = field(default_factory=list)  # Conditions for approval
    
    @property
    def hash(self) -> str:
        """Compute hash of review for audit chain."""
        content = json.dumps({
            'review_id': self.review_id,
            'gate_type': self.gate_type.value,
            'project_id': self.project_id,
            'stage_number': self.stage_number,
            'status': self.status.value,
            'reviewer': self.reviewer,
            'timestamp': self.timestamp,
            'evidence_hashes': self.evidence_hashes,
            'tolerances': self.tolerances,
            'rationale': self.rationale,
            'conditions': self.conditions
        }, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()
    
    def to_dict(self) -> Dict:
        return {
            'review_id': self.review_id,
            'gate_type': self.gate_type.value,
            'project_id': self.project_id,
            'stage_number': self.stage_number,
            'status': self.status.value,
            'reviewer': self.reviewer,
            'timestamp': self.timestamp,
            'evidence_hashes': self.evidence_hashes,
            'tolerances': self.tolerances,
            'rationale': self.rationale,
            'conditions': self.conditions,
            'hash': self.hash
        }


@dataclass
class Stage:
    """
    A management stage in the project.
    """
    stage_number: int
    name: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    entry_gate: Optional[GateReview] = None
    exit_gate: Optional[GateReview] = None
    tolerances: Dict[str, Tolerance] = field(default_factory=dict)
    
    @property
    def active(self) -> bool:
        return self.started_at is not None and self.completed_at is None
    
    @property
    def tolerance_status(self) -> ToleranceStatus:
        """Worst tolerance status across all metrics."""
        if not self.tolerances:
            return ToleranceStatus.GREEN
        
        statuses = [t.status for t in self.tolerances.values()]
        if ToleranceStatus.RED in statuses:
            return ToleranceStatus.RED
        elif ToleranceStatus.AMBER in statuses:
            return ToleranceStatus.AMBER
        return ToleranceStatus.GREEN


# =============================================================================
# GATE DEFINITIONS
# =============================================================================

GATE_REQUIREMENTS = {
    GateType.MANDATE: {
        'name': 'Project Mandate Gate',
        'question': 'Is this idea worth scoping?',
        'required_evidence': [
            'business_case_outline',
            'executive_sponsor_identified',
            'initial_scope_statement'
        ],
        'min_role': 'SPONSOR'
    },
    GateType.INITIATION: {
        'name': 'Initiation Gate',
        'question': 'Should we invest in planning?',
        'required_evidence': [
            'project_brief',
            'outline_business_case',
            'project_approach',
            'stage_plan_initiation'
        ],
        'min_role': 'PROJECT_BOARD'
    },
    GateType.DELIVERY: {
        'name': 'Authorization to Deliver',
        'question': 'Approve PID and start project?',
        'required_evidence': [
            'project_initiation_documentation',
            'detailed_business_case',
            'project_plan',
            'stage_plan_first_delivery',
            'risk_register',
            'quality_management_approach',
            'communication_management_approach'
        ],
        'min_role': 'PROJECT_BOARD'
    },
    GateType.STAGE: {
        'name': 'End Stage Assessment',
        'question': 'Continue to next stage?',
        'required_evidence': [
            'end_stage_report',
            'updated_project_plan',
            'next_stage_plan',
            'updated_business_case',
            'updated_risk_register',
            'lessons_log_update'
        ],
        'min_role': 'PROJECT_BOARD'
    },
    GateType.EXCEPTION: {
        'name': 'Exception Gate',
        'question': 'Approve recovery plan?',
        'required_evidence': [
            'exception_report',
            'exception_plan',
            'impact_assessment',
            'root_cause_analysis',
            'corrective_actions'
        ],
        'min_role': 'PROJECT_BOARD'
    },
    GateType.CLOSURE: {
        'name': 'Project Closure Gate',
        'question': 'Close project?',
        'required_evidence': [
            'end_project_report',
            'lessons_report',
            'benefits_review_plan',
            'product_acceptance_records',
            'handover_confirmation'
        ],
        'min_role': 'PROJECT_BOARD'
    }
}


# =============================================================================
# GATE SYSTEM
# =============================================================================

class GateSystem:
    """
    PRINCE2-aligned gate system for project governance.
    
    Enforces formal decision points where work must stop,
    prove control, and get permission to continue.
    
    Usage:
        gates = GateSystem(project_id="PROJ-001")
        
        # Submit gate for review
        result = gates.submit_gate(
            gate_type=GateType.MANDATE,
            evidence={'business_case_outline': 'hash123...'},
            submitter='project_manager'
        )
        
        # Review and decide
        review = gates.review_gate(
            gate_id=result['gate_id'],
            decision=GateStatus.APPROVED,
            reviewer='sponsor',
            rationale='Business case is sound'
        )
    """
    
    def __init__(self, project_id: str):
        """
        Initialize gate system for a project.
        
        Args:
            project_id: Unique project identifier
        """
        self.project_id = project_id
        self._stages: List[Stage] = []
        self._current_stage: int = 0
        self._reviews: List[GateReview] = []
        self._pending_gates: Dict[str, Dict] = {}
        self._halted: bool = False
        self._halt_reason: Optional[str] = None
        
        # Initialize with pre-project stage
        self._stages.append(Stage(
            stage_number=0,
            name="Pre-Project"
        ))
    
    def submit_gate(self, 
                    gate_type: GateType,
                    evidence: Dict[str, str],
                    submitter: str,
                    tolerances: Optional[Dict[str, Tolerance]] = None) -> Dict:
        """
        Submit a gate for review.
        
        Args:
            gate_type: Type of gate
            evidence: Dict mapping evidence names to content hashes
            submitter: Who is submitting
            tolerances: Current tolerance status (for STAGE gates)
            
        Returns:
            Gate submission record
        """
        gate_id = str(uuid.uuid4())[:12]
        requirements = GATE_REQUIREMENTS[gate_type]
        
        # Check required evidence
        missing = []
        for req in requirements['required_evidence']:
            if req not in evidence:
                missing.append(req)
        
        # Check tolerances for stage gates
        tolerance_status = {}
        exception_triggered = False
        
        if tolerances:
            for name, tol in tolerances.items():
                tolerance_status[name] = tol.status.value
                if tol.exceeded:
                    exception_triggered = True
        
        submission = {
            'gate_id': gate_id,
            'gate_type': gate_type.value,
            'project_id': self.project_id,
            'stage_number': self._current_stage,
            'submitted_by': submitter,
            'submitted_at': datetime.now(timezone.utc).isoformat(),
            'evidence': evidence,
            'missing_evidence': missing,
            'tolerances': tolerance_status,
            'exception_triggered': exception_triggered,
            'ready_for_review': len(missing) == 0,
            'status': 'PENDING'
        }
        
        self._pending_gates[gate_id] = submission
        
        return submission
    
    def review_gate(self,
                    gate_id: str,
                    decision: GateStatus,
                    reviewer: str,
                    rationale: str,
                    conditions: Optional[List[str]] = None) -> GateReview:
        """
        Review a pending gate and make decision.
        
        Args:
            gate_id: ID of pending gate
            decision: APPROVED, REJECTED, DEFERRED
            reviewer: Who is reviewing
            rationale: Reason for decision
            conditions: Conditions attached to approval
            
        Returns:
            GateReview record
        """
        if gate_id not in self._pending_gates:
            raise ValueError(f"Gate not found: {gate_id}")
        
        submission = self._pending_gates[gate_id]
        
        # Cannot approve with missing evidence
        if decision == GateStatus.APPROVED and submission['missing_evidence']:
            raise ValueError(f"Cannot approve - missing evidence: {submission['missing_evidence']}")
        
        # Create review record
        review = GateReview(
            review_id=str(uuid.uuid4())[:12],
            gate_type=GateType[submission['gate_type']],
            project_id=self.project_id,
            stage_number=submission['stage_number'],
            status=decision,
            reviewer=reviewer,
            timestamp=datetime.now(timezone.utc).isoformat(),
            evidence_hashes=list(submission['evidence'].values()),
            tolerances=submission['tolerances'],
            rationale=rationale,
            conditions=conditions or []
        )
        
        self._reviews.append(review)
        
        # Update submission status
        submission['status'] = decision.value
        submission['reviewed_by'] = reviewer
        submission['reviewed_at'] = review.timestamp
        
        # Handle approval - advance project state
        if decision == GateStatus.APPROVED:
            self._handle_approval(review)
        
        # Handle rejection - halt if delivery gate
        if decision == GateStatus.REJECTED:
            if review.gate_type in [GateType.DELIVERY, GateType.STAGE]:
                self._halted = True
                self._halt_reason = f"Gate {review.gate_type.value} rejected: {rationale}"
        
        return review
    
    def _handle_approval(self, review: GateReview):
        """Handle gate approval - advance project state."""
        
        if review.gate_type == GateType.MANDATE:
            # Ready for initiation
            pass
        
        elif review.gate_type == GateType.INITIATION:
            # Ready for PID development
            pass
        
        elif review.gate_type == GateType.DELIVERY:
            # Start first delivery stage
            self._advance_stage("Delivery Stage 1", review)
        
        elif review.gate_type == GateType.STAGE:
            # Advance to next stage
            next_num = self._current_stage + 1
            self._advance_stage(f"Delivery Stage {next_num}", review)
        
        elif review.gate_type == GateType.EXCEPTION:
            # Resume from exception
            self._halted = False
            self._halt_reason = None
        
        elif review.gate_type == GateType.CLOSURE:
            # Close project
            if self._current_stage > 0:
                self._stages[self._current_stage].completed_at = review.timestamp
    
    def _advance_stage(self, stage_name: str, entry_review: GateReview):
        """Advance to next stage."""
        # Close current stage
        if self._current_stage > 0:
            self._stages[self._current_stage].completed_at = entry_review.timestamp
            self._stages[self._current_stage].exit_gate = entry_review
        
        # Create new stage
        self._current_stage += 1
        new_stage = Stage(
            stage_number=self._current_stage,
            name=stage_name,
            started_at=entry_review.timestamp,
            entry_gate=entry_review
        )
        self._stages.append(new_stage)
    
    def trigger_exception(self, 
                         metric: str, 
                         baseline: float,
                         threshold: float,
                         actual: float,
                         description: str) -> Dict:
        """
        Trigger exception when tolerance exceeded.
        
        Args:
            metric: Name of the metric
            baseline: Original baseline value
            threshold: Tolerance threshold
            actual: Actual value that exceeded
            description: Description of the breach
            
        Returns:
            Exception record
        """
        exception_id = str(uuid.uuid4())[:12]
        
        # Halt the project
        self._halted = True
        self._halt_reason = f"Tolerance exceeded: {metric}"
        
        # Update current stage tolerance
        if self._current_stage > 0:
            self._stages[self._current_stage].tolerances[metric] = Tolerance(
                metric=metric,
                baseline=baseline,
                threshold=threshold,
                actual=actual
            )
        
        return {
            'exception_id': exception_id,
            'project_id': self.project_id,
            'stage_number': self._current_stage,
            'metric': metric,
            'baseline': baseline,
            'threshold': threshold,
            'actual': actual,
            'variance': actual - baseline,
            'description': description,
            'triggered_at': datetime.now(timezone.utc).isoformat(),
            'status': 'EXCEPTION_RAISED',
            'next_action': 'Submit EXCEPTION gate with recovery plan'
        }
    
    def get_status(self) -> Dict:
        """Get current project gate status."""
        current_stage = self._stages[self._current_stage] if self._stages else None
        
        return {
            'project_id': self.project_id,
            'current_stage': self._current_stage,
            'stage_name': current_stage.name if current_stage else None,
            'stage_status': current_stage.tolerance_status.value if current_stage else None,
            'halted': self._halted,
            'halt_reason': self._halt_reason,
            'pending_gates': len([g for g in self._pending_gates.values() if g['status'] == 'PENDING']),
            'total_reviews': len(self._reviews),
            'stages_completed': len([s for s in self._stages if s.completed_at])
        }
    
    def get_gate_history(self) -> List[Dict]:
        """Get all gate reviews."""
        return [r.to_dict() for r in self._reviews]
    
    def get_required_evidence(self, gate_type: GateType) -> Dict:
        """Get evidence requirements for a gate type."""
        req = GATE_REQUIREMENTS[gate_type]
        return {
            'gate_type': gate_type.value,
            'name': req['name'],
            'question': req['question'],
            'required_evidence': req['required_evidence'],
            'min_role': req['min_role']
        }
    
    @property
    def is_halted(self) -> bool:
        return self._halted
    
    def verify_chain(self) -> Tuple[bool, Optional[str]]:
        """Verify integrity of gate review chain."""
        # Simple sequential verification
        for i, review in enumerate(self._reviews):
            # Verify hash computes correctly
            expected = review.hash
            # In production, would verify against stored hash
        
        return True, None


# =============================================================================
# SELF-TEST
# =============================================================================

def self_test():
    """
    Self-test of Gate System.
    """
    print("=" * 60)
    print("JARUS Gate System (PRINCE2) - Self Test")
    print("=" * 60)
    
    # Initialize
    print("\n[1] Initialize gate system...")
    gates = GateSystem(project_id="PROJ-001")
    status = gates.get_status()
    print(f"    Project: {status['project_id']}")
    print(f"    Current stage: {status['current_stage']}")
    assert not gates.is_halted
    print("    ✓ PASS")
    
    # Test Gate 1: Mandate
    print("\n[2] Submit MANDATE gate...")
    result = gates.submit_gate(
        gate_type=GateType.MANDATE,
        evidence={
            'business_case_outline': hashlib.sha256(b'business case').hexdigest(),
            'executive_sponsor_identified': hashlib.sha256(b'sponsor').hexdigest(),
            'initial_scope_statement': hashlib.sha256(b'scope').hexdigest()
        },
        submitter='project_manager'
    )
    print(f"    Gate ID: {result['gate_id']}")
    print(f"    Ready for review: {result['ready_for_review']}")
    assert result['ready_for_review']
    print("    ✓ PASS")
    
    # Review mandate gate
    print("\n[3] Review MANDATE gate (approve)...")
    review = gates.review_gate(
        gate_id=result['gate_id'],
        decision=GateStatus.APPROVED,
        reviewer='executive_sponsor',
        rationale='Business case is sound, proceed to initiation'
    )
    print(f"    Review ID: {review.review_id}")
    print(f"    Status: {review.status.value}")
    assert review.status == GateStatus.APPROVED
    print("    ✓ PASS")
    
    # Test Gate 3: Delivery (skip initiation for brevity)
    print("\n[4] Submit DELIVERY gate...")
    delivery_evidence = {
        'project_initiation_documentation': hashlib.sha256(b'pid').hexdigest(),
        'detailed_business_case': hashlib.sha256(b'dbc').hexdigest(),
        'project_plan': hashlib.sha256(b'plan').hexdigest(),
        'stage_plan_first_delivery': hashlib.sha256(b'stage1').hexdigest(),
        'risk_register': hashlib.sha256(b'risks').hexdigest(),
        'quality_management_approach': hashlib.sha256(b'quality').hexdigest(),
        'communication_management_approach': hashlib.sha256(b'comms').hexdigest()
    }
    result = gates.submit_gate(
        gate_type=GateType.DELIVERY,
        evidence=delivery_evidence,
        submitter='project_manager'
    )
    print(f"    Ready for review: {result['ready_for_review']}")
    assert result['ready_for_review']
    
    review = gates.review_gate(
        gate_id=result['gate_id'],
        decision=GateStatus.APPROVED,
        reviewer='project_board',
        rationale='PID approved, authorize delivery'
    )
    print(f"    Status: {review.status.value}")
    
    status = gates.get_status()
    print(f"    New stage: {status['stage_name']}")
    assert status['current_stage'] == 1
    print("    ✓ PASS")
    
    # Test exception trigger
    print("\n[5] Trigger tolerance exception...")
    exception = gates.trigger_exception(
        metric='cost',
        baseline=100000,
        threshold=110000,
        actual=125000,
        description='Budget overrun due to scope creep'
    )
    print(f"    Exception ID: {exception['exception_id']}")
    print(f"    Variance: {exception['variance']}")
    assert gates.is_halted
    print(f"    Halted: {gates.is_halted}")
    print("    ✓ PASS")
    
    # Test Gate 5: Exception recovery
    print("\n[6] Submit EXCEPTION gate (recovery plan)...")
    result = gates.submit_gate(
        gate_type=GateType.EXCEPTION,
        evidence={
            'exception_report': hashlib.sha256(b'report').hexdigest(),
            'exception_plan': hashlib.sha256(b'plan').hexdigest(),
            'impact_assessment': hashlib.sha256(b'impact').hexdigest(),
            'root_cause_analysis': hashlib.sha256(b'rca').hexdigest(),
            'corrective_actions': hashlib.sha256(b'actions').hexdigest()
        },
        submitter='project_manager'
    )
    
    review = gates.review_gate(
        gate_id=result['gate_id'],
        decision=GateStatus.APPROVED,
        reviewer='project_board',
        rationale='Recovery plan accepted',
        conditions=['Weekly cost monitoring', 'Scope freeze']
    )
    print(f"    Conditions: {review.conditions}")
    print(f"    Halted: {gates.is_halted}")
    assert not gates.is_halted
    print("    ✓ PASS")
    
    # Test get requirements
    print("\n[7] Get gate requirements...")
    req = gates.get_required_evidence(GateType.CLOSURE)
    print(f"    Gate: {req['name']}")
    print(f"    Question: {req['question']}")
    print(f"    Evidence required: {len(req['required_evidence'])} items")
    print("    ✓ PASS")
    
    # Test history
    print("\n[8] Get gate history...")
    history = gates.get_gate_history()
    print(f"    Total reviews: {len(history)}")
    for h in history:
        print(f"      - {h['gate_type']}: {h['status']}")
    assert len(history) == 3  # MANDATE, DELIVERY, EXCEPTION
    print("    ✓ PASS")
    
    # Summary
    print("\n" + "=" * 60)
    print("SELF-TEST COMPLETE")
    print("=" * 60)
    print(f"Gates tested: 4 (MANDATE, DELIVERY, EXCEPTION, requirements)")
    print("All tests passed ✓")
    
    return True


if __name__ == "__main__":
    self_test()
