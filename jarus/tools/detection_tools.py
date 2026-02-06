#!/usr/bin/env python3
"""
JARUS Detection Tools
=====================
Tools for finding and identifying patterns, files, and entities.

Tools:
- scan: Filesystem scanning with patterns
- classify: Content classification
- detect: Anomaly detection
- recognize: Entity recognition

Author: Codex Sovereign Systems
Version: 1.0.0
"""

import re
import os
import hashlib
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime, timezone
import statistics

from .tool_base import Tool, ToolSpec, ToolCategory


# =============================================================================
# SCAN TOOL
# =============================================================================

class ScanTool(Tool):
    """
    Scan filesystem for files matching patterns.
    
    Usage:
        tool = ScanTool()
        result = tool.execute({
            'path': '/data',
            'pattern': '*.log',
            'recursive': True
        })
    """
    
    @property
    def spec(self) -> ToolSpec:
        return ToolSpec(
            name="scan",
            category=ToolCategory.DETECTION,
            description="Scan filesystem for files matching patterns",
            parameters={
                'path': {'type': 'str', 'required': True, 'description': 'Directory to scan'},
                'pattern': {'type': 'str', 'required': False, 'description': 'Glob pattern (default: *)'},
                'recursive': {'type': 'bool', 'required': False, 'description': 'Recursive scan'},
                'max_files': {'type': 'int', 'required': False, 'description': 'Max files to return'}
            }
        )
    
    def _execute(self, params: Dict) -> Dict:
        path = Path(params['path'])
        pattern = params.get('pattern', '*')
        recursive = params.get('recursive', False)
        max_files = params.get('max_files', 1000)
        
        if not path.exists():
            return {
                'found': False,
                'error': f"Path does not exist: {path}",
                'files': []
            }
        
        files = []
        glob_method = path.rglob if recursive else path.glob
        
        for f in glob_method(pattern):
            if len(files) >= max_files:
                break
            if f.is_file():
                try:
                    stat = f.stat()
                    files.append({
                        'path': str(f),
                        'name': f.name,
                        'size': stat.st_size,
                        'modified': datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat()
                    })
                except (PermissionError, OSError):
                    continue
        
        return {
            'found': True,
            'base_path': str(path),
            'pattern': pattern,
            'recursive': recursive,
            'file_count': len(files),
            'files': files
        }


# =============================================================================
# CLASSIFY TOOL
# =============================================================================

class ClassifyTool(Tool):
    """
    Classify content by type and sensitivity.
    
    Detects:
    - File types
    - Sensitive data (credentials, PII)
    - Content categories
    """
    
    # Patterns for sensitive data
    SENSITIVE_PATTERNS = {
        'api_key': r'(?i)(api[_-]?key|apikey)["\s:=]+["\']?([a-zA-Z0-9_-]{20,})["\']?',
        'password': r'(?i)(password|passwd|pwd)["\s:=]+["\']?([^\s"\']{8,})["\']?',
        'email': r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
        'phone': r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
        'ssn': r'\b\d{3}-\d{2}-\d{4}\b',
        'credit_card': r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',
        'private_key': r'-----BEGIN (RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----',
        'aws_key': r'AKIA[0-9A-Z]{16}',
        'jwt': r'eyJ[a-zA-Z0-9_-]+\.eyJ[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+'
    }
    
    # File type signatures (magic bytes)
    FILE_SIGNATURES = {
        b'\x89PNG': 'image/png',
        b'\xff\xd8\xff': 'image/jpeg',
        b'GIF8': 'image/gif',
        b'%PDF': 'application/pdf',
        b'PK\x03\x04': 'application/zip',
        b'\x1f\x8b': 'application/gzip',
        b'{\n': 'application/json',
        b'[': 'application/json',
        b'<!DOCTYPE': 'text/html',
        b'<html': 'text/html',
        b'<?xml': 'application/xml'
    }
    
    @property
    def spec(self) -> ToolSpec:
        return ToolSpec(
            name="classify",
            category=ToolCategory.DETECTION,
            description="Classify content by type and detect sensitive data",
            parameters={
                'content': {'type': 'str', 'required': False, 'description': 'Text content to classify'},
                'file_path': {'type': 'str', 'required': False, 'description': 'File to classify'},
                'check_sensitive': {'type': 'bool', 'required': False, 'description': 'Check for sensitive data'}
            }
        )
    
    def _execute(self, params: Dict) -> Dict:
        content = params.get('content', '')
        file_path = params.get('file_path')
        check_sensitive = params.get('check_sensitive', True)
        
        result = {
            'file_type': 'text/plain',
            'encoding': 'utf-8',
            'size_bytes': 0,
            'sensitive_data': [],
            'sensitivity_level': 'LOW'
        }
        
        # Read from file if specified
        if file_path:
            path = Path(file_path)
            if path.exists():
                # Detect type from magic bytes
                with open(path, 'rb') as f:
                    header = f.read(16)
                    for sig, mime in self.FILE_SIGNATURES.items():
                        if header.startswith(sig):
                            result['file_type'] = mime
                            break
                
                result['size_bytes'] = path.stat().st_size
                
                # Read text content for analysis
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        content = f.read(100000)  # Limit to 100KB
                except (UnicodeDecodeError, PermissionError):
                    content = ''
        else:
            result['size_bytes'] = len(content.encode('utf-8'))
        
        # Check for sensitive data
        if check_sensitive and content:
            found_sensitive = []
            for pattern_name, pattern in self.SENSITIVE_PATTERNS.items():
                matches = re.findall(pattern, content)
                if matches:
                    found_sensitive.append({
                        'type': pattern_name,
                        'count': len(matches),
                        'redacted': True
                    })
            
            result['sensitive_data'] = found_sensitive
            
            # Determine sensitivity level
            if any(s['type'] in ('private_key', 'aws_key', 'password', 'api_key') for s in found_sensitive):
                result['sensitivity_level'] = 'CRITICAL'
            elif any(s['type'] in ('ssn', 'credit_card') for s in found_sensitive):
                result['sensitivity_level'] = 'HIGH'
            elif found_sensitive:
                result['sensitivity_level'] = 'MEDIUM'
        
        return result


# =============================================================================
# DETECT TOOL
# =============================================================================

class DetectTool(Tool):
    """
    Detect anomalies in data using statistical methods.
    
    Methods:
    - z_score: Standard deviation from mean
    - iqr: Interquartile range
    - pattern: Regular expression matching
    """
    
    @property
    def spec(self) -> ToolSpec:
        return ToolSpec(
            name="detect",
            category=ToolCategory.DETECTION,
            description="Detect anomalies in data",
            parameters={
                'data': {'type': 'list', 'required': True, 'description': 'Data to analyze'},
                'method': {'type': 'str', 'required': False, 'description': 'Detection method: z_score, iqr, pattern'},
                'threshold': {'type': 'float', 'required': False, 'description': 'Detection threshold'},
                'pattern': {'type': 'str', 'required': False, 'description': 'Regex pattern for pattern method'}
            }
        )
    
    def _execute(self, params: Dict) -> Dict:
        data = params['data']
        method = params.get('method', 'z_score')
        threshold = params.get('threshold', 3.0)
        pattern = params.get('pattern')
        
        if not data:
            return {'anomalies': [], 'count': 0, 'method': method}
        
        anomalies = []
        
        if method == 'z_score':
            # Statistical anomaly detection
            try:
                numeric_data = [float(x) for x in data if isinstance(x, (int, float, str)) and str(x).replace('.', '').replace('-', '').isdigit()]
                if len(numeric_data) >= 2:
                    mean = statistics.mean(numeric_data)
                    stdev = statistics.stdev(numeric_data)
                    
                    if stdev > 0:
                        for i, val in enumerate(data):
                            try:
                                num_val = float(val)
                                z = abs((num_val - mean) / stdev)
                                if z > threshold:
                                    anomalies.append({
                                        'index': i,
                                        'value': val,
                                        'z_score': round(z, 2),
                                        'reason': f'Z-score {z:.2f} exceeds threshold {threshold}'
                                    })
                            except (ValueError, TypeError):
                                continue
            except (ValueError, statistics.StatisticsError):
                pass
        
        elif method == 'iqr':
            # IQR-based detection
            try:
                numeric_data = sorted([float(x) for x in data if isinstance(x, (int, float))])
                if len(numeric_data) >= 4:
                    q1 = numeric_data[len(numeric_data) // 4]
                    q3 = numeric_data[3 * len(numeric_data) // 4]
                    iqr = q3 - q1
                    lower = q1 - 1.5 * iqr
                    upper = q3 + 1.5 * iqr
                    
                    for i, val in enumerate(data):
                        try:
                            num_val = float(val)
                            if num_val < lower or num_val > upper:
                                anomalies.append({
                                    'index': i,
                                    'value': val,
                                    'reason': f'Outside IQR bounds [{lower:.2f}, {upper:.2f}]'
                                })
                        except (ValueError, TypeError):
                            continue
            except (ValueError, TypeError):
                pass
        
        elif method == 'pattern' and pattern:
            # Pattern-based detection
            regex = re.compile(pattern)
            for i, val in enumerate(data):
                str_val = str(val)
                if regex.search(str_val):
                    anomalies.append({
                        'index': i,
                        'value': val,
                        'reason': f'Matches pattern: {pattern}'
                    })
        
        return {
            'method': method,
            'threshold': threshold,
            'data_count': len(data),
            'anomaly_count': len(anomalies),
            'anomalies': anomalies
        }


# =============================================================================
# RECOGNIZE TOOL
# =============================================================================

class RecognizeTool(Tool):
    """
    Recognize entities in text.
    
    Entities:
    - email: Email addresses
    - url: URLs
    - ip: IP addresses
    - hash: Cryptographic hashes
    - date: Dates
    - money: Currency amounts
    """
    
    ENTITY_PATTERNS = {
        'email': r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
        'url': r'https?://[^\s<>"{}|\\^`\[\]]+',
        'ipv4': r'\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b',
        'sha256': r'\b[a-fA-F0-9]{64}\b',
        'sha1': r'\b[a-fA-F0-9]{40}\b',
        'md5': r'\b[a-fA-F0-9]{32}\b',
        'uuid': r'\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b',
        'date_iso': r'\b\d{4}-\d{2}-\d{2}\b',
        'money_usd': r'\$\d{1,3}(?:,\d{3})*(?:\.\d{2})?',
        'money_gbp': r'£\d{1,3}(?:,\d{3})*(?:\.\d{2})?'
    }
    
    @property
    def spec(self) -> ToolSpec:
        return ToolSpec(
            name="recognize",
            category=ToolCategory.DETECTION,
            description="Recognize entities in text",
            parameters={
                'text': {'type': 'str', 'required': True, 'description': 'Text to analyze'},
                'entity_types': {'type': 'list', 'required': False, 'description': 'Entity types to find (default: all)'}
            }
        )
    
    def _execute(self, params: Dict) -> Dict:
        text = params['text']
        entity_types = params.get('entity_types', list(self.ENTITY_PATTERNS.keys()))
        
        entities = {}
        total_count = 0
        
        for entity_type in entity_types:
            if entity_type in self.ENTITY_PATTERNS:
                pattern = self.ENTITY_PATTERNS[entity_type]
                matches = list(set(re.findall(pattern, text)))
                if matches:
                    entities[entity_type] = matches
                    total_count += len(matches)
        
        return {
            'text_length': len(text),
            'entity_types_checked': entity_types,
            'entities_found': total_count,
            'entities': entities
        }


# =============================================================================
# DETECTION TOOLKIT
# =============================================================================

class DetectionToolkit:
    """
    Collection of all detection tools.
    """
    
    def __init__(self):
        self.scan = ScanTool()
        self.classify = ClassifyTool()
        self.detect = DetectTool()
        self.recognize = RecognizeTool()
        
        self._tools = {
            'scan': self.scan,
            'classify': self.classify,
            'detect': self.detect,
            'recognize': self.recognize
        }
    
    def get_tools(self) -> List[Tool]:
        """Get all detection tools."""
        return list(self._tools.values())


# =============================================================================
# SELF-TEST
# =============================================================================

def self_test():
    """
    Self-test of Detection Tools.
    
    Tests:
    1. Scan tool
    2. Classify tool
    3. Detect tool (z_score)
    4. Recognize tool
    """
    print("=" * 60)
    print("JARUS Detection Tools - Self Test")
    print("=" * 60)
    
    # Test scan
    print("\n[1] Test ScanTool...")
    scan = ScanTool()
    result = scan.execute({'path': '/tmp', 'pattern': '*', 'max_files': 5})
    print(f"    Status: {result.status.value}")
    print(f"    Found: {result.output.get('file_count', 0)} files")
    assert result.succeeded
    print("    ✓ PASS")
    
    # Test classify
    print("\n[2] Test ClassifyTool...")
    classify = ClassifyTool()
    test_content = """
    API_KEY = "sk-abc123def456ghi789jkl012mno345"
    Contact: user@example.com
    Password: supersecret123
    """
    result = classify.execute({'content': test_content, 'check_sensitive': True})
    print(f"    Status: {result.status.value}")
    print(f"    Sensitivity: {result.output.get('sensitivity_level')}")
    print(f"    Sensitive items: {len(result.output.get('sensitive_data', []))}")
    assert result.succeeded
    assert result.output['sensitivity_level'] in ('HIGH', 'CRITICAL')
    print("    ✓ PASS")
    
    # Test detect
    print("\n[3] Test DetectTool...")
    detect = DetectTool()
    test_data = [10, 11, 12, 10, 11, 100, 11, 10, 12]  # 100 is anomaly
    result = detect.execute({'data': test_data, 'method': 'z_score', 'threshold': 2.0})
    print(f"    Status: {result.status.value}")
    print(f"    Anomalies found: {result.output.get('anomaly_count', 0)}")
    assert result.succeeded
    assert result.output['anomaly_count'] >= 1
    print("    ✓ PASS")
    
    # Test recognize
    print("\n[4] Test RecognizeTool...")
    recognize = RecognizeTool()
    test_text = """
    Contact: john@example.com
    Visit: https://example.com/page
    Server: 192.168.1.1
    Hash: a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2
    """
    result = recognize.execute({'text': test_text})
    print(f"    Status: {result.status.value}")
    print(f"    Entities found: {result.output.get('entities_found', 0)}")
    print(f"    Types: {list(result.output.get('entities', {}).keys())}")
    assert result.succeeded
    assert 'email' in result.output['entities']
    print("    ✓ PASS")
    
    # Summary
    print("\n" + "=" * 60)
    print("SELF-TEST COMPLETE")
    print("=" * 60)
    print("Tools tested: scan, classify, detect, recognize")
    print("All tests passed ✓")
    
    return True


if __name__ == "__main__":
    self_test()
