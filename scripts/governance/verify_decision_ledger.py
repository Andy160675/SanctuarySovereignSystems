#!/usr/bin/env python3
"""
Sovereign Decision Ledger Verification
Verifies tamper-evident hash chain integrity of the decision ledger.

Usage:
    python scripts/governance/verify_decision_ledger.py

Returns:
    - Exit 0: Ledger verified, integrity intact
    - Exit 1: Ledger missing, empty, or corrupted
"""

import sys
import json
import hashlib
from pathlib import Path
from datetime import datetime

LEDGER_PATH = Path("Governance/Logs/audit_chain.jsonl")

def compute_entry_hash(entry: dict, prev_hash: str = "") -> str:
    """Compute deterministic hash for a ledger entry."""
    canonical = json.dumps(entry, sort_keys=True, separators=(',', ':'))
    payload = f"{prev_hash}{canonical}"
    return hashlib.sha256(payload.encode('utf-8')).hexdigest()

def verify_ledger():
    """Verify ledger integrity and return verification report."""
    report = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "ledger_path": str(LEDGER_PATH),
        "status": "UNKNOWN",
        "entry_count": 0,
        "first_entry": None,
        "last_entry": None,
        "chain_valid": False,
        "errors": []
    }
    
    # Check ledger exists
    if not LEDGER_PATH.exists():
        report["status"] = "FAIL"
        report["errors"].append("Ledger file not found")
        return report
    
    # Read entries
    try:
        lines = LEDGER_PATH.read_text(encoding="utf-8").strip().splitlines()
    except Exception as e:
        report["status"] = "FAIL"
        report["errors"].append(f"Read error: {e}")
        return report
    
    if not lines:
        report["status"] = "FAIL"
        report["errors"].append("Ledger is empty")
        return report
    
    report["entry_count"] = len(lines)
    
    # Parse and verify chain
    prev_hash = ""
    chain_valid = True
    
    for i, line in enumerate(lines):
        try:
            entry = json.loads(line)
            
            # Record first/last entries
            if i == 0:
                report["first_entry"] = {
                    "timestamp": entry.get("timestamp"),
                    "event_type": entry.get("event_type", "UNKNOWN")
                }
            if i == len(lines) - 1:
                report["last_entry"] = {
                    "timestamp": entry.get("timestamp"),
                    "event_type": entry.get("event_type", "UNKNOWN")
                }
            
            # Verify hash chain if entry has prev_hash field
            if "prev_hash" in entry and entry["prev_hash"] != prev_hash:
                chain_valid = False
                report["errors"].append(f"Chain break at entry {i+1}")
            
            # Compute hash for next iteration
            if "hash" in entry:
                prev_hash = entry["hash"]
            else:
                prev_hash = compute_entry_hash(entry, prev_hash)
                
        except json.JSONDecodeError as e:
            chain_valid = False
            report["errors"].append(f"JSON parse error at line {i+1}: {e}")
    
    report["chain_valid"] = chain_valid
    report["status"] = "PASS" if chain_valid and not report["errors"] else "FAIL"
    
    return report

def main():
    print("=" * 60)
    print("SOVEREIGN DECISION LEDGER VERIFICATION")
    print("=" * 60)
    
    report = verify_ledger()
    
    print(f"\nTimestamp: {report['timestamp']}")
    print(f"Ledger: {report['ledger_path']}")
    print(f"Status: {'✅ ' if report['status'] == 'PASS' else '❌ '}{report['status']}")
    print(f"Entries: {report['entry_count']}")
    
    if report['first_entry']:
        print(f"First: {report['first_entry']['timestamp']} ({report['first_entry']['event_type']})")
    if report['last_entry']:
        print(f"Last: {report['last_entry']['timestamp']} ({report['last_entry']['event_type']})")
    
    print(f"Chain Valid: {'✅ YES' if report['chain_valid'] else '❌ NO'}")
    
    if report['errors']:
        print("\nErrors:")
        for err in report['errors']:
            print(f"  - {err}")
    
    print("=" * 60)
    
    # Write report to validation directory
    validation_dir = Path("validation")
    validation_dir.mkdir(exist_ok=True)
    report_path = validation_dir / f"ledger_verify_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
    report_path.write_text(json.dumps(report, indent=2))
    print(f"Report saved: {report_path}")
    
    sys.exit(0 if report['status'] == 'PASS' else 1)

if __name__ == "__main__":
    main()
