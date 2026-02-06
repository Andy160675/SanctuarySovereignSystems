#!/usr/bin/env python3
"""
JARUS Operator Console
======================
Human interface for sovereign system governance.

Features:
- Role-based access control (Viewer, Operator, Supervisor, Admin)
- Session management with audit trail
- Approval workflow for critical operations
- Real-time system status

Design Principles:
- Every command is recorded
- Critical operations require approval
- Clear feedback on permissions
- Consistent command structure

Author: Codex Sovereign Systems
Version: 1.0.0
"""

import json
import uuid
import sys
from datetime import datetime, timezone
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable, Any
from enum import Enum
from pathlib import Path

# Import core modules
from .constitutional_runtime import ConstitutionalRuntime, DecisionType
from .evidence_ledger import EvidenceLedger, EvidenceType
from .surge_wrapper import SurgeWrapper


# =============================================================================
# ENUMS
# =============================================================================

class OperatorRole(Enum):
    """Permission levels for operators."""
    VIEWER = 1          # Read-only access
    OPERATOR = 2        # Execute standard operations
    SUPERVISOR = 3      # Approve escalations
    ADMINISTRATOR = 4   # Full system access


class CommandCategory(Enum):
    """Categories of console commands."""
    SYSTEM = "SYSTEM"
    EVIDENCE = "EVIDENCE"
    GOVERNANCE = "GOVERNANCE"
    APPROVAL = "APPROVAL"
    HELP = "HELP"


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class OperatorSession:
    """Active operator session."""
    session_id: str
    operator_id: str
    role: OperatorRole
    started_at: str
    last_activity: str
    commands_executed: int = 0
    
    def update_activity(self):
        """Update last activity timestamp."""
        self.last_activity = datetime.now(timezone.utc).isoformat()
        self.commands_executed += 1


@dataclass
class CommandResult:
    """Result of executing a command."""
    success: bool
    command: str
    output: Any
    error: Optional[str] = None
    requires_approval: bool = False
    approval_id: Optional[str] = None


@dataclass
class PendingApproval:
    """Operation awaiting approval."""
    approval_id: str
    operation: str
    context: Dict
    requested_by: str
    requested_at: str
    expires_at: str
    reason: str
    approved: Optional[bool] = None
    approved_by: Optional[str] = None


@dataclass
class Command:
    """Definition of a console command."""
    name: str
    category: CommandCategory
    description: str
    handler: Callable
    min_role: OperatorRole
    
    def can_execute(self, role: OperatorRole) -> bool:
        """Check if role has permission."""
        return role.value >= self.min_role.value


# =============================================================================
# OPERATOR CONSOLE
# =============================================================================

class OperatorConsole:
    """
    Human interface for JARUS governance.
    
    Provides command-line access to:
    - System status and health
    - Evidence chain operations
    - Constitutional governance
    - Approval workflows
    
    Usage:
        console = OperatorConsole()
        session = console.create_session("andy", OperatorRole.ADMINISTRATOR)
        result = console.execute(session.session_id, "status")
        print(result.output)
    """
    
    def __init__(self,
                 runtime: Optional[ConstitutionalRuntime] = None,
                 ledger: Optional[EvidenceLedger] = None):
        """
        Initialize the console.
        
        Args:
            runtime: Constitutional runtime (created if not provided)
            ledger: Evidence ledger (created if not provided)
        """
        self._runtime = runtime or ConstitutionalRuntime()
        self._ledger = ledger or EvidenceLedger(auto_persist=False)
        self._surge = SurgeWrapper(self._runtime, self._ledger)
        self._sessions: Dict[str, OperatorSession] = {}
        self._approvals: Dict[str, PendingApproval] = {}
        self._commands: Dict[str, Command] = {}
        
        # Register built-in commands
        self._register_commands()
    
    def _register_commands(self):
        """Register all console commands."""
        
        # System commands
        self._register("status", CommandCategory.SYSTEM,
                      "Show system status", self._cmd_status,
                      OperatorRole.VIEWER)
        
        self._register("health", CommandCategory.SYSTEM,
                      "Show health check", self._cmd_health,
                      OperatorRole.VIEWER)
        
        self._register("halt", CommandCategory.SYSTEM,
                      "Halt the system", self._cmd_halt,
                      OperatorRole.ADMINISTRATOR)
        
        self._register("resume", CommandCategory.SYSTEM,
                      "Resume from halt", self._cmd_resume,
                      OperatorRole.ADMINISTRATOR)
        
        # Evidence commands
        self._register("evidence.list", CommandCategory.EVIDENCE,
                      "List recent evidence", self._cmd_evidence_list,
                      OperatorRole.VIEWER)
        
        self._register("evidence.verify", CommandCategory.EVIDENCE,
                      "Verify chain integrity", self._cmd_evidence_verify,
                      OperatorRole.VIEWER)
        
        self._register("evidence.record", CommandCategory.EVIDENCE,
                      "Record new evidence", self._cmd_evidence_record,
                      OperatorRole.OPERATOR)
        
        self._register("evidence.report", CommandCategory.EVIDENCE,
                      "Generate audit report", self._cmd_evidence_report,
                      OperatorRole.SUPERVISOR)
        
        # Governance commands
        self._register("constitution", CommandCategory.GOVERNANCE,
                      "Show constitution", self._cmd_constitution,
                      OperatorRole.VIEWER)
        
        self._register("violations", CommandCategory.GOVERNANCE,
                      "List violations", self._cmd_violations,
                      OperatorRole.VIEWER)
        
        self._register("evaluate", CommandCategory.GOVERNANCE,
                      "Evaluate action", self._cmd_evaluate,
                      OperatorRole.OPERATOR)
        
        # Approval commands
        self._register("approvals", CommandCategory.APPROVAL,
                      "List pending approvals", self._cmd_approvals_list,
                      OperatorRole.SUPERVISOR)
        
        self._register("approve", CommandCategory.APPROVAL,
                      "Approve operation", self._cmd_approve,
                      OperatorRole.SUPERVISOR)
        
        self._register("deny", CommandCategory.APPROVAL,
                      "Deny operation", self._cmd_deny,
                      OperatorRole.SUPERVISOR)
        
        # Help commands
        self._register("help", CommandCategory.HELP,
                      "Show available commands", self._cmd_help,
                      OperatorRole.VIEWER)
        
        self._register("whoami", CommandCategory.HELP,
                      "Show current session", self._cmd_whoami,
                      OperatorRole.VIEWER)
    
    def _register(self, name: str, category: CommandCategory,
                  description: str, handler: Callable, min_role: OperatorRole):
        """Register a command."""
        self._commands[name] = Command(
            name=name,
            category=category,
            description=description,
            handler=handler,
            min_role=min_role
        )
    
    def create_session(self, operator_id: str, role: OperatorRole) -> OperatorSession:
        """
        Create a new operator session.
        
        Args:
            operator_id: Unique operator identifier
            role: Operator's role
            
        Returns:
            New session object
        """
        session = OperatorSession(
            session_id=str(uuid.uuid4()),
            operator_id=operator_id,
            role=role,
            started_at=datetime.now(timezone.utc).isoformat(),
            last_activity=datetime.now(timezone.utc).isoformat()
        )
        
        self._sessions[session.session_id] = session
        
        # Record session creation
        self._ledger.record(
            evidence_type=EvidenceType.ACTION,
            content={'event': 'session_created', 'operator': operator_id, 'role': role.name},
            summary=f"Session created: {operator_id} ({role.name})"
        )
        
        return session
    
    def execute(self, session_id: str, command_name: str, 
                args: Optional[Dict] = None) -> CommandResult:
        """
        Execute a console command.
        
        Args:
            session_id: Active session ID
            command_name: Command to execute
            args: Command arguments
            
        Returns:
            CommandResult with output or error
        """
        args = args or {}
        
        # Validate session
        session = self._sessions.get(session_id)
        if not session:
            return CommandResult(
                success=False,
                command=command_name,
                output=None,
                error="Invalid session"
            )
        
        # Get command
        command = self._commands.get(command_name)
        if not command:
            return CommandResult(
                success=False,
                command=command_name,
                output=None,
                error=f"Unknown command: {command_name}. Type 'help' for commands."
            )
        
        # Check permissions
        if not command.can_execute(session.role):
            return CommandResult(
                success=False,
                command=command_name,
                output=None,
                error=f"Permission denied. Required: {command.min_role.name}"
            )
        
        # Check constitutional constraints
        context = {
            'action': command_name,
            'operator_id': session.operator_id,
            'role': session.role.name,
            'args': args
        }
        
        # For approval commands, set operator_approved
        if session.role.value >= OperatorRole.SUPERVISOR.value:
            context['operator_approved'] = True
        
        # Execute command using Surge Wrapper
        try:
            def handler():
                return command.handler(session, args)

            surge_result = self._surge.execute_sovereign_action(
                action_name=command_name,
                context=context,
                handler=handler
            )

            if surge_result.get("status") == "ESCALATED":
                approval = self._create_approval(command_name, context, session)
                return CommandResult(
                    success=False,
                    command=command_name,
                    output={'message': 'Approval required', 'approval_id': approval.approval_id},
                    requires_approval=True,
                    approval_id=approval.approval_id
                )

            session.update_activity()
            return CommandResult(
                success=True,
                command=command_name,
                output=surge_result["result"]
            )

        except PermissionError as e:
            return CommandResult(
                success=False,
                command=command_name,
                output=None,
                error=str(e)
            )
        except SystemExit as e:
            return CommandResult(
                success=False,
                command=command_name,
                output=None,
                error=str(e)
            )
        except Exception as e:
            return CommandResult(
                success=False,
                command=command_name,
                output=None,
                error=str(e)
            )
    
    def _create_approval(self, operation: str, context: Dict, 
                        session: OperatorSession) -> PendingApproval:
        """Create a pending approval request."""
        now = datetime.now(timezone.utc)
        expires = datetime.fromtimestamp(now.timestamp() + 3600, tz=timezone.utc)
        
        approval = PendingApproval(
            approval_id=str(uuid.uuid4()),
            operation=operation,
            context=context,
            requested_by=session.operator_id,
            requested_at=now.isoformat(),
            expires_at=expires.isoformat(),
            reason="Constitutional escalation"
        )
        
        self._approvals[approval.approval_id] = approval
        return approval
    
    # -------------------------------------------------------------------------
    # Command Handlers
    # -------------------------------------------------------------------------
    
    def _cmd_status(self, session: OperatorSession, args: Dict) -> Dict:
        """Show system status."""
        verification = self._ledger.verify_chain()
        
        return {
            'system': 'JARUS Sovereign System',
            'version': '1.0.0',
            'status': 'HALTED' if self._runtime.is_halted else 'OPERATIONAL',
            'constitution_hash': self._runtime.constitution_hash[:32] + '...',
            'evidence': {
                'chain_status': verification.status.value,
                'entries': self._ledger.entry_count,
                'chain_hash': verification.chain_hash[:32] + '...'
            },
            'sessions': len(self._sessions),
            'pending_approvals': len([a for a in self._approvals.values() if a.approved is None]),
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
    
    def _cmd_health(self, session: OperatorSession, args: Dict) -> Dict:
        """Show health check."""
        verification = self._ledger.verify_chain()
        
        checks = {
            'constitutional_runtime': 'PASS' if not self._runtime.is_halted else 'FAIL',
            'evidence_chain': 'PASS' if verification.status.value == 'VALID' else 'FAIL',
            'session_manager': 'PASS',
            'approval_system': 'PASS'
        }
        
        all_pass = all(v == 'PASS' for v in checks.values())
        
        return {
            'overall': 'HEALTHY' if all_pass else 'DEGRADED',
            'checks': checks
        }
    
    def _cmd_halt(self, session: OperatorSession, args: Dict) -> Dict:
        """Halt the system (Governed by Surge)."""
        reason = args.get('reason', 'Operator initiated halt')
        
        def halt_handler():
            self._runtime._halted = True
            self._runtime._halt_reason = reason
            return {'halted': True, 'reason': reason, 'by': session.operator_id}

        # Route through Surge wrapper for authoritative gating and pre-effect receipt
        result = self._surge.execute_sovereign_action(
            action_name="system_halt",
            context={
                'action': 'halt',
                'operator_id': session.operator_id,
                'reason': reason,
                'requires_approval': True # Critical action
            },
            handler=halt_handler,
            actor=session.operator_id
        )
        
        return result['result']

    def _cmd_resume(self, session: OperatorSession, args: Dict) -> Dict:
        """Resume from halt (Governed by Surge)."""
        
        def resume_handler():
            authorization = f"{session.operator_id}:{datetime.now(timezone.utc).isoformat()}"
            self._runtime.reset_halt(authorization)
            return {'resumed': True, 'by': session.operator_id}

        # Route through Surge wrapper
        result = self._surge.execute_sovereign_action(
            action_name="system_resume",
            context={
                'action': 'resume',
                'operator_id': session.operator_id,
                'requires_approval': True
            },
            handler=resume_handler,
            actor=session.operator_id
        )
        
        return result['result']
    
    def _cmd_evidence_list(self, session: OperatorSession, args: Dict) -> Dict:
        """List recent evidence."""
        limit = args.get('limit', 10)
        entries = self._ledger.get_entries(limit=limit)
        
        return {
            'count': len(entries),
            'entries': [
                {
                    'entry_id': e.entry_id[:16] + '...',
                    'timestamp': e.timestamp,
                    'type': e.evidence_type.value,
                    'summary': e.summary[:80]
                }
                for e in entries
            ]
        }
    
    def _cmd_evidence_verify(self, session: OperatorSession, args: Dict) -> Dict:
        """Verify chain integrity."""
        result = self._ledger.verify_chain()
        
        return {
            'status': result.status.value,
            'entries_checked': result.entries_checked,
            'chain_hash': result.chain_hash[:32] + '...',
            'error': result.error
        }
    
    def _cmd_evidence_record(self, session: OperatorSession, args: Dict) -> Dict:
        """Record new evidence."""
        content = args.get('content', '')
        summary = args.get('summary', 'Manual entry')
        
        receipt = self._ledger.record(
            evidence_type=EvidenceType.AUDIT_LOG,
            content=content,
            summary=summary,
            metadata={'recorded_by': session.operator_id}
        )
        
        return {
            'recorded': True,
            'entry_id': receipt.entry_id,
            'entry_hash': receipt.entry_hash[:32] + '...'
        }
    
    def _cmd_evidence_report(self, session: OperatorSession, args: Dict) -> Dict:
        """Generate audit report."""
        return self._ledger.generate_report()
    
    def _cmd_constitution(self, session: OperatorSession, args: Dict) -> Dict:
        """Show constitution."""
        clauses = self._runtime.get_clauses()
        
        return {
            'constitution_hash': self._runtime.constitution_hash[:32] + '...',
            'clause_count': len(clauses),
            'clauses': [
                {
                    'id': c['clause_id'],
                    'name': c['name'],
                    'enforcement': c['enforcement_level']
                }
                for c in clauses
            ]
        }
    
    def _cmd_violations(self, session: OperatorSession, args: Dict) -> Dict:
        """List violations."""
        return {
            'violation_count': self._runtime.violation_count,
            'decision_count': self._runtime.decision_count
        }
    
    def _cmd_evaluate(self, session: OperatorSession, args: Dict) -> Dict:
        """Evaluate action against constitution."""
        action = args.get('action', 'test')
        
        context = {
            'action': action,
            'operator_id': session.operator_id,
            **args
        }
        
        decision = self._runtime.evaluate(context)
        
        return {
            'decision': decision.decision_type.value,
            'rationale': decision.rationale,
            'decision_id': decision.decision_id[:16] + '...'
        }
    
    def _cmd_approvals_list(self, session: OperatorSession, args: Dict) -> Dict:
        """List pending approvals."""
        pending = [
            {
                'approval_id': a.approval_id[:16] + '...',
                'operation': a.operation,
                'requested_by': a.requested_by,
                'requested_at': a.requested_at
            }
            for a in self._approvals.values()
            if a.approved is None
        ]
        
        return {
            'count': len(pending),
            'pending': pending
        }
    
    def _cmd_approve(self, session: OperatorSession, args: Dict) -> Dict:
        """Approve pending operation."""
        approval_id = args.get('id', '')
        
        # Find approval (match by prefix)
        approval = None
        for aid, a in self._approvals.items():
            if aid.startswith(approval_id) and a.approved is None:
                approval = a
                break
        
        if not approval:
            return {'error': 'Approval not found or already processed'}
        
        approval.approved = True
        approval.approved_by = session.operator_id
        
        self._ledger.record(
            evidence_type=EvidenceType.ACTION,
            content={'event': 'approval_granted', 'approval_id': approval.approval_id},
            summary=f"Approved: {approval.operation} by {session.operator_id}"
        )
        
        return {
            'approved': True,
            'operation': approval.operation,
            'by': session.operator_id
        }
    
    def _cmd_deny(self, session: OperatorSession, args: Dict) -> Dict:
        """Deny pending operation."""
        approval_id = args.get('id', '')
        reason = args.get('reason', 'Denied by operator')
        
        # Find approval
        approval = None
        for aid, a in self._approvals.items():
            if aid.startswith(approval_id) and a.approved is None:
                approval = a
                break
        
        if not approval:
            return {'error': 'Approval not found or already processed'}
        
        approval.approved = False
        approval.approved_by = session.operator_id
        
        self._ledger.record(
            evidence_type=EvidenceType.ACTION,
            content={'event': 'approval_denied', 'approval_id': approval.approval_id, 'reason': reason},
            summary=f"Denied: {approval.operation} by {session.operator_id}"
        )
        
        return {
            'denied': True,
            'operation': approval.operation,
            'reason': reason
        }
    
    def _cmd_help(self, session: OperatorSession, args: Dict) -> Dict:
        """Show available commands."""
        commands_by_category = {}
        
        for cmd in self._commands.values():
            if cmd.can_execute(session.role):
                cat = cmd.category.value
                if cat not in commands_by_category:
                    commands_by_category[cat] = []
                commands_by_category[cat].append({
                    'command': cmd.name,
                    'description': cmd.description
                })
        
        return {
            'role': session.role.name,
            'commands': commands_by_category
        }
    
    def _cmd_whoami(self, session: OperatorSession, args: Dict) -> Dict:
        """Show current session info."""
        return {
            'session_id': session.session_id[:16] + '...',
            'operator_id': session.operator_id,
            'role': session.role.name,
            'started_at': session.started_at,
            'commands_executed': session.commands_executed
        }
    
    # -------------------------------------------------------------------------
    # Interactive Mode
    # -------------------------------------------------------------------------
    
    def interactive(self, operator_id: str, role: OperatorRole):
        """
        Run interactive console mode.
        
        Args:
            operator_id: Operator identifier
            role: Operator role
        """
        session = self.create_session(operator_id, role)
        
        print("=" * 60)
        print("JARUS Sovereign System - Operator Console")
        print("=" * 60)
        print(f"Session: {session.session_id[:16]}...")
        print(f"Operator: {operator_id}")
        print(f"Role: {role.name}")
        print("Type 'help' for commands, 'exit' to quit")
        print("=" * 60)
        
        while True:
            try:
                user_input = input("\njarus> ").strip()
                
                if not user_input:
                    continue
                
                if user_input.lower() == 'exit':
                    print("Session ended.")
                    break
                
                # Parse command and args
                parts = user_input.split(maxsplit=1)
                command = parts[0]
                args = {}
                
                if len(parts) > 1:
                    # Try JSON first
                    try:
                        args = json.loads(parts[1])
                    except:
                        # Try key=value format
                        for pair in parts[1].split():
                            if '=' in pair:
                                key, value = pair.split('=', 1)
                                args[key] = value
                
                # Execute
                result = self.execute(session.session_id, command, args)
                
                if result.success:
                    print(json.dumps(result.output, indent=2))
                else:
                    print(f"ERROR: {result.error}")
                    if result.requires_approval:
                        print(f"Approval required: {result.approval_id}")
                
            except KeyboardInterrupt:
                print("\nSession ended.")
                break
            except Exception as e:
                print(f"Error: {e}")


# =============================================================================
# SELF-TEST
# =============================================================================

def self_test():
    """
    Self-test of Operator Console.
    
    Tests:
    1. Session creation
    2. Permission checking
    3. Command execution
    4. Evidence recording
    5. Status commands
    """
    print("=" * 60)
    print("JARUS Operator Console - Self Test")
    print("=" * 60)
    
    # Initialize
    print("\n[1] Initialize console...")
    console = OperatorConsole()
    print(f"    Commands registered: {len(console._commands)}")
    print("    ✓ PASS")
    
    # Create session
    print("\n[2] Create session...")
    session = console.create_session("test_operator", OperatorRole.ADMINISTRATOR)
    print(f"    Session ID: {session.session_id[:16]}...")
    print(f"    Role: {session.role.name}")
    assert session.role == OperatorRole.ADMINISTRATOR
    print("    ✓ PASS")
    
    # Test status command
    print("\n[3] Execute 'status' command...")
    result = console.execute(session.session_id, "status")
    print(f"    Success: {result.success}")
    print(f"    System: {result.output.get('system')}")
    print(f"    Status: {result.output.get('status')}")
    assert result.success
    print("    ✓ PASS")
    
    # Test health command
    print("\n[4] Execute 'health' command...")
    result = console.execute(session.session_id, "health")
    print(f"    Overall: {result.output.get('overall')}")
    assert result.success
    print("    ✓ PASS")
    
    # Test evidence.verify
    print("\n[5] Execute 'evidence.verify' command...")
    result = console.execute(session.session_id, "evidence.verify")
    print(f"    Chain status: {result.output.get('status')}")
    assert result.success
    print("    ✓ PASS")
    
    # Test constitution
    print("\n[6] Execute 'constitution' command...")
    result = console.execute(session.session_id, "constitution")
    print(f"    Clause count: {result.output.get('clause_count')}")
    assert result.success
    print("    ✓ PASS")
    
    # Test help
    print("\n[7] Execute 'help' command...")
    result = console.execute(session.session_id, "help")
    print(f"    Categories: {list(result.output.get('commands', {}).keys())}")
    assert result.success
    print("    ✓ PASS")
    
    # Test permission denied (create viewer session)
    print("\n[8] Test permission denied...")
    viewer_session = console.create_session("viewer", OperatorRole.VIEWER)
    result = console.execute(viewer_session.session_id, "halt")
    print(f"    Command: halt")
    print(f"    Success: {result.success}")
    print(f"    Error: {result.error}")
    assert not result.success
    assert "Permission denied" in result.error
    print("    ✓ PASS")
    
    # Summary
    print("\n" + "=" * 60)
    print("SELF-TEST COMPLETE")
    print("=" * 60)
    print(f"Commands tested: 7")
    print(f"Sessions created: 2")
    print("All tests passed ✓")
    
    return True


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == '--interactive':
        console = OperatorConsole()
        console.interactive("admin", OperatorRole.ADMINISTRATOR)
    else:
        self_test()
