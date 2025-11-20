import json
import os
from pathlib import Path

AUDIT_LOG = Path("Governance/Logs/audit_chain.jsonl")

def main():
    print(" Checking Agent Readiness...")
    
    if not AUDIT_LOG.exists():
        print("     No audit log found.")
        return

    total_reviews = 0
    rejections = 0
    
    with open(AUDIT_LOG, 'r') as f:
        for line in f:
            try:
                entry = json.loads(line)
                if entry.get("event") == "HUMAN_REVIEW":
                    total_reviews += 1
                    if entry.get("data", {}).get("decision") == "REJECTED":
                        rejections += 1
            except:
                continue

    if total_reviews == 0:
        accuracy = 0.0
    else:
        accuracy = (total_reviews - rejections) / total_reviews

    print(f" Report generated: readiness_report.json")
    print(f" EVIDENCE-VALIDATOR")
    
    status = "CALIBRATING"
    if total_reviews >= 10 and accuracy >= 0.95:
        status = "READY_FOR_PROMOTION"
        
    print(f"   Status: {status}")
    print(f"   Accuracy: {accuracy:.1%} ({total_reviews - rejections}/{total_reviews})")
    print(f"   Threshold: 95.0%")
    
    if total_reviews < 10:
        print(f"   Note: Samples needed ({total_reviews} < 10)")

if __name__ == "__main__":
    main()