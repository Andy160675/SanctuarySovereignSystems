#!/usr/bin/env python3
"""
JARUS Integration Test
======================
Verifies that Constitutional Runtime and Evidence Ledger 
work together correctly.

Tests:
1. Constitutional decisions are recorded as evidence
2. Evidence chain remains valid across operations
3. Full workflow: evaluate → record → verify

Author: Codex Sovereign Systems
Version: 1.0.0
"""

import sys
import os
from pathlib import Path

# Add project root to path to ensure absolute imports work
root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if root_path not in sys.path:
    sys.path.insert(0, root_path)

from core.constitutional_runtime import ConstitutionalRuntime, DecisionType
from core.evidence_ledger import EvidenceLedger, EvidenceType, ChainStatus
from core.surge_wrapper import SurgeWrapper

def test_surge_wrapper():
    """Verify Surge Wrapper enforces the 'No Receipt, No Action' pattern."""
    print("\n[Surge Test] Verifying Surge Front-End Wrapper...")
    
    runtime = ConstitutionalRuntime()
    ledger = EvidenceLedger(auto_persist=False)
    surge = SurgeWrapper(runtime, ledger)
    
    # 1. Test SUCCESS path
    print("    Testing SUCCESS path...")
    execution_state = {"executed": False}
    def success_handler():
        execution_state["executed"] = True
        return "Action Result"
        
    context = {"action": "test_success", "operator": "tester"}
    result = surge.execute_sovereign_action("test_success", context, success_handler)
    
    assert result["status"] == "SUCCESS"
    assert execution_state["executed"] is True
    assert ledger.entry_count >= 3 # Genesis + Pre-Image + Post-Image
    
    # Verify pre-image exists before post-image
    pre_image = ledger.get_entries()[1]
    post_image = ledger.get_entries()[2]
    assert pre_image.summary == "Surge-Authorized: test_success"
    assert post_image.summary == "Action Complete: test_success"
    print("    ✓ Success path verified")
    
    # 2. Test DENY path
    print("    Testing DENY path...")
    def deny_handler():
        raise Exception("Should not be called")
        
    context_deny = {"fabricated": True} # Triggers CLAUSE-001 HALT
    try:
        surge.execute_sovereign_action("test_deny", context_deny, deny_handler)
    except SystemExit:
        print("    ✓ DENY/HALT path correctly blocked execution")
    
    print("    ✓ Surge Wrapper verification complete")

def integration_test():
    """
    Full integration test of JARUS core components.
    
    Simulates a real workflow:
    1. Initialize both systems
    2. Evaluate actions through constitutional runtime
    3. Record all decisions in evidence ledger
    4. Verify chain integrity
    5. Generate audit report
    """
    print("=" * 60)
    print("JARUS Integration Test")
    print("=" * 60)
    
    # ---------------------------------------------------------------------
    # Step 1: Initialize both systems
    # ---------------------------------------------------------------------
    print("\n[Step 1] Initialize systems...")
    
    runtime = ConstitutionalRuntime()
    ledger = EvidenceLedger(auto_persist=False)
    
    print(f"    Constitutional Runtime initialized")
    print(f"    - Clauses: {len(runtime.get_clauses())}")
    print(f"    - Constitution hash: {runtime.constitution_hash[:16]}...")
    
    print(f"    Evidence Ledger initialized")
    print(f"    - Genesis hash: {ledger.genesis_hash[:16]}...")
    
    print("    ✓ Systems ready")
    
    # ---------------------------------------------------------------------
    # Step 2: Evaluate and record PERMIT decision
    # ---------------------------------------------------------------------
    print("\n[Step 2] Evaluate PERMIT action...")
    
    context1 = {
        'action': 'read_config',
        'path': '/etc/jarus/config.yaml',
        'operator': 'system'
    }
    
    decision1 = runtime.evaluate(context1)
    print(f"    Decision: {decision1.decision_type.value}")
    
    # Record in evidence ledger
    receipt1 = ledger.record_decision(decision1.to_dict())
    print(f"    Recorded as evidence: {receipt1.entry_id[:16]}...")
    
    assert decision1.decision_type == DecisionType.PERMIT
    print("    ✓ PERMIT decision recorded")
    
    # ---------------------------------------------------------------------
    # Step 3: Evaluate and record DENY decision
    # ---------------------------------------------------------------------
    print("\n[Step 3] Evaluate DENY action (boundary violation)...")
    
    context2 = {
        'action': 'delete_all',
        'permitted_actions': ['read_config', 'write_log']
    }
    
    decision2 = runtime.evaluate(context2)
    print(f"    Decision: {decision2.decision_type.value}")
    print(f"    Rationale: {decision2.rationale}")
    
    # Record in evidence ledger
    receipt2 = ledger.record_decision(decision2.to_dict())
    print(f"    Recorded as evidence: {receipt2.entry_id[:16]}...")
    
    assert decision2.decision_type == DecisionType.DENY
    print("    ✓ DENY decision recorded")
    
    # ---------------------------------------------------------------------
    # Step 4: Evaluate and record ESCALATE decision
    # ---------------------------------------------------------------------
    print("\n[Step 4] Evaluate ESCALATE action (requires approval)...")
    
    context3 = {
        'action': 'deploy',
        'target': 'production',
        'operator_approved': False
    }
    
    decision3 = runtime.evaluate(context3)
    print(f"    Decision: {decision3.decision_type.value}")
    print(f"    Rationale: {decision3.rationale}")
    
    # Record in evidence ledger
    receipt3 = ledger.record_decision(decision3.to_dict())
    print(f"    Recorded as evidence: {receipt3.entry_id[:16]}...")
    
    assert decision3.decision_type == DecisionType.ESCALATE
    print("    ✓ ESCALATE decision recorded")
    
    # ---------------------------------------------------------------------
    # Step 5: Record operator attestation
    # ---------------------------------------------------------------------
    print("\n[Step 5] Record operator attestation...")
    
    receipt4 = ledger.record_attestation(
        statement="I verify that all security checks have been performed",
        attester="Andy Jones"
    )
    print(f"    Attestation recorded: {receipt4.entry_id[:16]}...")
    print("    ✓ Attestation recorded")
    
    # ---------------------------------------------------------------------
    # Step 6: Verify evidence chain integrity
    # ---------------------------------------------------------------------
    print("\n[Step 6] Verify evidence chain integrity...")
    
    verification = ledger.verify_chain()
    print(f"    Status: {verification.status.value}")
    print(f"    Entries checked: {verification.entries_checked}")
    print(f"    Chain hash: {verification.chain_hash[:16]}...")
    
    assert verification.status == ChainStatus.VALID
    print("    ✓ Chain integrity verified")
    
    # ---------------------------------------------------------------------
    # Step 7: Verify constitutional runtime chain
    # ---------------------------------------------------------------------
    print("\n[Step 7] Verify constitutional decision chain...")
    
    valid, error = runtime.verify_chain()
    print(f"    Valid: {valid}")
    print(f"    Decisions in chain: {runtime.decision_count}")
    
    assert valid
    print("    ✓ Decision chain verified")
    
    # ---------------------------------------------------------------------
    # Step 8: Verify receipts still valid
    # ---------------------------------------------------------------------
    print("\n[Step 8] Verify all receipts...")
    
    receipts = [receipt1, receipt2, receipt3, receipt4]
    for i, receipt in enumerate(receipts, 1):
        is_valid = ledger.verify_receipt(receipt)
        print(f"    Receipt {i}: {'✓ Valid' if is_valid else '✗ Invalid'}")
        assert is_valid
    
    print("    ✓ All receipts verified")
    
    # ---------------------------------------------------------------------
    # Step 9: Generate audit report
    # ---------------------------------------------------------------------
    print("\n[Step 9] Generate audit report...")
    
    report = ledger.generate_report()
    print(f"    Total entries: {report['total_entries']}")
    print(f"    Chain status: {report['chain_status']}")
    print(f"    Entries by type: {report['entries_by_type']}")
    
    assert report['chain_status'] == 'VALID'
    assert report['total_entries'] == 5  # Genesis + 4 records
    print("    ✓ Audit report generated")
    
    # ---------------------------------------------------------------------
    # Summary
    # ---------------------------------------------------------------------
    print("\n" + "=" * 60)
    print("INTEGRATION TEST COMPLETE")
    print("=" * 60)
    print(f"Constitutional Runtime:")
    print(f"  - Clauses: {len(runtime.get_clauses())}")
    print(f"  - Decisions: {runtime.decision_count}")
    print(f"  - Violations: {runtime.violation_count}")
    print(f"  - Constitution hash: {runtime.constitution_hash[:32]}...")
    print()
    print(f"Evidence Ledger:")
    print(f"  - Entries: {ledger.entry_count}")
    print(f"  - Chain status: {verification.status.value}")
    print(f"  - Chain hash: {ledger.chain_hash[:32]}...")
    print()
    print("All integration tests passed ✓")
    
    return True


if __name__ == "__main__":
    test_surge_wrapper()
    success = integration_test()
    sys.exit(0 if success else 1)
