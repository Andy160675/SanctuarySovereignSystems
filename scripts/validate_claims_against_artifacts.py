#!/usr/bin/env python3
"""
Claims Validator
================
Validates that all claims are backed by appropriate evidence
and respects phase boundaries.
"""

import json
import sys
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
CLAIMS_PATH = ROOT / "claims" / "claims.yaml"
ARTIFACTS_PATH = ROOT / "artifacts" / "index.jsonl"
PHASE_FILE = ROOT / "governance" / "ACTIVE_PHASE"
REPORT_PATH = ROOT / "artifacts" / "claims_report.json"


def main():
    # Load active phase
    if PHASE_FILE.exists():
        active_phase = int(PHASE_FILE.read_text().strip())
    else:
        print("WARNING: ACTIVE_PHASE file not found, defaulting to 0")
        active_phase = 0

    # Load claims
    if not CLAIMS_PATH.exists():
        print("ERROR: claims.yaml not found")
        sys.exit(1)

    claims_data = yaml.safe_load(CLAIMS_PATH.read_text())
    claims = claims_data.get("claims", [])

    # Load artifacts
    artifact_ids = set()
    if ARTIFACTS_PATH.exists():
        for line in ARTIFACTS_PATH.read_text().splitlines():
            if line.strip():
                try:
                    artifact = json.loads(line)
                    artifact_ids.add(artifact.get("artifact_id"))
                    artifact_ids.add(artifact.get("type"))  # Also match by type
                except json.JSONDecodeError:
                    pass

    # Validate claims
    verified = []
    prohibited = []
    invalid = []

    for claim in claims:
        claim_id = claim.get("id")
        phase_required = claim.get("phase_required", 0)
        status = claim.get("status", "unknown")

        # Check phase restriction
        if phase_required > active_phase:
            claim["status"] = f"prohibited_until_phase_{phase_required}"
            prohibited.append(claim)
            continue

        # Check evidence for verified claims
        if status == "verified":
            evidence = claim.get("evidence", [])
            has_artifact = False
            has_test = False

            for ev in evidence:
                if "artifact" in ev:
                    artifact_name = ev["artifact"]
                    if artifact_name in artifact_ids:
                        has_artifact = True
                if "test" in ev:
                    test_name = ev["test"]
                    # Check if test script exists
                    test_path = ROOT / "tests" / test_name
                    script_path = ROOT / "scripts" / test_name
                    if test_path.exists() or script_path.exists():
                        has_test = True

            if not has_artifact and not has_test:
                claim["status"] = "invalid"
                claim["reason"] = "No valid artifact or test evidence found"
                invalid.append(claim)
            else:
                verified.append(claim)
        else:
            # Pending or other status
            prohibited.append(claim)

    # Generate report
    report = {
        "active_phase": active_phase,
        "total_claims": len(claims),
        "verified_count": len(verified),
        "prohibited_count": len(prohibited),
        "invalid_count": len(invalid),
        "verified": [c["id"] for c in verified],
        "prohibited": [c["id"] for c in prohibited],
        "invalid": [{"id": c["id"], "reason": c.get("reason", "N/A")} for c in invalid],
    }

    # Ensure artifacts directory exists
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2))

    # Output results
    print(f"Claims validation report written: {REPORT_PATH}")
    print(f"  Active phase: {active_phase}")
    print(f"  Verified: {len(verified)}")
    print(f"  Prohibited: {len(prohibited)}")
    print(f"  Invalid: {len(invalid)}")

    if invalid:
        print("\nINVALID CLAIMS:")
        for c in invalid:
            print(f"  - {c['id']}: {c.get('reason', 'N/A')}")
        sys.exit(1)

    print("\nClaims validation: OK")


if __name__ == "__main__":
    main()
