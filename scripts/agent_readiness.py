import os
import sys
# Add root to path
sys.path.append(os.getcwd())

from src.core.config import CONFIG

def check_readiness():
    print("📊 SYSTEM READINESS CHECK")
    
    evidence_track = CONFIG.get_agent_track("evidence")
    property_track = CONFIG.get_agent_track("property")
    
    print(f"   EVIDENCE: {evidence_track.upper()}")
    print(f"   PROPERTY: {property_track.upper()}")
    
    if evidence_track != "stable":
        print("❌ Evidence Agent should be STABLE")
        sys.exit(1)
        
    if property_track != "insider":
        print("❌ Property Agent should be INSIDER")
        sys.exit(1)
        
    print("✅ ALL SYSTEMS GO")

if __name__ == "__main__":
    check_readiness()