#!/usr/bin/env python3
"""
Demo all bolt-ons working together.
"""

import tempfile
import os
import json
import sys
from datetime import datetime, timedelta

# Add project root to path
sys.path.append(os.getcwd())

def run_demo():
    print("="*60)
    print("Sovereign Engine Bolt-Ons Demo")
    print("="*60)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        print(f"Working directory: {tmpdir}")
        original_cwd = os.getcwd()
        os.chdir(tmpdir)
        
        try:
            # 1. Observatory
            print("\n1. 🛰️  Observatory - System Monitoring")
            from sovereign_engine.extensions.observatory import Observatory
            obs = Observatory()
            health = obs.generate_health_report()
            print(f"   Status: {health['status']}")
            print(f"   CPU: {health['metrics'].get('cpu_percent', 'N/A')}%")
            print(f"   Memory: {health['metrics'].get('memory_percent', 'N/A')}%")
            
            # 2. Evidence Vault
            print("\n2. 🔒 Evidence Vault - Immutable Storage")
            from sovereign_engine.extensions.evidence_vault import EvidenceVault
            vault = EvidenceVault("./demo_vault")
            
            # Store observatory data
            eid = vault.store_evidence(
                "system_health",
                health,
                {"source": "observatory_demo"}
            )
            print(f"   Stored evidence: {eid}")
            print(f"   Verified: {vault.verify_evidence(eid)}")
            
            # 3. Merge Gate
            print("\n3. 🚧 Merge Gate - Governance Enforcement")
            from sovereign_engine.extensions.merge_gate import MergeGate
            mg = MergeGate("./demo_vault")
            
            results = mg.validate_merge("demo-001", "demo-branch")
            print(f"   Validation: {results['overall']}")
            print(f"   Evidence ID: {results.get('evidence_id', 'N/A')}")
            
            # 4. Compliance Pack
            print("\n4. 📋 Compliance Pack - SOC2 Audit")
            from sovereign_engine.extensions.compliance import get_compliance_pack
            soc2 = get_compliance_pack("soc2")
            audit = soc2.run_audit({"risk_assessment": True})
            print(f"   Score: {audit['summary']['compliance_score']:.1f}%")
            print(f"   Controls: {audit['summary']['total_controls']}")
            
            # 5. Board Pack Templates
            print("\n5. 📊 Board Pack Templates - Professional Reports")
            from sovereign_engine.extensions.board_packs import BoardPackGenerator
            generator = BoardPackGenerator("DemoCorp")
            
            # Generate investor pack
            metrics = {
                "status": "Operational",
                "compliance_score": audit['summary']['compliance_score'],
                "uptime": "99.95%",
                "stability": "High",
                "revenue_growth": "18%"
            }
            
            investor_pack = generator.generate_investor_pack(metrics, "Q4 2024")
            print(f"   Investor pack: {len(investor_pack)} characters")
            print(f"   Sections: {investor_pack.count('##')}")
            
            # Save sample output
            with open("demo_investor_pack.md", "w", encoding="utf-8") as f:
                f.write(investor_pack)
            
            # 6. Slack Integration (if configured)
            print("\n6. 🔗 Slack Connector - Alerting")
            from sovereign_engine.extensions.connectors.slack import SlackConnector
            slack = SlackConnector()
            
            if slack.webhook_url:
                success = slack.send_alert(
                    message="Bolt-ons demo completed successfully",
                    severity="info",
                    context={"evidence_id": eid, "compliance_score": audit['summary']['compliance_score']}
                )
                print(f"   Alert sent: {success}")
            else:
                print("   No Slack webhook configured (set SLACK_WEBHOOK_URL env var)")
            
            # 7. Generate summary report
            print("\n7. 📈 Integration Summary")
            print("   " + "="*50)
            print("   | Component        | Status     | Output")
            print("   |------------------|------------|-------------------")
            print(f"   | Observatory      | {'✅' if health['status'] == 'healthy' else '⚠️'} | Health monitoring")
            print(f"   | Evidence Vault   | ✅         | {eid}")
            print(f"   | Merge Gate       | ✅         | {results['overall']}")
            print(f"   | Compliance Pack  | ✅         | {audit['summary']['compliance_score']:.1f}%")
            print(f"   | Board Packs      | ✅         | Report generated")
            print(f"   | Slack Connector  | {'✅' if slack.webhook_url else '⚠️'} | Alerts {'enabled' if slack.webhook_url else 'disabled'}")
            print("   " + "="*50)
            
            print("\n✅ Demo completed successfully!")
            print(f"\nFiles created in: {tmpdir}")
            print("  - demo_vault/ (evidence storage)")
            print("  - demo_investor_pack.md (sample report)")
            
        finally:
            os.chdir(original_cwd)
        
        return True

if __name__ == '__main__':
    try:
        run_demo()
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
