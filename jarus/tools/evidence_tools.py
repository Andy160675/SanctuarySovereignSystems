#!/usr/bin/env python3
"""
JARUS Evidence Tools
====================
Tools for collecting and managing evidence.

Tools:
- collect: Gather evidence from sources
- receipt: Generate evidence receipts
- custody: Track chain of custody
- export: Export evidence packages

Author: Codex Sovereign Systems
Version: 1.0.0
"""

import hashlib
import json
import zipfile
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime, timezone

from .tool_base import Tool, ToolSpec, ToolCategory


# =============================================================================
# COLLECT TOOL
# =============================================================================

class CollectTool(Tool):
    """Collect evidence from various sources."""
    
    @property
    def spec(self) -> ToolSpec:
        return ToolSpec(
            name="collect",
            category=ToolCategory.EVIDENCE,
            description="Collect evidence from various sources",
            parameters={
                'source_type': {'type': 'str', 'required': True, 'description': 'file, directory, data'},
                'source': {'type': 'str', 'required': True, 'description': 'Source path or data'},
                'metadata': {'type': 'dict', 'required': False, 'description': 'Additional metadata'}
            }
        )
    
    def _execute(self, params: Dict) -> Dict:
        source_type = params['source_type']
        source = params['source']
        metadata = params.get('metadata', {})
        
        now = datetime.now(timezone.utc)
        collection_id = hashlib.sha256(f"{source}{now.isoformat()}".encode()).hexdigest()[:12]
        
        evidence = {
            'collection_id': collection_id,
            'source_type': source_type,
            'collected_at': now.isoformat(),
            'items': [],
            'metadata': metadata
        }
        
        if source_type == 'file':
            path = Path(source)
            if path.exists() and path.is_file():
                with open(path, 'rb') as f:
                    content = f.read()
                file_hash = hashlib.sha256(content).hexdigest()
                evidence['items'].append({
                    'path': str(path),
                    'name': path.name,
                    'size': len(content),
                    'hash': file_hash,
                    'hash_algorithm': 'sha256'
                })
            else:
                return {'collected': False, 'error': f"File not found: {source}"}
        
        elif source_type == 'directory':
            path = Path(source)
            if path.exists() and path.is_dir():
                for f in path.rglob('*'):
                    if f.is_file():
                        try:
                            with open(f, 'rb') as fp:
                                content = fp.read()
                            file_hash = hashlib.sha256(content).hexdigest()
                            evidence['items'].append({
                                'path': str(f),
                                'name': f.name,
                                'size': len(content),
                                'hash': file_hash
                            })
                        except (PermissionError, OSError):
                            continue
                        if len(evidence['items']) >= 100:  # Limit
                            break
            else:
                return {'collected': False, 'error': f"Directory not found: {source}"}
        
        elif source_type == 'data':
            data_bytes = source.encode('utf-8') if isinstance(source, str) else source
            data_hash = hashlib.sha256(data_bytes).hexdigest()
            evidence['items'].append({
                'type': 'inline_data',
                'size': len(data_bytes),
                'hash': data_hash,
                'preview': source[:100] + '...' if len(source) > 100 else source
            })
        
        evidence['item_count'] = len(evidence['items'])
        evidence['total_hash'] = hashlib.sha256(
            json.dumps(evidence['items'], sort_keys=True).encode()
        ).hexdigest()
        
        return {'collected': True, **evidence}


# =============================================================================
# RECEIPT TOOL
# =============================================================================

class ReceiptTool(Tool):
    """Generate evidence receipts for proof of collection."""
    
    @property
    def spec(self) -> ToolSpec:
        return ToolSpec(
            name="receipt",
            category=ToolCategory.EVIDENCE,
            description="Generate evidence receipts",
            parameters={
                'evidence_hash': {'type': 'str', 'required': True, 'description': 'Hash of evidence'},
                'description': {'type': 'str', 'required': True, 'description': 'Description'},
                'collector': {'type': 'str', 'required': True, 'description': 'Who collected'},
                'witness': {'type': 'str', 'required': False, 'description': 'Witness identifier'}
            }
        )
    
    def _execute(self, params: Dict) -> Dict:
        evidence_hash = params['evidence_hash']
        description = params['description']
        collector = params['collector']
        witness = params.get('witness')
        
        now = datetime.now(timezone.utc)
        
        receipt = {
            'receipt_id': hashlib.sha256(f"{evidence_hash}{now.isoformat()}".encode()).hexdigest()[:16],
            'evidence_hash': evidence_hash,
            'description': description,
            'collector': collector,
            'witness': witness,
            'issued_at': now.isoformat()
        }
        
        # Create receipt hash (for verification)
        receipt_content = json.dumps({
            'evidence_hash': evidence_hash,
            'description': description,
            'collector': collector,
            'witness': witness,
            'issued_at': receipt['issued_at']
        }, sort_keys=True)
        
        receipt['receipt_hash'] = hashlib.sha256(receipt_content.encode()).hexdigest()
        
        return receipt


# =============================================================================
# CUSTODY TOOL
# =============================================================================

class CustodyTool(Tool):
    """Track chain of custody for evidence."""
    
    # In-memory custody chains (would be persisted in production)
    _chains: Dict[str, List[Dict]] = {}
    
    @property
    def spec(self) -> ToolSpec:
        return ToolSpec(
            name="custody",
            category=ToolCategory.EVIDENCE,
            description="Track chain of custody",
            parameters={
                'evidence_id': {'type': 'str', 'required': True, 'description': 'Evidence identifier'},
                'action': {'type': 'str', 'required': True, 'description': 'transfer, access, view'},
                'from_party': {'type': 'str', 'required': False, 'description': 'Transferring party'},
                'to_party': {'type': 'str', 'required': False, 'description': 'Receiving party'},
                'reason': {'type': 'str', 'required': False, 'description': 'Reason for action'}
            }
        )
    
    def _execute(self, params: Dict) -> Dict:
        evidence_id = params['evidence_id']
        action = params['action']
        from_party = params.get('from_party')
        to_party = params.get('to_party')
        reason = params.get('reason', '')
        
        now = datetime.now(timezone.utc)
        
        if evidence_id not in CustodyTool._chains:
            CustodyTool._chains[evidence_id] = []
        
        chain = CustodyTool._chains[evidence_id]
        
        entry = {
            'entry_id': hashlib.sha256(f"{evidence_id}{action}{now.isoformat()}".encode()).hexdigest()[:12],
            'action': action,
            'timestamp': now.isoformat(),
            'from_party': from_party,
            'to_party': to_party,
            'reason': reason,
            'sequence': len(chain) + 1
        }
        
        # Link to previous entry
        if chain:
            entry['previous_hash'] = hashlib.sha256(
                json.dumps(chain[-1], sort_keys=True).encode()
            ).hexdigest()
        
        entry['entry_hash'] = hashlib.sha256(
            json.dumps(entry, sort_keys=True).encode()
        ).hexdigest()
        
        chain.append(entry)
        
        return {
            'recorded': True,
            'evidence_id': evidence_id,
            'entry': entry,
            'chain_length': len(chain)
        }


# =============================================================================
# EXPORT TOOL
# =============================================================================

class ExportTool(Tool):
    """Export evidence packages."""
    
    EXPORT_DIR = Path('/tmp/jarus_exports')
    
    @property
    def spec(self) -> ToolSpec:
        return ToolSpec(
            name="export_evidence",
            category=ToolCategory.EVIDENCE,
            description="Export evidence packages",
            parameters={
                'evidence_id': {'type': 'str', 'required': True, 'description': 'Evidence to export'},
                'format': {'type': 'str', 'required': False, 'description': 'json, zip'},
                'include_metadata': {'type': 'bool', 'required': False, 'description': 'Include metadata'}
            }
        )
    
    def _execute(self, params: Dict) -> Dict:
        evidence_id = params['evidence_id']
        export_format = params.get('format', 'json')
        include_metadata = params.get('include_metadata', True)
        
        now = datetime.now(timezone.utc)
        self.EXPORT_DIR.mkdir(parents=True, exist_ok=True)
        
        # Build export package
        package = {
            'export_id': hashlib.sha256(f"{evidence_id}{now.isoformat()}".encode()).hexdigest()[:12],
            'evidence_id': evidence_id,
            'exported_at': now.isoformat(),
            'format': export_format
        }
        
        # Get custody chain if exists
        if evidence_id in CustodyTool._chains:
            package['custody_chain'] = CustodyTool._chains[evidence_id]
        
        if include_metadata:
            package['metadata'] = {
                'exporter': 'JARUS Evidence System',
                'version': '1.0.0',
                'integrity_algorithm': 'sha256'
            }
        
        # Calculate package hash
        package['package_hash'] = hashlib.sha256(
            json.dumps(package, sort_keys=True, default=str).encode()
        ).hexdigest()
        
        # Write to file
        if export_format == 'json':
            export_path = self.EXPORT_DIR / f"evidence_{package['export_id']}.json"
            with open(export_path, 'w') as f:
                json.dump(package, f, indent=2)
        elif export_format == 'zip':
            export_path = self.EXPORT_DIR / f"evidence_{package['export_id']}.zip"
            with zipfile.ZipFile(export_path, 'w') as zf:
                zf.writestr('evidence.json', json.dumps(package, indent=2))
                zf.writestr('manifest.txt', f"Evidence ID: {evidence_id}\nExport ID: {package['export_id']}\n")
        
        return {
            'exported': True,
            'export_id': package['export_id'],
            'export_path': str(export_path),
            'package_hash': package['package_hash']
        }


# =============================================================================
# EVIDENCE TOOLKIT
# =============================================================================

class EvidenceToolkit:
    """
    Collection of all evidence tools.
    """
    
    def __init__(self):
        self.collect = CollectTool()
        self.receipt = ReceiptTool()
        self.custody = CustodyTool()
        self.export = ExportTool()
        
        self._tools = {
            'collect': self.collect,
            'receipt': self.receipt,
            'custody': self.custody,
            'export': self.export
        }
    
    def get_tools(self) -> List[Tool]:
        """Get all evidence tools."""
        return list(self._tools.values())


# =============================================================================
# SELF-TEST
# =============================================================================

def self_test():
    print("=" * 60)
    print("JARUS Evidence Tools - Self Test")
    print("=" * 60)
    
    # Test collect
    print("\n[1] Test CollectTool...")
    collect = CollectTool()
    result = collect.execute({'source_type': 'data', 'source': 'Test evidence data for collection'})
    print(f"    Status: {result.status.value}")
    print(f"    Collection ID: {result.output.get('collection_id')}")
    print(f"    Items collected: {result.output.get('item_count')}")
    assert result.succeeded
    assert result.output.get('collected')
    evidence_hash = result.output.get('total_hash')
    print("    ✓ PASS")
    
    # Test receipt
    print("\n[2] Test ReceiptTool...")
    receipt = ReceiptTool()
    result = receipt.execute({
        'evidence_hash': evidence_hash,
        'description': 'Test evidence collection',
        'collector': 'test_operator',
        'witness': 'test_witness'
    })
    print(f"    Status: {result.status.value}")
    print(f"    Receipt ID: {result.output.get('receipt_id')}")
    print(f"    Receipt Hash: {result.output.get('receipt_hash', '')[:32]}...")
    assert result.succeeded
    print("    ✓ PASS")
    
    # Test custody
    print("\n[3] Test CustodyTool...")
    custody = CustodyTool()
    evidence_id = f"EV-{evidence_hash[:8]}"
    
    result = custody.execute({
        'evidence_id': evidence_id,
        'action': 'transfer',
        'from_party': 'collector',
        'to_party': 'examiner',
        'reason': 'For analysis'
    })
    print(f"    Status: {result.status.value}")
    print(f"    Chain length: {result.output.get('chain_length')}")
    assert result.succeeded
    
    # Add another entry
    result = custody.execute({
        'evidence_id': evidence_id,
        'action': 'access',
        'from_party': 'examiner',
        'reason': 'Analysis complete'
    })
    print(f"    Chain length after access: {result.output.get('chain_length')}")
    assert result.output.get('chain_length') == 2
    print("    ✓ PASS")
    
    # Test export
    print("\n[4] Test ExportTool...")
    export = ExportTool()
    result = export.execute({
        'evidence_id': evidence_id,
        'format': 'json',
        'include_metadata': True
    })
    print(f"    Status: {result.status.value}")
    print(f"    Export ID: {result.output.get('export_id')}")
    print(f"    Export path: {result.output.get('export_path')}")
    assert result.succeeded
    assert result.output.get('exported')
    print("    ✓ PASS")
    
    print("\n" + "=" * 60)
    print("SELF-TEST COMPLETE")
    print("=" * 60)
    print("Tools tested: collect, receipt, custody, export")
    print("All tests passed ✓")
    return True


if __name__ == "__main__":
    self_test()
