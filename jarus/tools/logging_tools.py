#!/usr/bin/env python3
"""
JARUS Logging Tools
===================
Structured logging with cryptographic verification.

Tools:
- log: Write structured log entries
- append: Append to existing log streams
- record: Record events with context
- audit: Generate audit reports

Author: Codex Sovereign Systems
Version: 1.0.0
"""

import hashlib
import json
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from dataclasses import dataclass, field
from enum import Enum
import threading

# Import base framework
from .tool_framework import Tool, ToolCategory, ToolResult, ToolStatus


# =============================================================================
# ENUMS
# =============================================================================

class LogLevel(Enum):
    """Log severity levels."""
    DEBUG = 10
    INFO = 20
    WARNING = 30
    ERROR = 40
    CRITICAL = 50


class EventType(Enum):
    """Types of recordable events."""
    ACTION = "ACTION"
    DECISION = "DECISION"
    ERROR = "ERROR"
    SECURITY = "SECURITY"
    COMPLIANCE = "COMPLIANCE"
    SYSTEM = "SYSTEM"
    USER = "USER"


# =============================================================================
# LOG TOOL
# =============================================================================

class LogTool(Tool):
    """
    Write structured log entries.
    
    Logs are:
    - Timestamped (UTC)
    - Hash-chained for integrity
    - Stored in JSONL format
    
    Parameters:
        message: Log message
        level: DEBUG, INFO, WARNING, ERROR, CRITICAL
        context: Additional structured data
        stream: Log stream name (default: 'main')
    """
    
    LOG_DIR = Path('/tmp/jarus_logs')
    _lock = threading.RLock()
    _chains: Dict[str, str] = {}  # stream -> last hash
    
    @property
    def name(self) -> str:
        return "log"
    
    @property
    def category(self) -> ToolCategory:
        return ToolCategory.LOGGING
    
    @property
    def description(self) -> str:
        return "Write structured, hash-chained log entries"
    
    @property
    def parameters(self) -> Dict:
        return {
            'message': 'string - log message',
            'level': 'string - DEBUG/INFO/WARNING/ERROR/CRITICAL',
            'context': 'dict - additional data',
            'stream': 'string - log stream name'
        }
    
    def _execute(self, context: Dict) -> Any:
        message = context.get('message', '')
        level_str = context.get('level', 'INFO').upper()
        extra_context = context.get('context', {})
        stream = context.get('stream', 'main')
        
        try:
            level = LogLevel[level_str]
        except KeyError:
            level = LogLevel.INFO
        
        self.LOG_DIR.mkdir(parents=True, exist_ok=True)
        
        with self._lock:
            # Get previous hash for chain
            prev_hash = self._chains.get(stream, '0' * 64)
            
            timestamp = datetime.now(timezone.utc).isoformat()
            
            entry = {
                'timestamp': timestamp,
                'level': level.name,
                'level_value': level.value,
                'message': message,
                'context': extra_context,
                'stream': stream,
                'prev_hash': prev_hash
            }
            
            # Compute entry hash
            entry_content = json.dumps(entry, sort_keys=True)
            entry_hash = hashlib.sha256(entry_content.encode()).hexdigest()
            entry['hash'] = entry_hash
            
            # Update chain
            self._chains[stream] = entry_hash
            
            # Write to file
            log_path = self.LOG_DIR / f"{stream}.jsonl"
            with open(log_path, 'a') as f:
                f.write(json.dumps(entry) + '\n')
        
        return {
            'logged': True,
            'timestamp': timestamp,
            'level': level.name,
            'stream': stream,
            'hash': entry_hash,
            'message_preview': message[:50] + '...' if len(message) > 50 else message
        }


# =============================================================================
# APPEND TOOL
# =============================================================================

class AppendTool(Tool):
    """
    Append data to existing log streams.
    
    For bulk logging or continuation of log entries.
    
    Parameters:
        stream: Log stream name
        entries: List of entries to append
        validate: Whether to validate chain integrity
    """
    
    LOG_DIR = Path('/tmp/jarus_logs')
    _lock = threading.RLock()
    
    @property
    def name(self) -> str:
        return "append"
    
    @property
    def category(self) -> ToolCategory:
        return ToolCategory.LOGGING
    
    @property
    def description(self) -> str:
        return "Append multiple entries to log stream"
    
    @property
    def parameters(self) -> Dict:
        return {
            'stream': 'string - log stream name',
            'entries': 'list - entries to append',
            'validate': 'bool - validate chain first'
        }
    
    def _execute(self, context: Dict) -> Any:
        stream = context.get('stream', 'main')
        entries = context.get('entries', [])
        validate = context.get('validate', True)
        
        if not entries:
            return {'appended': 0, 'stream': stream, 'status': 'NO_ENTRIES'}
        
        self.LOG_DIR.mkdir(parents=True, exist_ok=True)
        log_path = self.LOG_DIR / f"{stream}.jsonl"
        
        with self._lock:
            # Get current chain state
            prev_hash = '0' * 64
            if log_path.exists() and validate:
                with open(log_path, 'r') as f:
                    for line in f:
                        if line.strip():
                            entry = json.loads(line)
                            prev_hash = entry.get('hash', prev_hash)
            
            appended = 0
            hashes = []
            
            with open(log_path, 'a') as f:
                for entry_data in entries:
                    timestamp = datetime.now(timezone.utc).isoformat()
                    
                    entry = {
                        'timestamp': timestamp,
                        'level': entry_data.get('level', 'INFO'),
                        'message': entry_data.get('message', ''),
                        'context': entry_data.get('context', {}),
                        'stream': stream,
                        'prev_hash': prev_hash
                    }
                    
                    entry_content = json.dumps(entry, sort_keys=True)
                    entry_hash = hashlib.sha256(entry_content.encode()).hexdigest()
                    entry['hash'] = entry_hash
                    
                    f.write(json.dumps(entry) + '\n')
                    
                    prev_hash = entry_hash
                    hashes.append(entry_hash)
                    appended += 1
        
        return {
            'appended': appended,
            'stream': stream,
            'first_hash': hashes[0] if hashes else None,
            'last_hash': hashes[-1] if hashes else None,
            'status': 'APPENDED'
        }


# =============================================================================
# RECORD TOOL
# =============================================================================

class RecordTool(Tool):
    """
    Record events with full context.
    
    Higher-level than log - for significant events.
    
    Parameters:
        event_type: ACTION, DECISION, ERROR, SECURITY, COMPLIANCE, SYSTEM, USER
        event_name: Name of the event
        actor: Who/what triggered the event
        details: Event details
        outcome: Result of the event
    """
    
    RECORD_DIR = Path('/tmp/jarus_records')
    _lock = threading.RLock()
    _chain_hash: str = '0' * 64
    
    @property
    def name(self) -> str:
        return "record"
    
    @property
    def category(self) -> ToolCategory:
        return ToolCategory.LOGGING
    
    @property
    def description(self) -> str:
        return "Record significant events with full context"
    
    @property
    def parameters(self) -> Dict:
        return {
            'event_type': 'string - ACTION/DECISION/ERROR/SECURITY/COMPLIANCE/SYSTEM/USER',
            'event_name': 'string - name of event',
            'actor': 'string - who triggered event',
            'details': 'dict - event details',
            'outcome': 'string - result of event'
        }
    
    def _execute(self, context: Dict) -> Any:
        event_type_str = context.get('event_type', 'SYSTEM').upper()
        event_name = context.get('event_name', 'unnamed_event')
        actor = context.get('actor', 'system')
        details = context.get('details', {})
        outcome = context.get('outcome', 'unknown')
        
        try:
            event_type = EventType[event_type_str]
        except KeyError:
            event_type = EventType.SYSTEM
        
        self.RECORD_DIR.mkdir(parents=True, exist_ok=True)
        
        with self._lock:
            record_id = hashlib.sha256(
                f"{event_name}:{datetime.now().isoformat()}".encode()
            ).hexdigest()[:16]
            
            timestamp = datetime.now(timezone.utc).isoformat()
            
            record = {
                'record_id': record_id,
                'timestamp': timestamp,
                'event_type': event_type.value,
                'event_name': event_name,
                'actor': actor,
                'details': details,
                'outcome': outcome,
                'prev_hash': self._chain_hash
            }
            
            record_content = json.dumps(record, sort_keys=True)
            record_hash = hashlib.sha256(record_content.encode()).hexdigest()
            record['hash'] = record_hash
            
            RecordTool._chain_hash = record_hash
            
            # Write to records file
            record_path = self.RECORD_DIR / 'events.jsonl'
            with open(record_path, 'a') as f:
                f.write(json.dumps(record) + '\n')
        
        return {
            'record_id': record_id,
            'timestamp': timestamp,
            'event_type': event_type.value,
            'event_name': event_name,
            'actor': actor,
            'outcome': outcome,
            'hash': record_hash,
            'status': 'RECORDED'
        }


# =============================================================================
# AUDIT TOOL
# =============================================================================

class AuditTool(Tool):
    """
    Generate audit reports from logs and records.
    
    Parameters:
        action: 'report', 'verify', 'search', 'stats'
        stream: Log stream to audit
        start_time: Filter start (ISO timestamp)
        end_time: Filter end (ISO timestamp)
        filters: Additional filters
    """
    
    LOG_DIR = Path('/tmp/jarus_logs')
    RECORD_DIR = Path('/tmp/jarus_records')
    
    @property
    def name(self) -> str:
        return "audit"
    
    @property
    def category(self) -> ToolCategory:
        return ToolCategory.LOGGING
    
    @property
    def description(self) -> str:
        return "Generate audit reports and verify log integrity"
    
    @property
    def parameters(self) -> Dict:
        return {
            'action': 'string - report, verify, search, stats',
            'stream': 'string - log stream name',
            'start_time': 'string - filter start (ISO)',
            'end_time': 'string - filter end (ISO)',
            'filters': 'dict - additional filters'
        }
    
    def _execute(self, context: Dict) -> Any:
        action = context.get('action', 'stats')
        stream = context.get('stream', 'main')
        start_time = context.get('start_time')
        end_time = context.get('end_time')
        filters = context.get('filters', {})
        
        if action == 'verify':
            return self._verify_chain(stream)
        elif action == 'report':
            return self._generate_report(stream, start_time, end_time, filters)
        elif action == 'search':
            return self._search(stream, filters)
        elif action == 'stats':
            return self._get_stats(stream)
        else:
            raise ValueError(f"Unknown action: {action}")
    
    def _verify_chain(self, stream: str) -> Dict:
        """Verify hash chain integrity."""
        log_path = self.LOG_DIR / f"{stream}.jsonl"
        
        if not log_path.exists():
            return {'stream': stream, 'exists': False, 'status': 'NOT_FOUND'}
        
        prev_hash = '0' * 64
        entries_checked = 0
        broken_at = None
        
        with open(log_path, 'r') as f:
            for line_num, line in enumerate(f, 1):
                if not line.strip():
                    continue
                
                entry = json.loads(line)
                
                # Check chain link
                if entry.get('prev_hash') != prev_hash:
                    broken_at = line_num
                    break
                
                # Verify entry hash
                entry_hash = entry.pop('hash', None)
                entry_content = json.dumps(entry, sort_keys=True)
                computed_hash = hashlib.sha256(entry_content.encode()).hexdigest()
                
                if entry_hash != computed_hash:
                    broken_at = line_num
                    break
                
                prev_hash = entry_hash
                entries_checked += 1
        
        return {
            'stream': stream,
            'entries_checked': entries_checked,
            'chain_intact': broken_at is None,
            'broken_at_line': broken_at,
            'last_hash': prev_hash,
            'status': 'INTACT' if broken_at is None else 'BROKEN'
        }
    
    def _generate_report(self, stream: str, start_time: Optional[str],
                        end_time: Optional[str], filters: Dict) -> Dict:
        """Generate audit report."""
        log_path = self.LOG_DIR / f"{stream}.jsonl"
        
        if not log_path.exists():
            return {'stream': stream, 'status': 'NOT_FOUND'}
        
        entries = []
        level_counts = {}
        
        with open(log_path, 'r') as f:
            for line in f:
                if not line.strip():
                    continue
                
                entry = json.loads(line)
                
                # Time filters
                if start_time and entry['timestamp'] < start_time:
                    continue
                if end_time and entry['timestamp'] > end_time:
                    continue
                
                # Level filter
                if 'level' in filters:
                    if entry.get('level') != filters['level']:
                        continue
                
                entries.append(entry)
                level = entry.get('level', 'UNKNOWN')
                level_counts[level] = level_counts.get(level, 0) + 1
        
        return {
            'stream': stream,
            'total_entries': len(entries),
            'time_range': {
                'start': entries[0]['timestamp'] if entries else None,
                'end': entries[-1]['timestamp'] if entries else None
            },
            'level_breakdown': level_counts,
            'entries': entries[-100:],  # Last 100 entries
            'status': 'GENERATED'
        }
    
    def _search(self, stream: str, filters: Dict) -> Dict:
        """Search logs."""
        log_path = self.LOG_DIR / f"{stream}.jsonl"
        
        if not log_path.exists():
            return {'stream': stream, 'status': 'NOT_FOUND'}
        
        query = filters.get('query', '').lower()
        level = filters.get('level')
        limit = filters.get('limit', 50)
        
        matches = []
        
        with open(log_path, 'r') as f:
            for line in f:
                if not line.strip():
                    continue
                
                entry = json.loads(line)
                
                if level and entry.get('level') != level:
                    continue
                
                if query:
                    message = entry.get('message', '').lower()
                    if query not in message:
                        continue
                
                matches.append(entry)
                
                if len(matches) >= limit:
                    break
        
        return {
            'stream': stream,
            'query': query,
            'matches': len(matches),
            'results': matches,
            'status': 'FOUND' if matches else 'NO_MATCHES'
        }
    
    def _get_stats(self, stream: str) -> Dict:
        """Get log statistics."""
        log_path = self.LOG_DIR / f"{stream}.jsonl"
        
        if not log_path.exists():
            return {'stream': stream, 'exists': False, 'status': 'NOT_FOUND'}
        
        total = 0
        level_counts = {}
        first_ts = None
        last_ts = None
        
        with open(log_path, 'r') as f:
            for line in f:
                if not line.strip():
                    continue
                
                entry = json.loads(line)
                total += 1
                
                level = entry.get('level', 'UNKNOWN')
                level_counts[level] = level_counts.get(level, 0) + 1
                
                ts = entry.get('timestamp')
                if first_ts is None:
                    first_ts = ts
                last_ts = ts
        
        file_size = log_path.stat().st_size
        
        return {
            'stream': stream,
            'total_entries': total,
            'file_size_bytes': file_size,
            'level_breakdown': level_counts,
            'time_range': {
                'first': first_ts,
                'last': last_ts
            },
            'status': 'OK'
        }


# =============================================================================
# LOGGING TOOLKIT
# =============================================================================

class LoggingToolkit:
    """
    Collection of all logging tools.
    """
    
    def __init__(self):
        self.log = LogTool()
        self.append = AppendTool()
        self.record = RecordTool()
        self.audit = AuditTool()
        
        self._tools = {
            'log': self.log,
            'append': self.append,
            'record': self.record,
            'audit': self.audit
        }
    
    def get_tools(self) -> List[Tool]:
        """Get all logging tools."""
        return list(self._tools.values())
    
    def execute(self, tool_name: str, context: Dict) -> ToolResult:
        """Execute a logging tool by name."""
        if tool_name not in self._tools:
            return ToolResult(
                tool_name=tool_name,
                status=ToolStatus.FAILURE,
                data=None,
                evidence_hash='',
                execution_time_ms=0,
                error=f"Unknown logging tool: {tool_name}"
            )
        return self._tools[tool_name].execute(context)


# =============================================================================
# SELF-TEST
# =============================================================================

def self_test():
    """
    Self-test of Logging Tools.
    """
    print("=" * 60)
    print("JARUS Logging Tools - Self Test")
    print("=" * 60)
    
    # Clean up from previous runs
    import shutil
    shutil.rmtree('/tmp/jarus_logs', ignore_errors=True)
    shutil.rmtree('/tmp/jarus_records', ignore_errors=True)
    
    # Reset class-level state
    LogTool._chains = {}
    RecordTool._chain_hash = '0' * 64
    
    toolkit = LoggingToolkit()
    
    # Test 1: Log tool
    print("\n[1] Testing log tool...")
    result = toolkit.log.execute({
        'message': 'System started successfully',
        'level': 'INFO',
        'context': {'version': '1.0.0', 'node': 'primary'},
        'stream': 'test_stream'
    })
    print(f"    Status: {result.status.value}")
    print(f"    Hash: {result.data.get('hash', '')[:32]}...")
    assert result.success
    print("    ✓ PASS")
    
    # Test 2: Log multiple levels
    print("\n[2] Testing log levels...")
    for level in ['DEBUG', 'WARNING', 'ERROR']:
        result = toolkit.log.execute({
            'message': f'Test message at {level} level',
            'level': level,
            'stream': 'test_stream'
        })
        assert result.success
    print("    Logged: DEBUG, WARNING, ERROR")
    print("    ✓ PASS")
    
    # Test 3: Append tool
    print("\n[3] Testing append tool...")
    entries = [
        {'message': 'Batch entry 1', 'level': 'INFO'},
        {'message': 'Batch entry 2', 'level': 'INFO'},
        {'message': 'Batch entry 3', 'level': 'WARNING'}
    ]
    result = toolkit.append.execute({
        'stream': 'test_stream',
        'entries': entries
    })
    print(f"    Status: {result.status.value}")
    print(f"    Appended: {result.data.get('appended')}")
    assert result.success
    assert result.data['appended'] == 3
    print("    ✓ PASS")
    
    # Test 4: Record tool
    print("\n[4] Testing record tool...")
    result = toolkit.record.execute({
        'event_type': 'SECURITY',
        'event_name': 'user_login',
        'actor': 'admin@example.com',
        'details': {'ip': '192.168.1.1', 'method': 'password'},
        'outcome': 'success'
    })
    print(f"    Status: {result.status.value}")
    print(f"    Record ID: {result.data.get('record_id')}")
    assert result.success
    print("    ✓ PASS")
    
    # Test 5: Audit - stats
    print("\n[5] Testing audit tool (stats)...")
    result = toolkit.audit.execute({
        'action': 'stats',
        'stream': 'test_stream'
    })
    print(f"    Status: {result.status.value}")
    print(f"    Total entries: {result.data.get('total_entries')}")
    print(f"    Level breakdown: {result.data.get('level_breakdown')}")
    assert result.success
    print("    ✓ PASS")
    
    # Test 6: Audit - verify chain
    print("\n[6] Testing audit tool (verify chain)...")
    result = toolkit.audit.execute({
        'action': 'verify',
        'stream': 'test_stream'
    })
    print(f"    Status: {result.data.get('status')}")
    print(f"    Chain intact: {result.data.get('chain_intact')}")
    print(f"    Entries checked: {result.data.get('entries_checked')}")
    assert result.success
    assert result.data['chain_intact'] == True
    print("    ✓ PASS")
    
    # Test 7: Audit - search
    print("\n[7] Testing audit tool (search)...")
    result = toolkit.audit.execute({
        'action': 'search',
        'stream': 'test_stream',
        'filters': {'query': 'batch', 'limit': 10}
    })
    print(f"    Status: {result.data.get('status')}")
    print(f"    Matches: {result.data.get('matches')}")
    assert result.success
    print("    ✓ PASS")
    
    # Test 8: Audit - report
    print("\n[8] Testing audit tool (report)...")
    result = toolkit.audit.execute({
        'action': 'report',
        'stream': 'test_stream'
    })
    print(f"    Status: {result.data.get('status')}")
    print(f"    Total entries: {result.data.get('total_entries')}")
    assert result.success
    print("    ✓ PASS")
    
    # Summary
    print("\n" + "=" * 60)
    print("SELF-TEST COMPLETE")
    print("=" * 60)
    print(f"Logging tools tested: 4")
    print("All tests passed ✓")
    
    return True


if __name__ == "__main__":
    self_test()
