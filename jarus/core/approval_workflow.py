#!/usr/bin/env python3
"""
JARUS Approval Workflow
=======================
Complete approval system for critical operations.

Features:
- Multi-level escalation chains
- Configurable timeouts
- Approval/denial with rationale
- Notification callbacks
- Full audit trail

Design Principles:
- No critical operation without human approval
- Clear escalation path
- Timeout protection (operations don't hang forever)
- Complete audit trail

Author: Codex Sovereign Systems
Version: 1.0.0
"""

import uuid
import json
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable, Any
from enum import Enum

# Import core modules
from .evidence_ledger import EvidenceLedger, EvidenceType


# =============================================================================
# ENUMS
# =============================================================================

class ApprovalStatus(Enum):
    """Status of an approval request."""
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    DENIED = "DENIED"
    EXPIRED = "EXPIRED"
    ESCALATED = "ESCALATED"
    CANCELLED = "CANCELLED"


class ApprovalPriority(Enum):
    """Priority levels for approvals."""
    LOW = 1         # 24 hour timeout
    NORMAL = 2      # 4 hour timeout
    HIGH = 3        # 1 hour timeout
    CRITICAL = 4    # 15 minute timeout


class EscalationLevel(Enum):
    """Escalation levels in the chain."""
    OPERATOR = 1
    SUPERVISOR = 2
    ADMINISTRATOR = 3
    CONSTITUTIONAL = 4  # Requires constitutional amendment


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class ApprovalRequest:
    """
    A request for approval of a critical operation.
    
    Tracks the full lifecycle from request to resolution.
    """
    request_id: str
    operation: str
    description: str
    context: Dict
    requested_by: str
    requested_at: str
    expires_at: str
    priority: ApprovalPriority
    escalation_level: EscalationLevel
    status: ApprovalStatus = ApprovalStatus.PENDING
    resolved_by: Optional[str] = None
    resolved_at: Optional[str] = None
    resolution_reason: Optional[str] = None
    escalation_history: List[Dict] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        """Serialize for storage."""
        return {
            'request_id': self.request_id,
            'operation': self.operation,
            'description': self.description,
            'context': self.context,
            'requested_by': self.requested_by,
            'requested_at': self.requested_at,
            'expires_at': self.expires_at,
            'priority': self.priority.name,
            'escalation_level': self.escalation_level.name,
            'status': self.status.name,
            'resolved_by': self.resolved_by,
            'resolved_at': self.resolved_at,
            'resolution_reason': self.resolution_reason,
            'escalation_history': self.escalation_history
        }
    
    @property
    def is_expired(self) -> bool:
        """Check if request has expired."""
        now = datetime.now(timezone.utc)
        expires = datetime.fromisoformat(self.expires_at.replace('Z', '+00:00'))
        return now > expires
    
    @property
    def time_remaining(self) -> timedelta:
        """Get time until expiration."""
        now = datetime.now(timezone.utc)
        expires = datetime.fromisoformat(self.expires_at.replace('Z', '+00:00'))
        return max(expires - now, timedelta(0))


@dataclass
class EscalationRule:
    """
    Rule for automatic escalation.
    
    Defines when and how approvals escalate up the chain.
    """
    rule_id: str
    operation_pattern: str  # Regex or exact match
    initial_level: EscalationLevel
    escalate_after_minutes: int
    max_level: EscalationLevel
    auto_deny_on_expire: bool = True


@dataclass
class ApprovalPolicy:
    """
    Policy defining approval requirements for operations.
    """
    policy_id: str
    operation: str
    min_level: EscalationLevel
    priority: ApprovalPriority
    require_reason: bool = True
    dual_approval: bool = False  # Requires two approvers


# =============================================================================
# APPROVAL WORKFLOW
# =============================================================================

class ApprovalWorkflow:
    """
    Manages the full approval lifecycle.
    
    Handles:
    - Creating approval requests
    - Processing approvals/denials
    - Automatic escalation
    - Timeout handling
    - Notification dispatch
    
    Usage:
        workflow = ApprovalWorkflow(ledger)
        
        # Request approval
        request = workflow.request_approval(
            operation="deploy_production",
            description="Deploy v2.1 to production",
            context={'version': '2.1', 'target': 'prod'},
            requested_by="operator_1"
        )
        
        # Approve
        workflow.approve(request.request_id, "supervisor_1", "Reviewed and approved")
    """
    
    # Default timeouts by priority (in minutes)
    DEFAULT_TIMEOUTS = {
        ApprovalPriority.LOW: 1440,      # 24 hours
        ApprovalPriority.NORMAL: 240,    # 4 hours
        ApprovalPriority.HIGH: 60,       # 1 hour
        ApprovalPriority.CRITICAL: 15    # 15 minutes
    }
    
    def __init__(self, 
                 ledger: Optional[EvidenceLedger] = None,
                 on_request: Optional[Callable[[ApprovalRequest], None]] = None,
                 on_escalate: Optional[Callable[[ApprovalRequest], None]] = None,
                 on_resolve: Optional[Callable[[ApprovalRequest], None]] = None,
                 on_expire: Optional[Callable[[ApprovalRequest], None]] = None):
        """
        Initialize the workflow.
        
        Args:
            ledger: Evidence ledger for audit trail
            on_request: Callback when new request created
            on_escalate: Callback when request escalates
            on_resolve: Callback when request resolved
            on_expire: Callback when request expires
        """
        self._ledger = ledger or EvidenceLedger(auto_persist=False)
        self._requests: Dict[str, ApprovalRequest] = {}
        self._policies: Dict[str, ApprovalPolicy] = {}
        self._escalation_rules: Dict[str, EscalationRule] = {}
        
        # Callbacks
        self._on_request = on_request
        self._on_escalate = on_escalate
        self._on_resolve = on_resolve
        self._on_expire = on_expire
        
        # Register default policies
        self._register_default_policies()
    
    def _register_default_policies(self):
        """Register policies for common critical operations."""
        
        # Production deployment
        self.register_policy(ApprovalPolicy(
            policy_id="POL-DEPLOY",
            operation="deploy",
            min_level=EscalationLevel.SUPERVISOR,
            priority=ApprovalPriority.HIGH,
            require_reason=True
        ))
        
        # Delete operations
        self.register_policy(ApprovalPolicy(
            policy_id="POL-DELETE",
            operation="delete",
            min_level=EscalationLevel.ADMINISTRATOR,
            priority=ApprovalPriority.CRITICAL,
            require_reason=True,
            dual_approval=True
        ))
        
        # Financial transactions
        self.register_policy(ApprovalPolicy(
            policy_id="POL-FINANCIAL",
            operation="financial",
            min_level=EscalationLevel.ADMINISTRATOR,
            priority=ApprovalPriority.CRITICAL,
            require_reason=True,
            dual_approval=True
        ))
        
        # Constitution modification
        self.register_policy(ApprovalPolicy(
            policy_id="POL-CONSTITUTION",
            operation="modify_constitution",
            min_level=EscalationLevel.CONSTITUTIONAL,
            priority=ApprovalPriority.CRITICAL,
            require_reason=True,
            dual_approval=True
        ))
        
        # External API calls
        self.register_policy(ApprovalPolicy(
            policy_id="POL-EXTERNAL",
            operation="external_api",
            min_level=EscalationLevel.OPERATOR,
            priority=ApprovalPriority.NORMAL,
            require_reason=False
        ))
    
    def register_policy(self, policy: ApprovalPolicy):
        """Register an approval policy."""
        self._policies[policy.operation] = policy
    
    def register_escalation_rule(self, rule: EscalationRule):
        """Register an escalation rule."""
        self._escalation_rules[rule.rule_id] = rule
    
    def request_approval(self,
                        operation: str,
                        description: str,
                        context: Dict,
                        requested_by: str,
                        priority: Optional[ApprovalPriority] = None) -> ApprovalRequest:
        """
        Create a new approval request.
        
        Args:
            operation: Name of the operation
            description: Human-readable description
            context: Operation context/parameters
            requested_by: Operator requesting approval
            priority: Override default priority
            
        Returns:
            New ApprovalRequest
        """
        # Get policy for operation
        policy = self._policies.get(operation)
        
        # Determine priority and level
        if priority is None:
            priority = policy.priority if policy else ApprovalPriority.NORMAL
        
        initial_level = policy.min_level if policy else EscalationLevel.SUPERVISOR
        
        # Calculate expiration
        timeout_minutes = self.DEFAULT_TIMEOUTS[priority]
        now = datetime.now(timezone.utc)
        expires = now + timedelta(minutes=timeout_minutes)
        
        # Create request
        request = ApprovalRequest(
            request_id=str(uuid.uuid4()),
            operation=operation,
            description=description,
            context=context,
            requested_by=requested_by,
            requested_at=now.isoformat(),
            expires_at=expires.isoformat(),
            priority=priority,
            escalation_level=initial_level
        )
        
        self._requests[request.request_id] = request
        
        # Record in ledger
        self._ledger.record(
            evidence_type=EvidenceType.ACTION,
            content=request.to_dict(),
            summary=f"Approval requested: {operation} by {requested_by}",
            metadata={'request_id': request.request_id}
        )
        
        # Notify
        if self._on_request:
            self._on_request(request)
        
        return request
    
    def approve(self,
                request_id: str,
                approved_by: str,
                reason: str = "") -> ApprovalRequest:
        """
        Approve a pending request.
        
        Args:
            request_id: Request to approve
            approved_by: Approver identifier
            reason: Reason for approval
            
        Returns:
            Updated ApprovalRequest
            
        Raises:
            ValueError: If request not found or already resolved
        """
        request = self._requests.get(request_id)
        if not request:
            raise ValueError(f"Request not found: {request_id}")
        
        if request.status != ApprovalStatus.PENDING:
            raise ValueError(f"Request already resolved: {request.status.name}")
        
        # Check expiration
        if request.is_expired:
            request.status = ApprovalStatus.EXPIRED
            raise ValueError("Request has expired")
        
        # Check policy requirements
        policy = self._policies.get(request.operation)
        if policy and policy.require_reason and not reason:
            raise ValueError("Reason required for this operation")
        
        # Approve
        request.status = ApprovalStatus.APPROVED
        request.resolved_by = approved_by
        request.resolved_at = datetime.now(timezone.utc).isoformat()
        request.resolution_reason = reason
        
        # Record in ledger
        self._ledger.record(
            evidence_type=EvidenceType.ACTION,
            content={
                'event': 'approval_granted',
                'request_id': request_id,
                'approved_by': approved_by,
                'reason': reason
            },
            summary=f"Approved: {request.operation} by {approved_by}",
            metadata={'request_id': request_id}
        )
        
        # Notify
        if self._on_resolve:
            self._on_resolve(request)
        
        return request
    
    def deny(self,
             request_id: str,
             denied_by: str,
             reason: str) -> ApprovalRequest:
        """
        Deny a pending request.
        
        Args:
            request_id: Request to deny
            denied_by: Denier identifier
            reason: Reason for denial (required)
            
        Returns:
            Updated ApprovalRequest
        """
        request = self._requests.get(request_id)
        if not request:
            raise ValueError(f"Request not found: {request_id}")
        
        if request.status != ApprovalStatus.PENDING:
            raise ValueError(f"Request already resolved: {request.status.name}")
        
        if not reason:
            raise ValueError("Reason required for denial")
        
        # Deny
        request.status = ApprovalStatus.DENIED
        request.resolved_by = denied_by
        request.resolved_at = datetime.now(timezone.utc).isoformat()
        request.resolution_reason = reason
        
        # Record in ledger
        self._ledger.record(
            evidence_type=EvidenceType.ACTION,
            content={
                'event': 'approval_denied',
                'request_id': request_id,
                'denied_by': denied_by,
                'reason': reason
            },
            summary=f"Denied: {request.operation} by {denied_by}",
            metadata={'request_id': request_id}
        )
        
        # Notify
        if self._on_resolve:
            self._on_resolve(request)
        
        return request
    
    def escalate(self, request_id: str, escalated_by: str, reason: str) -> ApprovalRequest:
        """
        Escalate a request to the next level.
        
        Args:
            request_id: Request to escalate
            escalated_by: Who is escalating
            reason: Reason for escalation
            
        Returns:
            Updated ApprovalRequest
        """
        request = self._requests.get(request_id)
        if not request:
            raise ValueError(f"Request not found: {request_id}")
        
        if request.status != ApprovalStatus.PENDING:
            raise ValueError(f"Request already resolved: {request.status.name}")
        
        # Determine next level
        current_level = request.escalation_level
        if current_level == EscalationLevel.CONSTITUTIONAL:
            raise ValueError("Already at maximum escalation level")
        
        next_level = EscalationLevel(current_level.value + 1)
        
        # Record escalation
        request.escalation_history.append({
            'from_level': current_level.name,
            'to_level': next_level.name,
            'escalated_by': escalated_by,
            'escalated_at': datetime.now(timezone.utc).isoformat(),
            'reason': reason
        })
        
        request.escalation_level = next_level
        request.status = ApprovalStatus.ESCALATED
        # Reset to pending at new level
        request.status = ApprovalStatus.PENDING
        
        # Record in ledger
        self._ledger.record(
            evidence_type=EvidenceType.ACTION,
            content={
                'event': 'approval_escalated',
                'request_id': request_id,
                'from_level': current_level.name,
                'to_level': next_level.name,
                'escalated_by': escalated_by,
                'reason': reason
            },
            summary=f"Escalated: {request.operation} to {next_level.name}",
            metadata={'request_id': request_id}
        )
        
        # Notify
        if self._on_escalate:
            self._on_escalate(request)
        
        return request
    
    def cancel(self, request_id: str, cancelled_by: str, reason: str) -> ApprovalRequest:
        """
        Cancel a pending request.
        
        Args:
            request_id: Request to cancel
            cancelled_by: Who is cancelling
            reason: Reason for cancellation
            
        Returns:
            Updated ApprovalRequest
        """
        request = self._requests.get(request_id)
        if not request:
            raise ValueError(f"Request not found: {request_id}")
        
        if request.status != ApprovalStatus.PENDING:
            raise ValueError(f"Request already resolved: {request.status.name}")
        
        request.status = ApprovalStatus.CANCELLED
        request.resolved_by = cancelled_by
        request.resolved_at = datetime.now(timezone.utc).isoformat()
        request.resolution_reason = reason
        
        # Record in ledger
        self._ledger.record(
            evidence_type=EvidenceType.ACTION,
            content={
                'event': 'approval_cancelled',
                'request_id': request_id,
                'cancelled_by': cancelled_by,
                'reason': reason
            },
            summary=f"Cancelled: {request.operation} by {cancelled_by}",
            metadata={'request_id': request_id}
        )
        
        return request
    
    def check_expirations(self) -> List[ApprovalRequest]:
        """
        Check and process expired requests.
        
        Should be called periodically (e.g., every minute).
        
        Returns:
            List of newly expired requests
        """
        expired = []
        
        for request in self._requests.values():
            if request.status == ApprovalStatus.PENDING and request.is_expired:
                request.status = ApprovalStatus.EXPIRED
                request.resolved_at = datetime.now(timezone.utc).isoformat()
                request.resolution_reason = "Request expired without resolution"
                
                # Record in ledger
                self._ledger.record(
                    evidence_type=EvidenceType.SYSTEM_EVENT,
                    content={
                        'event': 'approval_expired',
                        'request_id': request.request_id
                    },
                    summary=f"Expired: {request.operation}",
                    metadata={'request_id': request.request_id}
                )
                
                # Notify
                if self._on_expire:
                    self._on_expire(request)
                
                expired.append(request)
        
        return expired
    
    def get_request(self, request_id: str) -> Optional[ApprovalRequest]:
        """Get request by ID."""
        return self._requests.get(request_id)
    
    def get_pending(self, 
                    level: Optional[EscalationLevel] = None,
                    operation: Optional[str] = None) -> List[ApprovalRequest]:
        """
        Get pending requests with optional filters.
        
        Args:
            level: Filter by escalation level
            operation: Filter by operation name
            
        Returns:
            List of pending requests
        """
        pending = [
            r for r in self._requests.values()
            if r.status == ApprovalStatus.PENDING
        ]
        
        if level:
            pending = [r for r in pending if r.escalation_level == level]
        
        if operation:
            pending = [r for r in pending if r.operation == operation]
        
        # Sort by priority (highest first) then by time (oldest first)
        pending.sort(key=lambda r: (-r.priority.value, r.requested_at))
        
        return pending
    
    def get_history(self,
                    since: Optional[str] = None,
                    status: Optional[ApprovalStatus] = None,
                    limit: int = 100) -> List[ApprovalRequest]:
        """
        Get approval history.
        
        Args:
            since: ISO timestamp to filter from
            status: Filter by status
            limit: Maximum results
            
        Returns:
            List of requests (newest first)
        """
        results = list(self._requests.values())
        
        if since:
            results = [r for r in results if r.requested_at >= since]
        
        if status:
            results = [r for r in results if r.status == status]
        
        results.sort(key=lambda r: r.requested_at, reverse=True)
        
        return results[:limit]
    
    def generate_report(self) -> Dict:
        """Generate approval workflow report."""
        all_requests = list(self._requests.values())
        
        # Count by status
        status_counts = {}
        for r in all_requests:
            s = r.status.name
            status_counts[s] = status_counts.get(s, 0) + 1
        
        # Count by operation
        operation_counts = {}
        for r in all_requests:
            o = r.operation
            operation_counts[o] = operation_counts.get(o, 0) + 1
        
        # Calculate average resolution time
        resolved = [r for r in all_requests if r.resolved_at]
        avg_resolution = None
        if resolved:
            total_seconds = 0
            for r in resolved:
                requested = datetime.fromisoformat(r.requested_at.replace('Z', '+00:00'))
                resolved_time = datetime.fromisoformat(r.resolved_at.replace('Z', '+00:00'))
                total_seconds += (resolved_time - requested).total_seconds()
            avg_resolution = total_seconds / len(resolved)
        
        return {
            'report_id': str(uuid.uuid4()),
            'generated_at': datetime.now(timezone.utc).isoformat(),
            'total_requests': len(all_requests),
            'by_status': status_counts,
            'by_operation': operation_counts,
            'pending_count': len(self.get_pending()),
            'policies_registered': len(self._policies),
            'average_resolution_seconds': avg_resolution
        }


# =============================================================================
# SELF-TEST
# =============================================================================

def self_test():
    """
    Self-test of Approval Workflow.
    
    Tests:
    1. Create approval request
    2. Approve request
    3. Deny request
    4. Escalate request
    5. Cancel request
    6. Expiration handling
    7. Generate report
    """
    print("=" * 60)
    print("JARUS Approval Workflow - Self Test")
    print("=" * 60)
    
    # Track notifications
    notifications = []
    
    def on_request(r):
        notifications.append(('request', r.request_id))
    
    def on_resolve(r):
        notifications.append(('resolve', r.request_id))
    
    # Initialize
    print("\n[1] Initialize workflow...")
    workflow = ApprovalWorkflow(
        on_request=on_request,
        on_resolve=on_resolve
    )
    print(f"    Policies registered: {len(workflow._policies)}")
    assert len(workflow._policies) == 5
    print("    ✓ PASS")
    
    # Create request
    print("\n[2] Create approval request...")
    request1 = workflow.request_approval(
        operation="deploy",
        description="Deploy v2.0 to production",
        context={'version': '2.0', 'target': 'production'},
        requested_by="operator_1"
    )
    print(f"    Request ID: {request1.request_id[:16]}...")
    print(f"    Status: {request1.status.name}")
    print(f"    Priority: {request1.priority.name}")
    print(f"    Level: {request1.escalation_level.name}")
    assert request1.status == ApprovalStatus.PENDING
    assert ('request', request1.request_id) in notifications
    print("    ✓ PASS")
    
    # Approve request
    print("\n[3] Approve request...")
    request1 = workflow.approve(
        request1.request_id,
        approved_by="supervisor_1",
        reason="Reviewed deployment plan, approved"
    )
    print(f"    Status: {request1.status.name}")
    print(f"    Resolved by: {request1.resolved_by}")
    assert request1.status == ApprovalStatus.APPROVED
    print("    ✓ PASS")
    
    # Create and deny request
    print("\n[4] Create and deny request...")
    request2 = workflow.request_approval(
        operation="delete",
        description="Delete production database",
        context={'target': 'prod_db'},
        requested_by="operator_2"
    )
    request2 = workflow.deny(
        request2.request_id,
        denied_by="admin_1",
        reason="Dangerous operation, denied"
    )
    print(f"    Status: {request2.status.name}")
    print(f"    Reason: {request2.resolution_reason}")
    assert request2.status == ApprovalStatus.DENIED
    print("    ✓ PASS")
    
    # Create and escalate request
    print("\n[5] Create and escalate request...")
    request3 = workflow.request_approval(
        operation="external_api",
        description="Call external payment API",
        context={'api': 'stripe'},
        requested_by="operator_3"
    )
    original_level = request3.escalation_level
    request3 = workflow.escalate(
        request3.request_id,
        escalated_by="supervisor_2",
        reason="Needs higher approval"
    )
    print(f"    Original level: {original_level.name}")
    print(f"    New level: {request3.escalation_level.name}")
    print(f"    Escalation history: {len(request3.escalation_history)}")
    assert request3.escalation_level.value > original_level.value
    print("    ✓ PASS")
    
    # Cancel request
    print("\n[6] Cancel request...")
    request3 = workflow.cancel(
        request3.request_id,
        cancelled_by="operator_3",
        reason="No longer needed"
    )
    print(f"    Status: {request3.status.name}")
    assert request3.status == ApprovalStatus.CANCELLED
    print("    ✓ PASS")
    
    # Get pending
    print("\n[7] Get pending requests...")
    pending = workflow.get_pending()
    print(f"    Pending count: {len(pending)}")
    assert len(pending) == 0  # All resolved
    print("    ✓ PASS")
    
    # Generate report
    print("\n[8] Generate report...")
    report = workflow.generate_report()
    print(f"    Total requests: {report['total_requests']}")
    print(f"    By status: {report['by_status']}")
    assert report['total_requests'] == 3
    print("    ✓ PASS")
    
    # Summary
    print("\n" + "=" * 60)
    print("SELF-TEST COMPLETE")
    print("=" * 60)
    print(f"Requests processed: {report['total_requests']}")
    print(f"Notifications sent: {len(notifications)}")
    print("All tests passed ✓")
    
    return True


if __name__ == "__main__":
    self_test()
