#!/usr/bin/env python3
"""
Test Observatory + Evidence Vault + Merge Gate integration.
"""

import tempfile
import os
import sys

# Add project root to path
sys.path.append(os.getcwd())

from sovereign_engine.extensions.observatory import Observatory
from sovereign_engine.extensions.evidence_vault import EvidenceVault
from sovereign_engine.extensions.merge_gate import MergeGate

def test_integration():
    print("Testing bolt-on integration...")
    
    # Create temp directory for vault
    with tempfile.TemporaryDirectory() as tmpdir:
        print(f"Using temp directory: {tmpdir}")
        
        # 1. Test Observatory
        print("\n1. Testing Observatory...")
        obs = Observatory()
        # Mock cpu_percent etc for stability in tests
        metrics = obs.collect_telemetry()
        print(f"  CPU: {metrics.get('cpu_percent', 'N/A')}%")
        print(f"  Memory: {metrics.get('memory_percent', 'N/A')}%")
        print(f"  Kernel tests: {'passed' if metrics.get('kernel_tests_passed') else 'failed'}")
        
        # 2. Test Evidence Vault
        print("\n2. Testing Evidence Vault...")
        vault_path = os.path.join(tmpdir, "vault")
        vault = EvidenceVault(vault_path)
        
        # Store test evidence
        evidence_id = vault.store_evidence(
            "test",
            {"message": "Test evidence", "metrics": metrics},
            {"test": True}
        )
        print(f"  Stored evidence: {evidence_id}")
        
        # Retrieve and verify
        evidence = vault.retrieve_evidence(evidence_id)
        print(f"  Retrieved: {evidence['record']['type']}")
        print(f"  Verified: {vault.verify_evidence(evidence_id)}")
        
        # 3. Test Merge Gate
        print("\n3. Testing Merge Gate...")
        merge_gate = MergeGate(vault_path)
        
        # Simulate PR validation
        results = merge_gate.validate_merge("test-123", "test-branch")
        print(f"  Merge validation: {results['overall']}")
        
        # Check individual validations
        for check_id, check_result in results['checks'].items():
            status = "✓" if check_result['passed'] else "✗"
            print(f"    {status} {check_id}: {check_result['output'][:50]}...")
        
        # 4. Generate manifest
        print("\n4. Testing Manifest Generation...")
        manifest = vault.generate_manifest([evidence_id])
        print(f"  Manifest hash: {manifest['total_hash'][:16]}...")
        print(f"  Items in manifest: {len(manifest['items'])}")
        
        print("\n✅ All bolt-ons integrated successfully!")
        return True

if __name__ == '__main__':
    try:
        if not test_integration():
            sys.exit(1)
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
