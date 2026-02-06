#!/usr/bin/env python3
"""
JARUS Enforcement Tools
=======================
Tools for blocking and enforcing policies.

Tools:
- block: Block operations temporarily
- enforce: Policy enforcement
- quarantine: Isolate files
- halt: System halt (requires approval)

Author: Codex Sovereign Systems
Version: 1.0.0
"""

import hashlib
import json
import shutil
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime, timezone, timedelta

from .tool_base import Tool, ToolSpec, ToolCategory


# =============================================================================
# BLOCK TOOL
# =============================================================================

class BlockTool(Tool):
    """Block operations temporarily."""
    
    # In-memory block list (would be persisted in production)
    _blocks: Dict[str, Dict] = {}
    
    @property
    def spec(self) -> ToolSpec:
        return ToolSpec(
            name="block",
            category=ToolCategory.ENFORCEMENT,
            description="Block operations temporarily",
            parameters={
                'target': {'type': 'str', 'required': True, 'description': 'What to block'},
                'reason': {'type': 'str', 'required': True, 'description': 'Reason for block'},
                'duration_minutes': {'type': 'int', 'required': False, 'description': 'Block duration'},
                'action': {'type': 'str', 'required': False, 'description': 'add, remove, check, list'}
            }
        )
    
    def _execute(self, params: Dict) -> Dict:
        target = params['target']
        reason = params.get('reason', 'No reason provided')
        duration = params.get('duration_minutes', 60)
        action = params.get('action', 'add')
        
        now = datetime.now(timezone.utc)
        
        if action == 'add':
            expires = now + timedelta(minutes=duration)
            block_id = hashlib.sha256(f"{target}{now.isoformat()}".encode()).hexdigest()[:12]
            
            BlockTool._blocks[target] = {
                'block_id': block_id,
                'target': target,
                'reason': reason,
                'blocked_at': now.isoformat(),
                'expires_at': expires.isoformat(),
                'duration_minutes': duration
            }
            
            return {'action': 'blocked', 'block_id': block_id, 'target': target, 
                    'expires_at': expires.isoformat()}
        
        elif action == 'remove':
            if target in BlockTool._blocks:
                del BlockTool._blocks[target]
                return {'action': 'unblocked', 'target': target}
            return {'action': 'not_found', 'target': target}
        
        elif action == 'check':
            if target in BlockTool._blocks:
                block = BlockTool._blocks[target]
                expires = datetime.fromisoformat(block['expires_at'].replace('Z', '+00:00'))
                if now > expires:
                    del BlockTool._blocks[target]
                    return {'blocked': False, 'target': target, 'reason': 'Expired'}
                return {'blocked': True, 'target': target, 'reason': block['reason'],
                        'expires_at': block['expires_at']}
            return {'blocked': False, 'target': target}
        
        elif action == 'list':
            active = []
            expired = []
            for t, block in list(BlockTool._blocks.items()):
                expires = datetime.fromisoformat(block['expires_at'].replace('Z', '+00:00'))
                if now > expires:
                    expired.append(t)
                else:
                    active.append({'target': t, 'reason': block['reason'], 
                                  'expires_at': block['expires_at']})
            for t in expired:
                del BlockTool._blocks[t]
            return {'active_blocks': active, 'count': len(active)}
        
        return {'error': f"Unknown action: {action}"}


# =============================================================================
# ENFORCE TOOL
# =============================================================================

class EnforceTool(Tool):
    """Enforce policies on data or operations."""
    
    @property
    def spec(self) -> ToolSpec:
        return ToolSpec(
            name="enforce",
            category=ToolCategory.ENFORCEMENT,
            description="Enforce policies on data or operations",
            parameters={
                'policy': {'type': 'str', 'required': True, 'description': 'Policy to enforce'},
                'target': {'type': 'any', 'required': True, 'description': 'Target data/operation'},
                'action': {'type': 'str', 'required': False, 'description': 'deny, allow, transform'}
            }
        )
    
    # Built-in policies
    POLICIES = {
        'no_pii': {
            'description': 'Block personally identifiable information',
            'patterns': [r'\b\d{3}-\d{2}-\d{4}\b', r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b']
        },
        'no_secrets': {
            'description': 'Block secrets and credentials',
            'patterns': [r'(?i)(password|api[_-]?key|secret)["\s:=]+\S+', r'-----BEGIN.*PRIVATE KEY-----']
        },
        'max_length': {
            'description': 'Enforce maximum length',
            'max_length': 10000
        },
        'alphanumeric_only': {
            'description': 'Only allow alphanumeric characters',
            'pattern': r'^[a-zA-Z0-9\s]+$'
        }
    }
    
    def _execute(self, params: Dict) -> Dict:
        import re
        policy_name = params['policy']
        target = params['target']
        action = params.get('action', 'deny')
        
        if policy_name not in self.POLICIES:
            return {'enforced': False, 'error': f"Unknown policy: {policy_name}",
                    'available_policies': list(self.POLICIES.keys())}
        
        policy = self.POLICIES[policy_name]
        violations = []
        
        target_str = str(target)
        
        # Check patterns
        if 'patterns' in policy:
            for pattern in policy['patterns']:
                if re.search(pattern, target_str):
                    violations.append(f"Pattern violation: {pattern[:30]}...")
        
        # Check pattern (single)
        if 'pattern' in policy:
            if not re.match(policy['pattern'], target_str):
                violations.append(f"Does not match required pattern")
        
        # Check max length
        if 'max_length' in policy:
            if len(target_str) > policy['max_length']:
                violations.append(f"Exceeds max length of {policy['max_length']}")
        
        result = {
            'policy': policy_name,
            'description': policy['description'],
            'compliant': len(violations) == 0,
            'violations': violations,
            'violation_count': len(violations)
        }
        
        if violations and action == 'deny':
            result['action_taken'] = 'denied'
        elif violations and action == 'transform':
            # Simple redaction
            transformed = target_str
            if 'patterns' in policy:
                for pattern in policy['patterns']:
                    transformed = re.sub(pattern, '[REDACTED]', transformed)
            result['action_taken'] = 'transformed'
            result['transformed'] = transformed
        else:
            result['action_taken'] = 'allowed'
        
        return result


# =============================================================================
# QUARANTINE TOOL
# =============================================================================

class QuarantineTool(Tool):
    """Quarantine suspicious files."""
    
    QUARANTINE_DIR = Path('/tmp/jarus_quarantine')
    
    @property
    def spec(self) -> ToolSpec:
        return ToolSpec(
            name="quarantine",
            category=ToolCategory.ENFORCEMENT,
            description="Quarantine suspicious files",
            parameters={
                'file_path': {'type': 'str', 'required': True, 'description': 'File to quarantine'},
                'reason': {'type': 'str', 'required': True, 'description': 'Reason for quarantine'},
                'action': {'type': 'str', 'required': False, 'description': 'quarantine, release, list'}
            },
            requires_approval=False  # Would be True in production
        )
    
    def _execute(self, params: Dict) -> Dict:
        file_path = params.get('file_path', '')
        reason = params.get('reason', 'Suspicious activity')
        action = params.get('action', 'quarantine')
        
        self.QUARANTINE_DIR.mkdir(parents=True, exist_ok=True)
        
        if action == 'quarantine':
            source = Path(file_path)
            if not source.exists():
                return {'quarantined': False, 'error': f"File not found: {file_path}"}
            
            # Create quarantine record
            quarantine_id = hashlib.sha256(f"{file_path}{datetime.now(timezone.utc).isoformat()}".encode()).hexdigest()[:12]
            dest = self.QUARANTINE_DIR / f"{quarantine_id}_{source.name}"
            
            # Move file
            shutil.move(str(source), str(dest))
            
            # Write metadata
            meta = {
                'quarantine_id': quarantine_id,
                'original_path': str(source),
                'quarantine_path': str(dest),
                'reason': reason,
                'quarantined_at': datetime.now(timezone.utc).isoformat()
            }
            meta_path = self.QUARANTINE_DIR / f"{quarantine_id}.json"
            with open(meta_path, 'w') as f:
                json.dump(meta, f, indent=2)
            
            return {'quarantined': True, 'quarantine_id': quarantine_id, 
                    'original_path': str(source), 'reason': reason}
        
        elif action == 'list':
            items = []
            for meta_file in self.QUARANTINE_DIR.glob('*.json'):
                with open(meta_file) as f:
                    items.append(json.load(f))
            return {'quarantine_items': items, 'count': len(items)}
        
        elif action == 'release':
            # Find by quarantine_id
            for meta_file in self.QUARANTINE_DIR.glob('*.json'):
                with open(meta_file) as f:
                    meta = json.load(f)
                if meta.get('quarantine_id') == file_path or str(meta.get('original_path')) == file_path:
                    # Restore file
                    quarantine_path = Path(meta['quarantine_path'])
                    original_path = Path(meta['original_path'])
                    if quarantine_path.exists():
                        shutil.move(str(quarantine_path), str(original_path))
                        meta_file.unlink()
                        return {'released': True, 'restored_to': str(original_path)}
            return {'released': False, 'error': 'Quarantine record not found'}
        
        return {'error': f"Unknown action: {action}"}


# =============================================================================
# HALT TOOL
# =============================================================================

class HaltTool(Tool):
    """Halt system operations (requires approval)."""
    
    @property
    def spec(self) -> ToolSpec:
        return ToolSpec(
            name="halt",
            category=ToolCategory.ENFORCEMENT,
            description="Halt system operations",
            parameters={
                'reason': {'type': 'str', 'required': True, 'description': 'Reason for halt'},
                'scope': {'type': 'str', 'required': False, 'description': 'Scope: full, subsystem'},
                'force': {'type': 'bool', 'required': False, 'description': 'Force halt without cleanup'}
            },
            requires_approval=True
        )
    
    def _execute(self, params: Dict) -> Dict:
        reason = params['reason']
        scope = params.get('scope', 'full')
        force = params.get('force', False)
        
        # In production, this would actually halt operations
        # For now, we just record the intent
        
        halt_record = {
            'halt_id': hashlib.sha256(f"{reason}{datetime.now(timezone.utc).isoformat()}".encode()).hexdigest()[:12],
            'reason': reason,
            'scope': scope,
            'force': force,
            'requested_at': datetime.now(timezone.utc).isoformat(),
            'status': 'recorded'  # Would be 'executed' in production
        }
        
        return halt_record


# =============================================================================
# ENFORCEMENT TOOLKIT
# =============================================================================

class EnforcementToolkit:
    """
    Collection of all enforcement tools.
    """
    
    def __init__(self):
        self.block = BlockTool()
        self.enforce = EnforceTool()
        self.quarantine = QuarantineTool()
        self.halt = HaltTool()
        
        self._tools = {
            'block': self.block,
            'enforce': self.enforce,
            'quarantine': self.quarantine,
            'halt': self.halt
        }
    
    def get_tools(self) -> List[Tool]:
        """Get all enforcement tools."""
        return list(self._tools.values())


# =============================================================================
# SELF-TEST
# =============================================================================

def self_test():
    print("=" * 60)
    print("JARUS Enforcement Tools - Self Test")
    print("=" * 60)
    
    # Test block
    print("\n[1] Test BlockTool...")
    block = BlockTool()
    result = block.execute({'target': 'test_operation', 'reason': 'Testing', 'duration_minutes': 5})
    print(f"    Status: {result.status.value}")
    print(f"    Block ID: {result.output.get('block_id')}")
    assert result.succeeded
    
    # Check block
    result = block.execute({'target': 'test_operation', 'reason': '', 'action': 'check'})
    print(f"    Is blocked: {result.output.get('blocked')}")
    assert result.output.get('blocked')
    
    # Remove block
    result = block.execute({'target': 'test_operation', 'reason': '', 'action': 'remove'})
    print(f"    Unblocked: {result.output.get('action') == 'unblocked'}")
    print("    ✓ PASS")
    
    # Test enforce
    print("\n[2] Test EnforceTool...")
    enforce = EnforceTool()
    
    # Compliant data
    result = enforce.execute({'policy': 'alphanumeric_only', 'target': 'Hello World 123'})
    print(f"    Status: {result.status.value}")
    print(f"    Compliant: {result.output.get('compliant')}")
    assert result.output.get('compliant')
    
    # Non-compliant data
    result = enforce.execute({'policy': 'alphanumeric_only', 'target': 'Hello! @#$%'})
    print(f"    Violations: {result.output.get('violation_count')}")
    assert not result.output.get('compliant')
    print("    ✓ PASS")
    
    # Test quarantine (list only - no actual files)
    print("\n[3] Test QuarantineTool...")
    quarantine = QuarantineTool()
    result = quarantine.execute({'file_path': '', 'reason': '', 'action': 'list'})
    print(f"    Status: {result.status.value}")
    print(f"    Quarantine count: {result.output.get('count', 0)}")
    assert result.succeeded
    print("    ✓ PASS")
    
    # Test halt (requires approval, so it should return REQUIRES_APPROVAL)
    print("\n[4] Test HaltTool...")
    halt = HaltTool()
    result = halt.execute({'reason': 'Test halt', 'scope': 'full'})
    print(f"    Status: {result.status.value}")
    assert result.status.value == 'REQUIRES_APPROVAL'
    print("    ✓ PASS (correctly requires approval)")
    
    print("\n" + "=" * 60)
    print("SELF-TEST COMPLETE")
    print("=" * 60)
    print("Tools tested: block, enforce, quarantine, halt")
    print("All tests passed ✓")
    return True


if __name__ == "__main__":
    self_test()
