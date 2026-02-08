"""
Sovereign Platform Initialization Script
Validates the foundation of the 90-day execution matrix.
"""

import asyncio
import os
import sys
from src.core.governance_pack import GovernancePack
from src.core.boardroom_engine import BoardroomDecisionEngine

async def main():
    print("="*60)
    print("SOVEREIGN PLATFORM INITIALIZATION")
    print("="*60)
    
    # 1. Initialize Governance Pack
    print("\n1. Initializing Governance Core Pack...")
    gov = GovernancePack()
    print("   ✓ Governance Core initialized.")
    
    # 2. Verify Evidence Chain
    print("\n2. Verifying Evidence Chain Integrity...")
    integrity = gov.verify_integrity()
    print(f"   ✓ Integrity check: {'PASSED' if integrity else 'FAILED'}")
    
    # 3. Check for Drift
    print("\n3. Running Constitutional Drift Guard...")
    alerts = gov.drift_guard.monitor_kernel()
    if alerts:
        for alert in alerts:
            print(f"   ⚠️  {alert}")
    else:
        print("   ✓ No constitutional drift detected.")
        
    # 4. Initialize Boardroom
    print("\n4. Initializing Boardroom Pro Engine...")
    boardroom = BoardroomDecisionEngine()
    print("   ✓ Boardroom initialized.")
    
    # 5. Run Demo Proposal
    print("\n5. Running Demo Deliberation...")
    proposal = {
        "id": "PROP-2026-001",
        "type": "governance",
        "policy": "boardroom_default",
        "context": {
            "amount": 500,
            "authority": "steward"
        }
    }
    
    # Pre-load a policy for the demo
    gov.policy_compiler.load_policy("boardroom_default", {
        "rules": [
            {"field": "amount", "operator": "lt", "value": 1000}
        ]
    })
    
    decision = await boardroom.deliberate(proposal)
    print(f"   Decision: {decision['verdict']}")
    print(f"   Reason: {decision['reason']}")
    
    # 6. Export Audit Trail
    print("\n6. Exporting Foundation Evidence...")
    audit = gov.get_audit_trail()
    print(f"   ✓ Audit trail contains {len(audit)} sealed records.")
    
    print("\n" + "="*60)
    print("FOUNDATION SPRINT: READY FOR DAY 2")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(main())
