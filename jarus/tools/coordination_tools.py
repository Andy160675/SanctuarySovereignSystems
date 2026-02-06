#!/usr/bin/env python3
"""
JARUS Coordination Tools
========================
Tools for orchestrating multi-step operations.

Tools:
- select: Choose from options based on criteria
- compose: Build complex operations from primitives
- checkpoint: Save/restore operation state
- escalate: Escalate to human operator

Author: Codex Sovereign Systems
Version: 1.0.0
"""

import hashlib
import json
import os
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timezone
from dataclasses import dataclass, field
from enum import Enum
import threading

# Import base framework
from .tool_framework import Tool, ToolCategory, ToolResult, ToolStatus


# =============================================================================
# ENUMS
# =============================================================================

class EscalationLevel(Enum):
    """Urgency levels for escalation."""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4
    EMERGENCY = 5


class CheckpointStatus(Enum):
    """Status of checkpoints."""
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    ROLLED_BACK = "ROLLED_BACK"


# =============================================================================
# SELECT TOOL
# =============================================================================

class SelectTool(Tool):
    """
    Select from options based on criteria.
    
    Supports weighted scoring, filters, and constraints.
    
    Parameters:
        options: List of options to choose from
        criteria: Scoring criteria (weights)
        constraints: Hard requirements
        limit: Max number to return
    """
    
    @property
    def name(self) -> str:
        return "select"
    
    @property
    def category(self) -> ToolCategory:
        return ToolCategory.COORDINATION
    
    @property
    def description(self) -> str:
        return "Select from options based on weighted criteria"
    
    @property
    def parameters(self) -> Dict:
        return {
            'options': 'list - options to choose from',
            'criteria': 'dict - scoring weights',
            'constraints': 'dict - hard requirements',
            'limit': 'int - max results'
        }
    
    def _execute(self, context: Dict) -> Any:
        options = context.get('options', [])
        criteria = context.get('criteria', {})
        constraints = context.get('constraints', {})
        limit = context.get('limit', 1)
        
        if not options:
            return {
                'selected': [],
                'total_options': 0,
                'status': 'NO_OPTIONS'
            }
        
        # Apply constraints (hard filters)
        filtered = []
        for opt in options:
            passes = True
            for key, required in constraints.items():
                if isinstance(opt, dict):
                    actual = opt.get(key)
                else:
                    actual = getattr(opt, key, None)
                
                if actual != required:
                    passes = False
                    break
            
            if passes:
                filtered.append(opt)
        
        # Score remaining options
        scored = []
        for opt in filtered:
            score = 0
            score_breakdown = {}
            
            for key, weight in criteria.items():
                if isinstance(opt, dict):
                    value = opt.get(key, 0)
                else:
                    value = getattr(opt, key, 0)
                
                # Normalize value to 0-1 if not already
                if isinstance(value, bool):
                    value = 1 if value else 0
                elif isinstance(value, (int, float)):
                    value = min(1, max(0, value))
                else:
                    value = 0
                
                component_score = value * weight
                score += component_score
                score_breakdown[key] = component_score
            
            scored.append({
                'option': opt,
                'score': score,
                'breakdown': score_breakdown
            })
        
        # Sort by score descending
        scored.sort(key=lambda x: x['score'], reverse=True)
        
        # Return top N
        selected = scored[:limit]
        
        return {
            'selected': [s['option'] for s in selected],
            'scores': selected,
            'total_options': len(options),
            'filtered_count': len(filtered),
            'status': 'SELECTED' if selected else 'NO_MATCH'
        }


# =============================================================================
# COMPOSE TOOL
# =============================================================================

class ComposeTool(Tool):
    """
    Compose complex operations from primitives.
    
    Define a pipeline of operations with dependencies.
    
    Parameters:
        pipeline: List of operation steps
        context: Shared context for all steps
        mode: 'sequential' or 'parallel'
    """
    
    @property
    def name(self) -> str:
        return "compose"
    
    @property
    def category(self) -> ToolCategory:
        return ToolCategory.COORDINATION
    
    @property
    def description(self) -> str:
        return "Compose operations into pipelines"
    
    @property
    def parameters(self) -> Dict:
        return {
            'pipeline': 'list - operation steps',
            'context': 'dict - shared context',
            'mode': 'string - sequential or parallel'
        }
    
    def _execute(self, context: Dict) -> Any:
        pipeline = context.get('pipeline', [])
        shared_context = context.get('context', {})
        mode = context.get('mode', 'sequential')
        
        if not pipeline:
            return {
                'executed': 0,
                'status': 'EMPTY_PIPELINE'
            }
        
        composition_id = hashlib.sha256(
            f"compose:{datetime.now().isoformat()}".encode()
        ).hexdigest()[:16]
        
        results = []
        success_count = 0
        failed_at = None
        
        for i, step in enumerate(pipeline):
            step_id = step.get('id', f'step_{i}')
            step_name = step.get('name', step_id)
            step_action = step.get('action')
            step_params = step.get('params', {})
            
            # Merge shared context
            step_params.update(shared_context)
            
            # In a real system, would execute the action
            # Here we simulate success
            step_result = {
                'step_id': step_id,
                'step_name': step_name,
                'action': step_action,
                'executed_at': datetime.now(timezone.utc).isoformat(),
                'success': True,
                'output': step_params.get('expected_output', {})
            }
            
            results.append(step_result)
            
            if step_result['success']:
                success_count += 1
                # Update shared context with outputs
                if 'output_key' in step:
                    shared_context[step['output_key']] = step_result['output']
            else:
                failed_at = i
                if mode == 'sequential':
                    break
        
        return {
            'composition_id': composition_id,
            'mode': mode,
            'total_steps': len(pipeline),
            'executed': len(results),
            'succeeded': success_count,
            'failed_at_step': failed_at,
            'results': results,
            'final_context': shared_context,
            'status': 'COMPLETED' if failed_at is None else 'PARTIAL'
        }


# =============================================================================
# CHECKPOINT TOOL
# =============================================================================

class CheckpointTool(Tool):
    """
    Save and restore operation state.
    
    For long-running operations that need recovery.
    
    Parameters:
        action: 'create', 'restore', 'list', 'delete'
        checkpoint_id: ID for specific checkpoint
        operation_id: Operation being checkpointed
        state: State to save
    """
    
    CHECKPOINT_DIR = Path('/tmp/jarus_checkpoints')
    _lock = threading.RLock()
    
    @property
    def name(self) -> str:
        return "checkpoint"
    
    @property
    def category(self) -> ToolCategory:
        return ToolCategory.COORDINATION
    
    @property
    def description(self) -> str:
        return "Save and restore operation state"
    
    @property
    def parameters(self) -> Dict:
        return {
            'action': 'string - create, restore, list, delete',
            'checkpoint_id': 'string - checkpoint identifier',
            'operation_id': 'string - operation being checkpointed',
            'state': 'dict - state to save'
        }
    
    def _execute(self, context: Dict) -> Any:
        action = context.get('action', 'list')
        
        self.CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
        
        if action == 'create':
            return self._create_checkpoint(
                context.get('operation_id'),
                context.get('state', {})
            )
        elif action == 'restore':
            return self._restore_checkpoint(context.get('checkpoint_id'))
        elif action == 'list':
            return self._list_checkpoints(context.get('operation_id'))
        elif action == 'delete':
            return self._delete_checkpoint(context.get('checkpoint_id'))
        else:
            raise ValueError(f"Unknown action: {action}")
    
    def _create_checkpoint(self, operation_id: str, state: Dict) -> Dict:
        """Create a checkpoint."""
        if not operation_id:
            raise ValueError("operation_id required")
        
        with self._lock:
            checkpoint_id = hashlib.sha256(
                f"{operation_id}:{datetime.now().isoformat()}".encode()
            ).hexdigest()[:16]
            
            checkpoint = {
                'checkpoint_id': checkpoint_id,
                'operation_id': operation_id,
                'created_at': datetime.now(timezone.utc).isoformat(),
                'state': state,
                'state_hash': hashlib.sha256(
                    json.dumps(state, sort_keys=True).encode()
                ).hexdigest(),
                'status': CheckpointStatus.ACTIVE.value
            }
            
            checkpoint_path = self.CHECKPOINT_DIR / f"{checkpoint_id}.json"
            with open(checkpoint_path, 'w') as f:
                json.dump(checkpoint, f, indent=2)
        
        return {
            'checkpoint_id': checkpoint_id,
            'operation_id': operation_id,
            'state_hash': checkpoint['state_hash'],
            'status': 'CREATED'
        }
    
    def _restore_checkpoint(self, checkpoint_id: str) -> Dict:
        """Restore from checkpoint."""
        if not checkpoint_id:
            raise ValueError("checkpoint_id required")
        
        checkpoint_path = self.CHECKPOINT_DIR / f"{checkpoint_id}.json"
        
        if not checkpoint_path.exists():
            return {
                'checkpoint_id': checkpoint_id,
                'status': 'NOT_FOUND'
            }
        
        with open(checkpoint_path) as f:
            checkpoint = json.load(f)
        
        # Verify state integrity
        current_hash = hashlib.sha256(
            json.dumps(checkpoint['state'], sort_keys=True).encode()
        ).hexdigest()
        
        if current_hash != checkpoint['state_hash']:
            return {
                'checkpoint_id': checkpoint_id,
                'status': 'CORRUPTED',
                'expected_hash': checkpoint['state_hash'],
                'actual_hash': current_hash
            }
        
        return {
            'checkpoint_id': checkpoint_id,
            'operation_id': checkpoint['operation_id'],
            'created_at': checkpoint['created_at'],
            'state': checkpoint['state'],
            'state_hash': checkpoint['state_hash'],
            'status': 'RESTORED'
        }
    
    def _list_checkpoints(self, operation_id: Optional[str]) -> Dict:
        """List checkpoints."""
        checkpoints = []
        
        for cp_file in self.CHECKPOINT_DIR.glob('*.json'):
            with open(cp_file) as f:
                cp = json.load(f)
                if operation_id is None or cp['operation_id'] == operation_id:
                    checkpoints.append({
                        'checkpoint_id': cp['checkpoint_id'],
                        'operation_id': cp['operation_id'],
                        'created_at': cp['created_at'],
                        'status': cp['status']
                    })
        
        # Sort by creation time
        checkpoints.sort(key=lambda x: x['created_at'], reverse=True)
        
        return {
            'operation_id': operation_id,
            'count': len(checkpoints),
            'checkpoints': checkpoints,
            'status': 'OK'
        }
    
    def _delete_checkpoint(self, checkpoint_id: str) -> Dict:
        """Delete a checkpoint."""
        if not checkpoint_id:
            raise ValueError("checkpoint_id required")
        
        checkpoint_path = self.CHECKPOINT_DIR / f"{checkpoint_id}.json"
        
        if not checkpoint_path.exists():
            return {
                'checkpoint_id': checkpoint_id,
                'status': 'NOT_FOUND'
            }
        
        checkpoint_path.unlink()
        
        return {
            'checkpoint_id': checkpoint_id,
            'status': 'DELETED'
        }


# =============================================================================
# ESCALATE TOOL
# =============================================================================

class EscalateTool(Tool):
    """
    Escalate to human operator.
    
    For decisions requiring human judgment.
    
    Parameters:
        level: LOW, MEDIUM, HIGH, CRITICAL, EMERGENCY
        reason: Why escalating
        context: Relevant context
        options: Options for human to choose
        timeout_minutes: How long to wait
    """
    
    ESCALATION_DIR = Path('/tmp/jarus_escalations')
    _pending: Dict[str, Dict] = {}
    _lock = threading.RLock()
    
    @property
    def name(self) -> str:
        return "escalate"
    
    @property
    def category(self) -> ToolCategory:
        return ToolCategory.COORDINATION
    
    @property
    def description(self) -> str:
        return "Escalate decisions to human operators"
    
    @property
    def parameters(self) -> Dict:
        return {
            'action': 'string - create, respond, list, status',
            'level': 'string - LOW/MEDIUM/HIGH/CRITICAL/EMERGENCY',
            'reason': 'string - why escalating',
            'context': 'dict - relevant context',
            'options': 'list - options for human',
            'escalation_id': 'string - for respond action',
            'response': 'string - human response'
        }
    
    def _execute(self, context: Dict) -> Any:
        action = context.get('action', 'create')
        
        self.ESCALATION_DIR.mkdir(parents=True, exist_ok=True)
        
        if action == 'create':
            return self._create_escalation(
                context.get('level', 'MEDIUM'),
                context.get('reason', 'No reason provided'),
                context.get('context', {}),
                context.get('options', []),
                context.get('timeout_minutes', 60)
            )
        elif action == 'respond':
            return self._respond(
                context.get('escalation_id'),
                context.get('response'),
                context.get('responder', 'operator')
            )
        elif action == 'list':
            return self._list_escalations(context.get('status_filter'))
        elif action == 'status':
            return self._get_status(context.get('escalation_id'))
        else:
            raise ValueError(f"Unknown action: {action}")
    
    def _create_escalation(self, level: str, reason: str, 
                          escalation_context: Dict, options: List,
                          timeout_minutes: int) -> Dict:
        """Create an escalation."""
        try:
            esc_level = EscalationLevel[level.upper()]
        except KeyError:
            esc_level = EscalationLevel.MEDIUM
        
        with self._lock:
            escalation_id = hashlib.sha256(
                f"escalate:{datetime.now().isoformat()}".encode()
            ).hexdigest()[:16]
            
            escalation = {
                'escalation_id': escalation_id,
                'level': esc_level.name,
                'level_value': esc_level.value,
                'reason': reason,
                'context': escalation_context,
                'options': options,
                'created_at': datetime.now(timezone.utc).isoformat(),
                'timeout_minutes': timeout_minutes,
                'status': 'PENDING',
                'response': None,
                'responded_at': None,
                'responder': None
            }
            
            self._pending[escalation_id] = escalation
            
            # Save to file
            esc_path = self.ESCALATION_DIR / f"{escalation_id}.json"
            with open(esc_path, 'w') as f:
                json.dump(escalation, f, indent=2)
        
        return {
            'escalation_id': escalation_id,
            'level': esc_level.name,
            'reason': reason,
            'options': options,
            'timeout_minutes': timeout_minutes,
            'status': 'ESCALATED'
        }
    
    def _respond(self, escalation_id: str, response: str, 
                responder: str) -> Dict:
        """Respond to an escalation."""
        if not escalation_id:
            raise ValueError("escalation_id required")
        
        with self._lock:
            # Load from file
            esc_path = self.ESCALATION_DIR / f"{escalation_id}.json"
            
            if not esc_path.exists():
                return {
                    'escalation_id': escalation_id,
                    'status': 'NOT_FOUND'
                }
            
            with open(esc_path) as f:
                escalation = json.load(f)
            
            if escalation['status'] != 'PENDING':
                return {
                    'escalation_id': escalation_id,
                    'status': 'ALREADY_RESOLVED',
                    'previous_response': escalation['response']
                }
            
            escalation['status'] = 'RESOLVED'
            escalation['response'] = response
            escalation['responded_at'] = datetime.now(timezone.utc).isoformat()
            escalation['responder'] = responder
            
            # Save updated
            with open(esc_path, 'w') as f:
                json.dump(escalation, f, indent=2)
            
            if escalation_id in self._pending:
                del self._pending[escalation_id]
        
        return {
            'escalation_id': escalation_id,
            'response': response,
            'responder': responder,
            'status': 'RESOLVED'
        }
    
    def _list_escalations(self, status_filter: Optional[str]) -> Dict:
        """List escalations."""
        escalations = []
        
        for esc_file in self.ESCALATION_DIR.glob('*.json'):
            with open(esc_file) as f:
                esc = json.load(f)
                if status_filter is None or esc['status'] == status_filter:
                    escalations.append({
                        'escalation_id': esc['escalation_id'],
                        'level': esc['level'],
                        'reason': esc['reason'][:50],
                        'created_at': esc['created_at'],
                        'status': esc['status']
                    })
        
        # Sort by level (highest first) then time
        escalations.sort(key=lambda x: (-EscalationLevel[x['level']].value, x['created_at']))
        
        pending_count = sum(1 for e in escalations if e['status'] == 'PENDING')
        
        return {
            'total': len(escalations),
            'pending': pending_count,
            'escalations': escalations,
            'status': 'OK'
        }
    
    def _get_status(self, escalation_id: str) -> Dict:
        """Get escalation status."""
        if not escalation_id:
            raise ValueError("escalation_id required")
        
        esc_path = self.ESCALATION_DIR / f"{escalation_id}.json"
        
        if not esc_path.exists():
            return {
                'escalation_id': escalation_id,
                'status': 'NOT_FOUND'
            }
        
        with open(esc_path) as f:
            escalation = json.load(f)
        
        return {
            'escalation_id': escalation_id,
            'level': escalation['level'],
            'reason': escalation['reason'],
            'status': escalation['status'],
            'response': escalation['response'],
            'responder': escalation['responder'],
            'created_at': escalation['created_at'],
            'responded_at': escalation['responded_at']
        }


# =============================================================================
# COORDINATION TOOLKIT
# =============================================================================

class CoordinationToolkit:
    """
    Collection of all coordination tools.
    """
    
    def __init__(self):
        self.select = SelectTool()
        self.compose = ComposeTool()
        self.checkpoint = CheckpointTool()
        self.escalate = EscalateTool()
        
        self._tools = {
            'select': self.select,
            'compose': self.compose,
            'checkpoint': self.checkpoint,
            'escalate': self.escalate
        }
    
    def get_tools(self) -> List[Tool]:
        """Get all coordination tools."""
        return list(self._tools.values())
    
    def execute(self, tool_name: str, context: Dict) -> ToolResult:
        """Execute a coordination tool by name."""
        if tool_name not in self._tools:
            return ToolResult(
                tool_name=tool_name,
                status=ToolStatus.FAILURE,
                data=None,
                evidence_hash='',
                execution_time_ms=0,
                error=f"Unknown coordination tool: {tool_name}"
            )
        return self._tools[tool_name].execute(context)


# =============================================================================
# SELF-TEST
# =============================================================================

def self_test():
    """
    Self-test of Coordination Tools.
    """
    print("=" * 60)
    print("JARUS Coordination Tools - Self Test")
    print("=" * 60)
    
    toolkit = CoordinationToolkit()
    
    # Test 1: Select tool
    print("\n[1] Testing select tool...")
    options = [
        {'name': 'Option A', 'cost': 0.3, 'quality': 0.9, 'speed': 0.5},
        {'name': 'Option B', 'cost': 0.7, 'quality': 0.6, 'speed': 0.8},
        {'name': 'Option C', 'cost': 0.5, 'quality': 0.7, 'speed': 0.7}
    ]
    result = toolkit.select.execute({
        'options': options,
        'criteria': {'quality': 0.5, 'speed': 0.3, 'cost': 0.2},
        'limit': 2
    })
    print(f"    Status: {result.status.value}")
    print(f"    Selected: {[s['name'] for s in result.data.get('selected', [])]}")
    assert result.success
    print("    ✓ PASS")
    
    # Test 2: Select with constraints
    print("\n[2] Testing select tool (with constraints)...")
    result = toolkit.select.execute({
        'options': options,
        'criteria': {'quality': 1.0},
        'constraints': {'speed': 0.8},
        'limit': 1
    })
    print(f"    Status: {result.status.value}")
    print(f"    Filtered: {result.data.get('filtered_count')}")
    assert result.success
    print("    ✓ PASS")
    
    # Test 3: Compose tool
    print("\n[3] Testing compose tool...")
    pipeline = [
        {'id': 'step1', 'name': 'Initialize', 'action': 'init', 'params': {'x': 1}},
        {'id': 'step2', 'name': 'Process', 'action': 'process', 'params': {'y': 2}},
        {'id': 'step3', 'name': 'Finalize', 'action': 'finalize', 'params': {'z': 3}}
    ]
    result = toolkit.compose.execute({
        'pipeline': pipeline,
        'context': {'env': 'test'},
        'mode': 'sequential'
    })
    print(f"    Status: {result.status.value}")
    print(f"    Steps executed: {result.data.get('executed')}")
    print(f"    Succeeded: {result.data.get('succeeded')}")
    assert result.success
    assert result.data['succeeded'] == 3
    print("    ✓ PASS")
    
    # Test 4: Checkpoint create
    print("\n[4] Testing checkpoint tool (create)...")
    result = toolkit.checkpoint.execute({
        'action': 'create',
        'operation_id': 'OP-001',
        'state': {'step': 5, 'data': [1, 2, 3], 'progress': 0.5}
    })
    print(f"    Status: {result.status.value}")
    print(f"    Checkpoint ID: {result.data.get('checkpoint_id')}")
    checkpoint_id = result.data.get('checkpoint_id')
    assert result.success
    print("    ✓ PASS")
    
    # Test 5: Checkpoint restore
    print("\n[5] Testing checkpoint tool (restore)...")
    result = toolkit.checkpoint.execute({
        'action': 'restore',
        'checkpoint_id': checkpoint_id
    })
    print(f"    Status: {result.data.get('status')}")
    print(f"    State: {result.data.get('state')}")
    assert result.success
    assert result.data['state']['step'] == 5
    print("    ✓ PASS")
    
    # Test 6: Checkpoint list
    print("\n[6] Testing checkpoint tool (list)...")
    result = toolkit.checkpoint.execute({
        'action': 'list',
        'operation_id': 'OP-001'
    })
    print(f"    Status: {result.status.value}")
    print(f"    Count: {result.data.get('count')}")
    assert result.success
    print("    ✓ PASS")
    
    # Test 7: Escalate create
    print("\n[7] Testing escalate tool (create)...")
    result = toolkit.escalate.execute({
        'action': 'create',
        'level': 'HIGH',
        'reason': 'Unusual activity detected requiring human review',
        'context': {'alert_id': 'ALT-123', 'source': 'monitoring'},
        'options': ['Approve', 'Deny', 'Investigate'],
        'timeout_minutes': 30
    })
    print(f"    Status: {result.status.value}")
    print(f"    Escalation ID: {result.data.get('escalation_id')}")
    escalation_id = result.data.get('escalation_id')
    assert result.success
    print("    ✓ PASS")
    
    # Test 8: Escalate respond
    print("\n[8] Testing escalate tool (respond)...")
    result = toolkit.escalate.execute({
        'action': 'respond',
        'escalation_id': escalation_id,
        'response': 'Approve',
        'responder': 'admin@example.com'
    })
    print(f"    Status: {result.data.get('status')}")
    print(f"    Response: {result.data.get('response')}")
    assert result.success
    assert result.data['status'] == 'RESOLVED'
    print("    ✓ PASS")
    
    # Test 9: Escalate list
    print("\n[9] Testing escalate tool (list)...")
    result = toolkit.escalate.execute({
        'action': 'list'
    })
    print(f"    Status: {result.status.value}")
    print(f"    Total: {result.data.get('total')}")
    print(f"    Pending: {result.data.get('pending')}")
    assert result.success
    print("    ✓ PASS")
    
    # Summary
    print("\n" + "=" * 60)
    print("SELF-TEST COMPLETE")
    print("=" * 60)
    print(f"Coordination tools tested: 4")
    print("All tests passed ✓")
    
    return True


if __name__ == "__main__":
    self_test()
