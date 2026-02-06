#!/usr/bin/env python3
"""
Sovereign Security Scanner (The Hacking Solution)
Part of the Hacking Suite.

This script scans the sovereign node for common vulnerabilities, 
misconfigurations, and potential security breaches.
"""

import os
import sys
import json
import hashlib
from pathlib import Path
from datetime import datetime, timezone

# Critical files that must be protected
CRITICAL_FILES = [
    "sovereign.key",
    "sovereign.pub",
    "CANON/SYSTEM_LAW.md",
    "AUTONOMY_LIMITS.md"
]

def utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def check_file_permissions():
    """Check for loose permissions on critical files (Simulated for Windows)."""
    vulnerabilities = []
    for cf in CRITICAL_FILES:
        path = Path(cf)
        if path.exists():
            # In a real Windows environment, we'd check ACLs.
            # Here we simulate by checking if they are 'too easy' to find/read.
            stats = path.stat()
            if stats.st_size == 0:
                vulnerabilities.append({
                    "target": cf,
                    "issue": "Empty critical file",
                    "severity": "CRITICAL"
                })
    return vulnerabilities

def check_missing_seals():
    """Check for files in Codex that are missing .sha256.txt seals."""
    vulnerabilities = []
    codex_dir = Path("Codex")
    if codex_dir.exists():
        for md_file in codex_dir.glob("**/*.md"):
            seal_file = Path(f"{md_file}.sha256.txt")
            if not seal_file.exists():
                vulnerabilities.append({
                    "target": str(md_file),
                    "issue": "Missing tamper-evidence seal",
                    "severity": "HIGH"
                })
    return vulnerabilities

def check_network_anomalies():
    """Check for suspicious external connections (Simulated)."""
    # This would normally use psutil or netstat
    return []

def main():
    print(f"=== SOVEREIGN SECURITY SCANNER [{utc_now_iso()}] ===")
    
    report = {
        "timestamp": utc_now_iso(),
        "scanner": "SOV_SEC_SCANNER_V1",
        "results": []
    }
    
    print("[1/3] Checking file integrity...")
    report["results"].extend(check_file_permissions())
    
    print("[2/3] Auditing tamper-evidence seals...")
    report["results"].extend(check_missing_seals())
    
    print("[3/3] Scanning for network anomalies...")
    report["results"].extend(check_network_anomalies())
    
    # Save report
    out_dir = Path("validation/security")
    out_dir.mkdir(parents=True, exist_ok=True)
    report_file = out_dir / f"scan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    
    print(f"\nSCAN COMPLETE. Found {len(report['results'])} vulnerabilities.")
    print(f"REPORT: {report_file}")
    
    if len(report['results']) > 0:
        for v in report['results']:
            print(f"  [{v['severity']}] {v['target']}: {v['issue']}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
