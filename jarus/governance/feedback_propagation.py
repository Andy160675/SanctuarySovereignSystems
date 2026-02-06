#!/usr/bin/env python3
"""
JARUS Feedback Propagation System
==================================
The circulatory system: fix + feedback propagation, then reset and resume.

Canonical Loop:
    Gemba → Audit → HALT → Fix → Feedback → Acknowledge → Reset → Resume

Every fix produces learning.
Every learning is propagated.
Every node restarts with the new truth.
No node is allowed to "carry on as before."

Author: Codex Sovereign Systems
Version: 1.0.0
"""

import hashlib
import json
import uuid
from datetime import datetime, timezone
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Set
from enum import Enum


# =============================================================================
# ENUMS
# =============================================================================

class SystemState(Enum):
    """System execution state."""
    RUN = "RUN"               # Normal operation
    HALT = "HALT"             # Stopped due to violation
    PROPAGATING = "PROPAGATING"  # Broadcasting alert
    RESETTING = "RESETTING"   # Applying new invariants


class ObservationType(Enum):
    """Type of gemba observation."""
    NEAR_MISS = "NEAR_MISS"       # Boundary approached but not crossed
    VIOLATION = "VIOLATION"        # Boundary crossed
    ANOMALY = "ANOMALY"            # Unexpected pattern
    POSITIVE = "POSITIVE"          # Good practice observed


class AcknowledgementStatus(Enum):
    """Node acknowledgement status."""
    PENDING = "PENDING"       # Alert sent, no response
    RECEIVED = "RECEIVED"     # Node received alert
    APPLIED = "APPLIED"       # Node applied the update
    FAILED = "FAILED"         # Node failed to apply
    TIMEOUT = "TIMEOUT"       # No response in time


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class GembaObservation:
    """
    Observation captured at point of work.
    
    No abstraction. Raw evidence from where work happens.
    """
    observation_id: str
    observation_type: ObservationType
    timestamp: str
    node_id: str
    boundary_id: Optional[str]
    description: str
    evidence_hash: str
    raw_data: Dict
    
    @property
    def hash(self) -> str:
        content = json.dumps({
            'observation_id': self.observation_id,
            'observation_type': self.observation_type.value,
            'timestamp': self.timestamp,
            'node_id': self.node_id,
            'boundary_id': self.boundary_id,
            'evidence_hash': self.evidence_hash
        }, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()
    
    def to_dict(self) -> Dict:
        return {
            'observation_id': self.observation_id,
            'observation_type': self.observation_type.value,
            'timestamp': self.timestamp,
            'node_id': self.node_id,
            'boundary_id': self.boundary_id,
            'description': self.description,
            'evidence_hash': self.evidence_hash,
            'hash': self.hash
        }


@dataclass
class Fix:
    """
    Surgical, scoped fix for a boundary violation.
    
    Maps explicitly to:
    - Which boundary
    - Which failure mode
    - Which evidence
    
    No opportunistic changes. No scope creep.
    """
    fix_id: str
    incident_id: str
    boundary_id: str
    failure_mode: str
    evidence_hashes: List[str]
    description: str
    guard_update: Optional[Dict]      # New guard condition
    rule_update: Optional[Dict]       # New rule
    constraint_update: Optional[Dict] # New constraint
    applied_at: str
    applied_by: str
    verified: bool = False
    verified_at: Optional[str] = None
    
    @property
    def hash(self) -> str:
        content = json.dumps({
            'fix_id': self.fix_id,
            'incident_id': self.incident_id,
            'boundary_id': self.boundary_id,
            'failure_mode': self.failure_mode,
            'evidence_hashes': self.evidence_hashes,
            'guard_update': self.guard_update,
            'rule_update': self.rule_update,
            'constraint_update': self.constraint_update
        }, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()
    
    def to_dict(self) -> Dict:
        return {
            'fix_id': self.fix_id,
            'incident_id': self.incident_id,
            'boundary_id': self.boundary_id,
            'failure_mode': self.failure_mode,
            'description': self.description,
            'applied_at': self.applied_at,
            'applied_by': self.applied_by,
            'verified': self.verified,
            'hash': self.hash
        }


@dataclass
class AlertUpdate:
    """
    Broadcast to all nodes when a fix is validated.
    
    This is not optional and not passive.
    """
    alert_id: str
    incident_id: str
    observation_summary: str          # What was observed at gemba
    boundary_id: str                  # Boundary involved
    change_description: str           # What changed
    guard_update: Optional[Dict]
    rule_update: Optional[Dict]
    constraint_update: Optional[Dict]
    effective_timestamp: str
    required_actions: List[str]       # Required local actions
    fix_hash: str                     # Hash of the fix for verification
    
    @property
    def hash(self) -> str:
        content = json.dumps({
            'alert_id': self.alert_id,
            'incident_id': self.incident_id,
            'boundary_id': self.boundary_id,
            'change_description': self.change_description,
            'effective_timestamp': self.effective_timestamp,
            'fix_hash': self.fix_hash
        }, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()
    
    def to_dict(self) -> Dict:
        return {
            'alert_id': self.alert_id,
            'incident_id': self.incident_id,
            'observation_summary': self.observation_summary,
            'boundary_id': self.boundary_id,
            'change_description': self.change_description,
            'guard_update': self.guard_update,
            'rule_update': self.rule_update,
            'constraint_update': self.constraint_update,
            'effective_timestamp': self.effective_timestamp,
            'required_actions': self.required_actions,
            'fix_hash': self.fix_hash,
            'hash': self.hash
        }


@dataclass
class NodeAcknowledgement:
    """
    Node's acknowledgement of an alert.
    
    Each node must:
    - Receive the alert
    - Confirm receipt
    - Apply the updated invariant
    - Log confirmation
    """
    ack_id: str
    alert_id: str
    node_id: str
    status: AcknowledgementStatus
    received_at: Optional[str]
    applied_at: Optional[str]
    confirmation_hash: Optional[str]  # Hash proving application
    error: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            'ack_id': self.ack_id,
            'alert_id': self.alert_id,
            'node_id': self.node_id,
            'status': self.status.value,
            'received_at': self.received_at,
            'applied_at': self.applied_at,
            'confirmation_hash': self.confirmation_hash,
            'error': self.error
        }


# =============================================================================
# FEEDBACK PROPAGATION SYSTEM
# =============================================================================

class FeedbackPropagationSystem:
    """
    The circulatory system for distributed safety learning.
    
    Implements the canonical loop:
        Gemba → Audit → HALT → Fix → Feedback → Acknowledge → Reset → Resume
    
    One near miss improves the whole system.
    One fix hardens all nodes.
    Learning speed scales with footprint.
    
    Usage:
        fps = FeedbackPropagationSystem(system_id="SOVEREIGN-001")
        fps.register_node("node-0")
        fps.register_node("node-1")
        
        # Observe at gemba
        obs = fps.observe_gemba(
            node_id="node-0",
            observation_type=ObservationType.NEAR_MISS,
            boundary_id="CLAUSE-001",
            description="Near miss on truth constraint",
            evidence={'context': 'detected fabrication attempt'}
        )
        
        # If violation, system halts automatically
        # Apply fix
        fix = fps.apply_fix(
            incident_id=obs.observation_id,
            boundary_id="CLAUSE-001",
            failure_mode="insufficient_validation",
            description="Add pre-output validation",
            guard_update={'validation_required': True}
        )
        
        # Propagate to all nodes
        alert = fps.propagate_fix(fix.fix_id)
        
        # Nodes acknowledge
        fps.acknowledge_alert(alert.alert_id, "node-1")
        
        # Reset and resume
        fps.reset_system()
    """
    
    def __init__(self, system_id: str):
        self.system_id = system_id
        self._state = SystemState.RUN
        self._halt_reason: Optional[str] = None
        
        # Registry
        self._nodes: Set[str] = set()
        self._observations: List[GembaObservation] = []
        self._fixes: Dict[str, Fix] = {}
        self._alerts: Dict[str, AlertUpdate] = {}
        self._acknowledgements: Dict[str, List[NodeAcknowledgement]] = {}
        
        # Counters (reset on system reset)
        self._near_miss_count: int = 0
        self._violation_count: int = 0
        
        # Current invariants (updated by fixes)
        self._guards: Dict[str, Dict] = {}
        self._rules: Dict[str, Dict] = {}
        self._constraints: Dict[str, Dict] = {}
    
    # -------------------------------------------------------------------------
    # Node Management
    # -------------------------------------------------------------------------
    
    def register_node(self, node_id: str) -> Dict:
        """Register a node in the system."""
        self._nodes.add(node_id)
        return {
            'node_id': node_id,
            'registered_at': datetime.now(timezone.utc).isoformat(),
            'total_nodes': len(self._nodes)
        }
    
    def unregister_node(self, node_id: str) -> bool:
        """Remove a node from the system."""
        if node_id in self._nodes:
            self._nodes.remove(node_id)
            return True
        return False
    
    # -------------------------------------------------------------------------
    # 1. Gemba Observation
    # -------------------------------------------------------------------------
    
    def observe_gemba(self,
                      node_id: str,
                      observation_type: ObservationType,
                      description: str,
                      evidence: Dict,
                      boundary_id: Optional[str] = None) -> GembaObservation:
        """
        Capture observation at point of work.
        
        No abstraction. Raw evidence.
        
        If VIOLATION, system halts automatically.
        """
        if node_id not in self._nodes:
            raise ValueError(f"Unknown node: {node_id}")
        
        evidence_hash = hashlib.sha256(
            json.dumps(evidence, sort_keys=True, default=str).encode()
        ).hexdigest()
        
        observation = GembaObservation(
            observation_id=str(uuid.uuid4())[:12],
            observation_type=observation_type,
            timestamp=datetime.now(timezone.utc).isoformat(),
            node_id=node_id,
            boundary_id=boundary_id,
            description=description,
            evidence_hash=evidence_hash,
            raw_data=evidence
        )
        
        self._observations.append(observation)
        
        # Update counters
        if observation_type == ObservationType.NEAR_MISS:
            self._near_miss_count += 1
        elif observation_type == ObservationType.VIOLATION:
            self._violation_count += 1
            # HALT on violation
            self._halt(f"Violation observed: {description}", observation.observation_id)
        
        return observation
    
    # -------------------------------------------------------------------------
    # 2. HALT
    # -------------------------------------------------------------------------
    
    def _halt(self, reason: str, incident_id: str):
        """Halt system execution."""
        self._state = SystemState.HALT
        self._halt_reason = reason
        # In production: auto-instantiate SITREP + 8D template
    
    # -------------------------------------------------------------------------
    # 3. Fix
    # -------------------------------------------------------------------------
    
    def apply_fix(self,
                  incident_id: str,
                  boundary_id: str,
                  failure_mode: str,
                  description: str,
                  applied_by: str,
                  guard_update: Optional[Dict] = None,
                  rule_update: Optional[Dict] = None,
                  constraint_update: Optional[Dict] = None,
                  evidence_hashes: Optional[List[str]] = None) -> Fix:
        """
        Apply a surgical, scoped fix.
        
        Must map explicitly to boundary, failure mode, and evidence.
        No opportunistic changes. No scope creep.
        """
        if self._state != SystemState.HALT:
            raise ValueError("Cannot apply fix when system is not halted")
        
        fix = Fix(
            fix_id=str(uuid.uuid4())[:12],
            incident_id=incident_id,
            boundary_id=boundary_id,
            failure_mode=failure_mode,
            evidence_hashes=evidence_hashes or [],
            description=description,
            guard_update=guard_update,
            rule_update=rule_update,
            constraint_update=constraint_update,
            applied_at=datetime.now(timezone.utc).isoformat(),
            applied_by=applied_by
        )
        
        self._fixes[fix.fix_id] = fix
        
        # Apply locally first
        if guard_update:
            self._guards[boundary_id] = guard_update
        if rule_update:
            self._rules[boundary_id] = rule_update
        if constraint_update:
            self._constraints[boundary_id] = constraint_update
        
        return fix
    
    def verify_fix(self, fix_id: str, verified_by: str) -> Fix:
        """Verify a fix before propagation."""
        if fix_id not in self._fixes:
            raise ValueError(f"Unknown fix: {fix_id}")
        
        fix = self._fixes[fix_id]
        fix.verified = True
        fix.verified_at = datetime.now(timezone.utc).isoformat()
        
        return fix
    
    # -------------------------------------------------------------------------
    # 4. Feedback Propagation
    # -------------------------------------------------------------------------
    
    def propagate_fix(self, fix_id: str) -> AlertUpdate:
        """
        Broadcast fix to all nodes.
        
        This is not optional and not passive.
        """
        if fix_id not in self._fixes:
            raise ValueError(f"Unknown fix: {fix_id}")
        
        fix = self._fixes[fix_id]
        
        if not fix.verified:
            raise ValueError("Fix must be verified before propagation")
        
        self._state = SystemState.PROPAGATING
        
        # Find the original observation
        observation = None
        for obs in self._observations:
            if obs.observation_id == fix.incident_id:
                observation = obs
                break
        
        alert = AlertUpdate(
            alert_id=str(uuid.uuid4())[:12],
            incident_id=fix.incident_id,
            observation_summary=observation.description if observation else "Unknown",
            boundary_id=fix.boundary_id,
            change_description=fix.description,
            guard_update=fix.guard_update,
            rule_update=fix.rule_update,
            constraint_update=fix.constraint_update,
            effective_timestamp=datetime.now(timezone.utc).isoformat(),
            required_actions=self._determine_required_actions(fix),
            fix_hash=fix.hash
        )
        
        self._alerts[alert.alert_id] = alert
        self._acknowledgements[alert.alert_id] = []
        
        # Create pending acknowledgements for all nodes
        for node_id in self._nodes:
            ack = NodeAcknowledgement(
                ack_id=str(uuid.uuid4())[:12],
                alert_id=alert.alert_id,
                node_id=node_id,
                status=AcknowledgementStatus.PENDING,
                received_at=None,
                applied_at=None,
                confirmation_hash=None
            )
            self._acknowledgements[alert.alert_id].append(ack)
        
        return alert
    
    def _determine_required_actions(self, fix: Fix) -> List[str]:
        """Determine required local actions for a fix."""
        actions = []
        
        if fix.guard_update:
            actions.append(f"Update guard for boundary {fix.boundary_id}")
        if fix.rule_update:
            actions.append(f"Update rule for boundary {fix.boundary_id}")
        if fix.constraint_update:
            actions.append(f"Update constraint for boundary {fix.boundary_id}")
        
        actions.append("Log confirmation of update")
        actions.append("Restart with new invariant")
        
        return actions
    
    # -------------------------------------------------------------------------
    # 5. Node Acknowledgement
    # -------------------------------------------------------------------------
    
    def acknowledge_alert(self, 
                          alert_id: str, 
                          node_id: str,
                          applied: bool = True,
                          error: Optional[str] = None) -> NodeAcknowledgement:
        """
        Node acknowledges an alert.
        
        Must:
        - Confirm receipt
        - Apply the updated invariant
        - Log confirmation
        """
        if alert_id not in self._alerts:
            raise ValueError(f"Unknown alert: {alert_id}")
        
        if node_id not in self._nodes:
            raise ValueError(f"Unknown node: {node_id}")
        
        # Find the pending acknowledgement
        ack = None
        for a in self._acknowledgements[alert_id]:
            if a.node_id == node_id:
                ack = a
                break
        
        if not ack:
            raise ValueError(f"No pending acknowledgement for node {node_id}")
        
        timestamp = datetime.now(timezone.utc).isoformat()
        
        if error:
            ack.status = AcknowledgementStatus.FAILED
            ack.error = error
        elif applied:
            ack.status = AcknowledgementStatus.APPLIED
            ack.received_at = timestamp
            ack.applied_at = timestamp
            # Generate confirmation hash
            ack.confirmation_hash = hashlib.sha256(
                f"{alert_id}:{node_id}:{timestamp}:applied".encode()
            ).hexdigest()
        else:
            ack.status = AcknowledgementStatus.RECEIVED
            ack.received_at = timestamp
        
        return ack
    
    def get_acknowledgement_status(self, alert_id: str) -> Dict:
        """Get acknowledgement status for an alert."""
        if alert_id not in self._alerts:
            raise ValueError(f"Unknown alert: {alert_id}")
        
        acks = self._acknowledgements[alert_id]
        
        by_status = {}
        for ack in acks:
            status = ack.status.value
            by_status[status] = by_status.get(status, 0) + 1
        
        all_applied = all(a.status == AcknowledgementStatus.APPLIED for a in acks)
        non_compliant = [a.node_id for a in acks if a.status != AcknowledgementStatus.APPLIED]
        
        return {
            'alert_id': alert_id,
            'total_nodes': len(acks),
            'by_status': by_status,
            'all_applied': all_applied,
            'non_compliant_nodes': non_compliant,
            'ready_for_reset': all_applied
        }
    
    # -------------------------------------------------------------------------
    # 6. System Reset
    # -------------------------------------------------------------------------
    
    def reset_system(self, force: bool = False) -> Dict:
        """
        Reset system and resume under new constraints.
        
        You don't "move on." You restart with a better system.
        
        Args:
            force: Reset even if not all nodes acknowledged
        """
        # Check all alerts are acknowledged
        for alert_id, acks in self._acknowledgements.items():
            non_applied = [a for a in acks if a.status != AcknowledgementStatus.APPLIED]
            if non_applied and not force:
                raise ValueError(
                    f"Cannot reset: {len(non_applied)} nodes have not acknowledged alert {alert_id}"
                )
        
        self._state = SystemState.RESETTING
        
        reset_record = {
            'reset_id': str(uuid.uuid4())[:12],
            'reset_at': datetime.now(timezone.utc).isoformat(),
            'previous_state': 'HALT',
            'near_misses_before_reset': self._near_miss_count,
            'violations_before_reset': self._violation_count,
            'active_guards': len(self._guards),
            'active_rules': len(self._rules),
            'active_constraints': len(self._constraints),
            'forced': force
        }
        
        # Reset counters
        self._near_miss_count = 0
        self._violation_count = 0
        
        # Clear halt
        self._halt_reason = None
        
        # Resume
        self._state = SystemState.RUN
        
        reset_record['new_state'] = 'RUN'
        
        return reset_record
    
    # -------------------------------------------------------------------------
    # Status and Queries
    # -------------------------------------------------------------------------
    
    def get_status(self) -> Dict:
        """Get current system status."""
        return {
            'system_id': self.system_id,
            'state': self._state.value,
            'halt_reason': self._halt_reason,
            'nodes': len(self._nodes),
            'observations': len(self._observations),
            'near_misses': self._near_miss_count,
            'violations': self._violation_count,
            'pending_alerts': len([
                a for a, acks in self._acknowledgements.items()
                if not all(ak.status == AcknowledgementStatus.APPLIED for ak in acks)
            ]),
            'active_guards': len(self._guards),
            'active_rules': len(self._rules),
            'active_constraints': len(self._constraints)
        }
    
    def get_observations(self, 
                         node_id: Optional[str] = None,
                         observation_type: Optional[ObservationType] = None) -> List[Dict]:
        """Get observations with optional filtering."""
        results = []
        for obs in self._observations:
            if node_id and obs.node_id != node_id:
                continue
            if observation_type and obs.observation_type != observation_type:
                continue
            results.append(obs.to_dict())
        return results
    
    def get_current_invariants(self) -> Dict:
        """Get all current guards, rules, and constraints."""
        return {
            'guards': self._guards,
            'rules': self._rules,
            'constraints': self._constraints,
            'total': len(self._guards) + len(self._rules) + len(self._constraints)
        }


# =============================================================================
# SELF-TEST
# =============================================================================

def self_test():
    """
    Self-test of Feedback Propagation System.
    
    Tests the complete canonical loop:
    Gemba → Audit → HALT → Fix → Feedback → Acknowledge → Reset → Resume
    """
    print("=" * 60)
    print("JARUS Feedback Propagation System - Self Test")
    print("=" * 60)
    
    # Initialize
    print("\n[1] Initialize system and register nodes...")
    fps = FeedbackPropagationSystem(system_id="SOVEREIGN-001")
    fps.register_node("node-0")
    fps.register_node("node-1")
    fps.register_node("node-2")
    
    status = fps.get_status()
    print(f"    System: {status['system_id']}")
    print(f"    State: {status['state']}")
    print(f"    Nodes: {status['nodes']}")
    assert status['state'] == 'RUN'
    print("    ✓ PASS")
    
    # Gemba observation - near miss
    print("\n[2] Observe near miss at gemba...")
    obs1 = fps.observe_gemba(
        node_id="node-0",
        observation_type=ObservationType.NEAR_MISS,
        boundary_id="CLAUSE-001",
        description="Detected potential fabrication in draft output",
        evidence={'output_draft': 'contained unverified claim', 'caught_by': 'pre-validation'}
    )
    print(f"    Observation: {obs1.observation_id}")
    print(f"    Type: {obs1.observation_type.value}")
    
    status = fps.get_status()
    print(f"    Near misses: {status['near_misses']}")
    print(f"    State: {status['state']} (still running)")
    assert status['state'] == 'RUN'  # Near miss doesn't halt
    print("    ✓ PASS")
    
    # Gemba observation - violation (triggers halt)
    print("\n[3] Observe violation at gemba (triggers HALT)...")
    obs2 = fps.observe_gemba(
        node_id="node-1",
        observation_type=ObservationType.VIOLATION,
        boundary_id="CLAUSE-001",
        description="Fabricated data in output",
        evidence={'output': 'contained fabricated statistic', 'severity': 'high'}
    )
    print(f"    Observation: {obs2.observation_id}")
    
    status = fps.get_status()
    print(f"    State: {status['state']}")
    print(f"    Halt reason: {status['halt_reason'][:50]}...")
    assert status['state'] == 'HALT'
    print("    ✓ PASS")
    
    # Apply fix
    print("\n[4] Apply surgical fix...")
    fix = fps.apply_fix(
        incident_id=obs2.observation_id,
        boundary_id="CLAUSE-001",
        failure_mode="insufficient_pre_output_validation",
        description="Add mandatory fact-check step before output",
        applied_by="operator",
        guard_update={
            'fact_check_required': True,
            'validation_steps': ['source_verification', 'claim_validation']
        },
        evidence_hashes=[obs2.evidence_hash]
    )
    print(f"    Fix ID: {fix.fix_id}")
    print(f"    Boundary: {fix.boundary_id}")
    print(f"    Failure mode: {fix.failure_mode}")
    print("    ✓ PASS")
    
    # Verify fix
    print("\n[5] Verify fix before propagation...")
    fix = fps.verify_fix(fix.fix_id, verified_by="supervisor")
    print(f"    Verified: {fix.verified}")
    print(f"    Verified at: {fix.verified_at}")
    assert fix.verified
    print("    ✓ PASS")
    
    # Propagate
    print("\n[6] Propagate fix to all nodes...")
    alert = fps.propagate_fix(fix.fix_id)
    print(f"    Alert ID: {alert.alert_id}")
    print(f"    Required actions: {len(alert.required_actions)}")
    for action in alert.required_actions:
        print(f"      - {action}")
    
    status = fps.get_status()
    print(f"    State: {status['state']}")
    assert status['state'] == 'PROPAGATING'
    print("    ✓ PASS")
    
    # Check acknowledgement status
    print("\n[7] Check acknowledgement status (before acks)...")
    ack_status = fps.get_acknowledgement_status(alert.alert_id)
    print(f"    Total nodes: {ack_status['total_nodes']}")
    print(f"    By status: {ack_status['by_status']}")
    print(f"    Non-compliant: {ack_status['non_compliant_nodes']}")
    assert not ack_status['ready_for_reset']
    print("    ✓ PASS")
    
    # Nodes acknowledge
    print("\n[8] Nodes acknowledge alert...")
    for node_id in ["node-0", "node-1", "node-2"]:
        ack = fps.acknowledge_alert(alert.alert_id, node_id, applied=True)
        print(f"    {node_id}: {ack.status.value}")
    
    ack_status = fps.get_acknowledgement_status(alert.alert_id)
    print(f"    All applied: {ack_status['all_applied']}")
    print(f"    Ready for reset: {ack_status['ready_for_reset']}")
    assert ack_status['ready_for_reset']
    print("    ✓ PASS")
    
    # Reset system
    print("\n[9] Reset system and resume...")
    reset = fps.reset_system()
    print(f"    Reset ID: {reset['reset_id']}")
    print(f"    Near misses cleared: {reset['near_misses_before_reset']}")
    print(f"    Violations cleared: {reset['violations_before_reset']}")
    print(f"    New state: {reset['new_state']}")
    
    status = fps.get_status()
    assert status['state'] == 'RUN'
    assert status['near_misses'] == 0
    print("    ✓ PASS")
    
    # Verify invariants persisted
    print("\n[10] Verify invariants persisted after reset...")
    invariants = fps.get_current_invariants()
    print(f"    Active guards: {len(invariants['guards'])}")
    print(f"    Guard for CLAUSE-001: {invariants['guards'].get('CLAUSE-001', {})}")
    assert 'CLAUSE-001' in invariants['guards']
    print("    ✓ PASS")
    
    # Summary
    print("\n" + "=" * 60)
    print("SELF-TEST COMPLETE")
    print("=" * 60)
    print("Canonical loop tested:")
    print("  Gemba → Audit → HALT → Fix → Feedback → Acknowledge → Reset")
    print("All tests passed ✓")
    
    return True


if __name__ == "__main__":
    self_test()
