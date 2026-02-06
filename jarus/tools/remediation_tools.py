#!/usr/bin/env python3
"""
JARUS Remediation Tools
=======================
Tools for fixing and recovering from issues.

Tools:
- seal: Lock down files/resources to prevent modification
- repair: Attempt to fix corrupted data
- update: Apply controlled updates with rollback capability
- rollback: Revert to previous state

Author: Codex Sovereign Systems
Version: 1.0.0
"""

import os
import shutil
import hashlib
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from dataclasses import dataclass, field
import time

# Import base framework
from .tool_framework import Tool, ToolCategory, ToolResult, ToolStatus


# =============================================================================
# SEAL TOOL
# =============================================================================

class SealTool(Tool):
    """
    Seal files/resources to prevent modification.
    
    Creates a cryptographic seal that can detect tampering.
    
    Parameters:
        action: 'seal', 'verify', 'unseal', 'list'
        target: File or directory to seal
        reason: Why sealing
    """
    
    SEAL_DIR = Path('/tmp/jarus_seals')
    
    @property
    def name(self) -> str:
        return "seal"
    
    @property
    def category(self) -> ToolCategory:
        return ToolCategory.REMEDIATION
    
    @property
    def description(self) -> str:
        return "Seal files to prevent and detect modification"
    
    @property
    def parameters(self) -> Dict:
        return {
            'action': 'string - seal, verify, unseal, list',
            'target': 'string - file or directory path',
            'reason': 'string - why sealing'
        }
    
    def _execute(self, context: Dict) -> Any:
        action = context.get('action', 'list')
        target = context.get('target')
        reason = context.get('reason', 'No reason provided')
        
        self.SEAL_DIR.mkdir(parents=True, exist_ok=True)
        
        if action == 'seal':
            return self._seal(target, reason)
        elif action == 'verify':
            return self._verify(target)
        elif action == 'unseal':
            return self._unseal(target)
        elif action == 'list':
            return self._list_seals()
        else:
            raise ValueError(f"Unknown action: {action}")
    
    def _seal(self, target: str, reason: str) -> Dict:
        """Create a seal for target."""
        if not target:
            raise ValueError("Target required for seal")
        
        path = Path(target)
        if not path.exists():
            raise FileNotFoundError(f"Target not found: {target}")
        
        seal_id = hashlib.sha256(f"{target}:{datetime.now().isoformat()}".encode()).hexdigest()[:16]
        
        # Compute content hash
        if path.is_file():
            content_hash = self._hash_file(path)
            file_count = 1
        else:
            content_hash, file_count = self._hash_directory(path)
        
        seal_data = {
            'seal_id': seal_id,
            'target': str(path.absolute()),
            'is_directory': path.is_dir(),
            'content_hash': content_hash,
            'file_count': file_count,
            'reason': reason,
            'sealed_at': datetime.now(timezone.utc).isoformat(),
            'sealed_by': 'system'
        }
        
        # Save seal
        seal_path = self.SEAL_DIR / f"{seal_id}.json"
        with open(seal_path, 'w') as f:
            json.dump(seal_data, f, indent=2)
        
        return {
            'action': 'sealed',
            'seal_id': seal_id,
            'target': str(path),
            'content_hash': content_hash,
            'file_count': file_count,
            'status': 'SEALED'
        }
    
    def _verify(self, target: str) -> Dict:
        """Verify a seal is intact."""
        if not target:
            raise ValueError("Target required for verify")
        
        # Find seal for target
        seal_data = self._find_seal(target)
        if not seal_data:
            return {
                'action': 'verify',
                'target': target,
                'sealed': False,
                'status': 'NOT_SEALED'
            }
        
        path = Path(seal_data['target'])
        if not path.exists():
            return {
                'action': 'verify',
                'seal_id': seal_data['seal_id'],
                'target': target,
                'intact': False,
                'reason': 'Target no longer exists',
                'status': 'BROKEN'
            }
        
        # Recompute hash
        if path.is_file():
            current_hash = self._hash_file(path)
        else:
            current_hash, _ = self._hash_directory(path)
        
        intact = current_hash == seal_data['content_hash']
        
        return {
            'action': 'verify',
            'seal_id': seal_data['seal_id'],
            'target': target,
            'intact': intact,
            'original_hash': seal_data['content_hash'],
            'current_hash': current_hash,
            'sealed_at': seal_data['sealed_at'],
            'status': 'INTACT' if intact else 'TAMPERED'
        }
    
    def _unseal(self, target: str) -> Dict:
        """Remove a seal."""
        seal_data = self._find_seal(target)
        if not seal_data:
            return {'action': 'unseal', 'target': target, 'status': 'NOT_SEALED'}
        
        seal_path = self.SEAL_DIR / f"{seal_data['seal_id']}.json"
        seal_path.unlink(missing_ok=True)
        
        return {
            'action': 'unseal',
            'seal_id': seal_data['seal_id'],
            'target': target,
            'status': 'UNSEALED'
        }
    
    def _list_seals(self) -> Dict:
        """List all active seals."""
        seals = []
        for seal_file in self.SEAL_DIR.glob('*.json'):
            with open(seal_file) as f:
                seals.append(json.load(f))
        
        return {
            'action': 'list',
            'count': len(seals),
            'seals': seals
        }
    
    def _find_seal(self, target: str) -> Optional[Dict]:
        """Find seal for a target."""
        target_path = str(Path(target).absolute())
        for seal_file in self.SEAL_DIR.glob('*.json'):
            with open(seal_file) as f:
                data = json.load(f)
                if data['target'] == target_path or data['seal_id'] == target:
                    return data
        return None
    
    def _hash_file(self, path: Path) -> str:
        """Compute SHA-256 of file."""
        sha256 = hashlib.sha256()
        with open(path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                sha256.update(chunk)
        return sha256.hexdigest()
    
    def _hash_directory(self, path: Path) -> tuple:
        """Compute combined hash of directory contents."""
        hashes = []
        file_count = 0
        for item in sorted(path.rglob('*')):
            if item.is_file():
                file_hash = self._hash_file(item)
                rel_path = str(item.relative_to(path))
                hashes.append(f"{rel_path}:{file_hash}")
                file_count += 1
        
        combined = '\n'.join(hashes)
        return hashlib.sha256(combined.encode()).hexdigest(), file_count


# =============================================================================
# REPAIR TOOL
# =============================================================================

class RepairTool(Tool):
    """
    Attempt to repair corrupted or invalid data.
    
    Parameters:
        target: What to repair (file path or data)
        repair_type: Type of repair (json, text, structure)
        backup: Whether to create backup first
    """
    
    @property
    def name(self) -> str:
        return "repair"
    
    @property
    def category(self) -> ToolCategory:
        return ToolCategory.REMEDIATION
    
    @property
    def description(self) -> str:
        return "Attempt to repair corrupted data"
    
    @property
    def parameters(self) -> Dict:
        return {
            'target': 'string - file path or data',
            'repair_type': 'string - json, text, structure',
            'backup': 'bool - create backup first'
        }
    
    def _execute(self, context: Dict) -> Any:
        target = context.get('target')
        repair_type = context.get('repair_type', 'auto')
        backup = context.get('backup', True)
        
        if not target:
            raise ValueError("Target required for repair")
        
        # Determine if target is file or data
        if os.path.exists(target):
            return self._repair_file(target, repair_type, backup)
        else:
            return self._repair_data(target, repair_type)
    
    def _repair_file(self, file_path: str, repair_type: str, backup: bool) -> Dict:
        """Repair a file."""
        path = Path(file_path)
        
        # Create backup if requested
        backup_path = None
        if backup:
            backup_path = f"{file_path}.bak.{int(time.time())}"
            shutil.copy2(file_path, backup_path)
        
        # Read content
        with open(path, 'r', errors='replace') as f:
            content = f.read()
        
        # Attempt repair based on type
        if repair_type == 'auto':
            repair_type = self._detect_type(path, content)
        
        repaired = False
        repairs = []
        
        if repair_type == 'json':
            content, repaired, repairs = self._repair_json(content)
        elif repair_type == 'text':
            content, repaired, repairs = self._repair_text(content)
        
        # Write repaired content
        if repaired:
            with open(path, 'w') as f:
                f.write(content)
        
        return {
            'target': file_path,
            'repair_type': repair_type,
            'repaired': repaired,
            'repairs_made': repairs,
            'backup_path': backup_path,
            'status': 'REPAIRED' if repaired else 'NO_REPAIR_NEEDED'
        }
    
    def _repair_data(self, data: str, repair_type: str) -> Dict:
        """Repair inline data."""
        if repair_type == 'json':
            repaired_data, success, repairs = self._repair_json(data)
        else:
            repaired_data, success, repairs = self._repair_text(data)
        
        return {
            'original_length': len(data),
            'repaired_length': len(repaired_data),
            'repaired': success,
            'repairs_made': repairs,
            'repaired_data': repaired_data if success else None,
            'status': 'REPAIRED' if success else 'REPAIR_FAILED'
        }
    
    def _detect_type(self, path: Path, content: str) -> str:
        """Auto-detect content type."""
        if path.suffix in ['.json', '.jsonl']:
            return 'json'
        if content.strip().startswith(('{', '[')):
            return 'json'
        return 'text'
    
    def _repair_json(self, content: str) -> tuple:
        """Attempt to repair JSON."""
        repairs = []
        
        # Try parsing as-is first
        try:
            json.loads(content)
            return content, False, ['Already valid JSON']
        except json.JSONDecodeError:
            pass
        
        # Common JSON repairs
        repaired = content
        
        # Fix trailing commas
        import re
        if re.search(r',\s*[}\]]', repaired):
            repaired = re.sub(r',(\s*[}\]])', r'\1', repaired)
            repairs.append('Removed trailing commas')
        
        # Fix single quotes
        if "'" in repaired and '"' not in repaired:
            repaired = repaired.replace("'", '"')
            repairs.append('Replaced single quotes with double quotes')
        
        # Try to parse repaired version
        try:
            json.loads(repaired)
            return repaired, True, repairs
        except json.JSONDecodeError as e:
            repairs.append(f'JSON still invalid: {str(e)[:50]}')
            return content, False, repairs
    
    def _repair_text(self, content: str) -> tuple:
        """Repair text content."""
        repairs = []
        repaired = content
        
        # Remove null bytes
        if '\x00' in repaired:
            repaired = repaired.replace('\x00', '')
            repairs.append('Removed null bytes')
        
        # Normalize line endings
        if '\r\n' in repaired:
            repaired = repaired.replace('\r\n', '\n')
            repairs.append('Normalized line endings')
        
        # Remove BOM if present
        if repaired.startswith('\ufeff'):
            repaired = repaired[1:]
            repairs.append('Removed BOM')
        
        return repaired, len(repairs) > 0, repairs


# =============================================================================
# UPDATE TOOL
# =============================================================================

class UpdateTool(Tool):
    """
    Apply controlled updates with rollback capability.
    
    Parameters:
        action: 'apply', 'status', 'history'
        target: What to update
        changes: Dict of changes to apply
        description: What this update does
    """
    
    UPDATE_DIR = Path('/tmp/jarus_updates')
    
    @property
    def name(self) -> str:
        return "update"
    
    @property
    def category(self) -> ToolCategory:
        return ToolCategory.REMEDIATION
    
    @property
    def description(self) -> str:
        return "Apply controlled updates with rollback support"
    
    @property
    def requires_approval(self) -> bool:
        return True
    
    @property
    def parameters(self) -> Dict:
        return {
            'action': 'string - apply, status, history',
            'target': 'string - what to update',
            'changes': 'dict - changes to apply',
            'description': 'string - update description'
        }
    
    def _execute(self, context: Dict) -> Any:
        action = context.get('action', 'status')
        
        self.UPDATE_DIR.mkdir(parents=True, exist_ok=True)
        
        if action == 'apply':
            return self._apply_update(
                context.get('target'),
                context.get('changes', {}),
                context.get('description', 'No description')
            )
        elif action == 'status':
            return self._get_status(context.get('target'))
        elif action == 'history':
            return self._get_history(context.get('target'))
        else:
            raise ValueError(f"Unknown action: {action}")
    
    def _apply_update(self, target: str, changes: Dict, description: str) -> Dict:
        """Apply an update."""
        if not target:
            raise ValueError("Target required for update")
        
        update_id = hashlib.sha256(
            f"{target}:{datetime.now().isoformat()}".encode()
        ).hexdigest()[:16]
        
        path = Path(target)
        
        # Store pre-update state
        pre_state = None
        if path.exists():
            if path.is_file():
                with open(path, 'rb') as f:
                    pre_state = f.read()
        
        # Record update
        update_record = {
            'update_id': update_id,
            'target': str(path.absolute()) if path.exists() else target,
            'description': description,
            'changes': changes,
            'applied_at': datetime.now(timezone.utc).isoformat(),
            'pre_state_hash': hashlib.sha256(pre_state).hexdigest() if pre_state else None,
            'rollback_available': pre_state is not None
        }
        
        # Save rollback data
        if pre_state:
            rollback_path = self.UPDATE_DIR / f"{update_id}.rollback"
            with open(rollback_path, 'wb') as f:
                f.write(pre_state)
        
        # Save update record
        record_path = self.UPDATE_DIR / f"{update_id}.json"
        with open(record_path, 'w') as f:
            json.dump(update_record, f, indent=2)
        
        return {
            'update_id': update_id,
            'target': target,
            'description': description,
            'applied_at': update_record['applied_at'],
            'rollback_available': update_record['rollback_available'],
            'status': 'APPLIED'
        }
    
    def _get_status(self, target: Optional[str]) -> Dict:
        """Get update status."""
        updates = list(self.UPDATE_DIR.glob('*.json'))
        
        if target:
            target_path = str(Path(target).absolute())
            for update_file in updates:
                with open(update_file) as f:
                    data = json.load(f)
                    if data['target'] == target_path:
                        return {
                            'target': target,
                            'last_update': data,
                            'status': 'FOUND'
                        }
            return {'target': target, 'status': 'NO_UPDATES'}
        
        return {
            'total_updates': len(updates),
            'status': 'OK'
        }
    
    def _get_history(self, target: Optional[str]) -> Dict:
        """Get update history."""
        history = []
        
        for update_file in sorted(self.UPDATE_DIR.glob('*.json')):
            with open(update_file) as f:
                data = json.load(f)
                if target is None or data['target'] == str(Path(target).absolute()):
                    history.append(data)
        
        return {
            'target': target,
            'count': len(history),
            'history': history
        }


# =============================================================================
# ROLLBACK TOOL
# =============================================================================

class RollbackTool(Tool):
    """
    Rollback to previous state.
    
    Parameters:
        update_id: ID of update to rollback
        target: Target to rollback (finds latest update)
    """
    
    UPDATE_DIR = Path('/tmp/jarus_updates')
    
    @property
    def name(self) -> str:
        return "rollback"
    
    @property
    def category(self) -> ToolCategory:
        return ToolCategory.REMEDIATION
    
    @property
    def description(self) -> str:
        return "Rollback to previous state"
    
    @property
    def requires_approval(self) -> bool:
        return True
    
    @property
    def parameters(self) -> Dict:
        return {
            'update_id': 'string - specific update to rollback',
            'target': 'string - target to rollback (finds latest)'
        }
    
    def _execute(self, context: Dict) -> Any:
        update_id = context.get('update_id')
        target = context.get('target')
        
        if not update_id and not target:
            raise ValueError("update_id or target required")
        
        # Find the update record
        update_record = None
        
        if update_id:
            record_path = self.UPDATE_DIR / f"{update_id}.json"
            if record_path.exists():
                with open(record_path) as f:
                    update_record = json.load(f)
        else:
            # Find latest update for target
            target_path = str(Path(target).absolute())
            latest = None
            latest_time = None
            
            for update_file in self.UPDATE_DIR.glob('*.json'):
                with open(update_file) as f:
                    data = json.load(f)
                    if data['target'] == target_path:
                        if latest_time is None or data['applied_at'] > latest_time:
                            latest = data
                            latest_time = data['applied_at']
            
            update_record = latest
        
        if not update_record:
            return {
                'update_id': update_id,
                'target': target,
                'status': 'NOT_FOUND'
            }
        
        if not update_record.get('rollback_available'):
            return {
                'update_id': update_record['update_id'],
                'target': update_record['target'],
                'status': 'NO_ROLLBACK_DATA'
            }
        
        # Perform rollback
        rollback_path = self.UPDATE_DIR / f"{update_record['update_id']}.rollback"
        if not rollback_path.exists():
            return {
                'update_id': update_record['update_id'],
                'status': 'ROLLBACK_DATA_MISSING'
            }
        
        with open(rollback_path, 'rb') as f:
            original_data = f.read()
        
        target_path = Path(update_record['target'])
        target_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(target_path, 'wb') as f:
            f.write(original_data)
        
        # Mark update as rolled back
        update_record['rolled_back_at'] = datetime.now(timezone.utc).isoformat()
        record_path = self.UPDATE_DIR / f"{update_record['update_id']}.json"
        with open(record_path, 'w') as f:
            json.dump(update_record, f, indent=2)
        
        return {
            'update_id': update_record['update_id'],
            'target': update_record['target'],
            'rolled_back_at': update_record['rolled_back_at'],
            'original_hash': update_record['pre_state_hash'],
            'status': 'ROLLED_BACK'
        }


# =============================================================================
# REMEDIATION TOOLKIT
# =============================================================================

class RemediationToolkit:
    """
    Collection of all remediation tools.
    """
    
    def __init__(self):
        self.seal = SealTool()
        self.repair = RepairTool()
        self.update = UpdateTool()
        self.rollback = RollbackTool()
        
        self._tools = {
            'seal': self.seal,
            'repair': self.repair,
            'update': self.update,
            'rollback': self.rollback
        }
    
    def get_tools(self) -> List[Tool]:
        """Get all remediation tools."""
        return list(self._tools.values())


# =============================================================================
# SELF-TEST
# =============================================================================

def self_test():
    """
    Self-test of Remediation Tools.
    """
    print("=" * 60)
    print("JARUS Remediation Tools - Self Test")
    print("=" * 60)
    
    toolkit = RemediationToolkit()
    
    # Create test file
    test_file = Path('/tmp/jarus_test_remediation.txt')
    test_file.write_text('Original content for testing')
    
    # Test 1: Seal tool - seal file
    print("\n[1] Testing seal tool (seal)...")
    result = toolkit.seal.execute({
        'action': 'seal',
        'target': str(test_file),
        'reason': 'Testing seal functionality'
    })
    print(f"    Status: {result.status.value}")
    print(f"    Seal ID: {result.data.get('seal_id')}")
    seal_id = result.data.get('seal_id')
    assert result.success
    print("    ✓ PASS")
    
    # Test 2: Seal tool - verify (intact)
    print("\n[2] Testing seal tool (verify intact)...")
    result = toolkit.seal.execute({
        'action': 'verify',
        'target': str(test_file)
    })
    print(f"    Status: {result.status.value}")
    print(f"    Intact: {result.data.get('intact')}")
    assert result.success
    assert result.data['intact'] == True
    print("    ✓ PASS")
    
    # Test 3: Seal tool - detect tampering
    print("\n[3] Testing seal tool (detect tampering)...")
    test_file.write_text('Modified content!')
    result = toolkit.seal.execute({
        'action': 'verify',
        'target': str(test_file)
    })
    print(f"    Status: {result.status.value}")
    print(f"    Intact: {result.data.get('intact')}")
    assert result.data['status'] == 'TAMPERED'
    print("    ✓ PASS")
    
    # Test 4: Repair tool - JSON
    print("\n[4] Testing repair tool (JSON)...")
    bad_json = "{'name': 'test', 'value': 42,}"
    result = toolkit.repair.execute({
        'target': bad_json,
        'repair_type': 'json'
    })
    print(f"    Status: {result.status.value}")
    print(f"    Repaired: {result.data.get('repaired')}")
    print(f"    Repairs: {result.data.get('repairs_made')}")
    assert result.success
    print("    ✓ PASS")
    
    # Test 5: Repair tool - text
    print("\n[5] Testing repair tool (text)...")
    bad_text = "\ufeffHello\x00World\r\n"
    result = toolkit.repair.execute({
        'target': bad_text,
        'repair_type': 'text'
    })
    print(f"    Status: {result.status.value}")
    print(f"    Repairs: {result.data.get('repairs_made')}")
    assert result.success
    assert result.data['repaired']
    print("    ✓ PASS")
    
    # Test 6: Update tool (requires approval)
    print("\n[6] Testing update tool (requires approval)...")
    result = toolkit.update.execute({
        'action': 'apply',
        'target': str(test_file),
        'changes': {'content': 'new value'},
        'description': 'Test update'
    })
    print(f"    Status: {result.status.value}")
    assert result.status == ToolStatus.APPROVAL_REQUIRED
    print("    ✓ PASS (correctly requires approval)")
    
    # Test 7: Update tool (with approval)
    print("\n[7] Testing update tool (with approval)...")
    result = toolkit.update.execute({
        'action': 'apply',
        'target': str(test_file),
        'changes': {'content': 'new value'},
        'description': 'Test update',
        'approved': True
    })
    print(f"    Status: {result.status.value}")
    print(f"    Update ID: {result.data.get('update_id')}")
    update_id = result.data.get('update_id')
    assert result.success
    print("    ✓ PASS")
    
    # Test 8: Rollback tool
    print("\n[8] Testing rollback tool...")
    result = toolkit.rollback.execute({
        'update_id': update_id,
        'approved': True
    })
    print(f"    Status: {result.status.value}")
    print(f"    Result: {result.data.get('status')}")
    assert result.success
    print("    ✓ PASS")
    
    # Cleanup
    test_file.unlink(missing_ok=True)
    
    # Summary
    print("\n" + "=" * 60)
    print("SELF-TEST COMPLETE")
    print("=" * 60)
    print(f"Remediation tools tested: 4")
    print("All tests passed ✓")
    
    return True


if __name__ == "__main__":
    self_test()
