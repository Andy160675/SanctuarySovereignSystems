#!/usr/bin/env python3
"""
Phase Validator
===============
Validates that a phase definition is structurally correct and
that all required tests exist.
"""

import sys
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]


def main(phase_yaml_path: str):
    """Validate a phase definition file."""
    path = Path(phase_yaml_path)

    if not path.exists():
        print(f"ERROR: Phase file not found: {path}")
        sys.exit(1)

    try:
        phase = yaml.safe_load(path.read_text())
    except Exception as e:
        print(f"ERROR: Failed to parse phase file: {e}")
        sys.exit(1)

    # Required fields
    required = ["phase", "name", "description", "automated_exit_tests",
                "allowed_capabilities", "forbidden_capabilities"]
    missing = [f for f in required if f not in phase]
    if missing:
        print(f"ERROR: Missing required fields: {missing}")
        sys.exit(1)

    # Check that automated_exit_test scripts exist
    tests = phase.get("automated_exit_tests", [])
    missing_tests = []
    for test_name in tests:
        # Check in scripts/ and tests/ directories
        script_path = ROOT / "scripts" / f"{test_name}.py"
        test_path = ROOT / "tests" / f"{test_name}.py"
        if not script_path.exists() and not test_path.exists():
            missing_tests.append(test_name)

    if missing_tests:
        print(f"WARNING: Missing automated_exit_tests scripts: {missing_tests}")
        print("  These must be created before phase exit.")

    phase_num = phase.get("phase")
    print(f"Phase {phase_num} validation: OK")
    print(f"  Name: {phase.get('name')}")
    print(f"  Allowed capabilities: {len(phase.get('allowed_capabilities', []))}")
    print(f"  Forbidden capabilities: {len(phase.get('forbidden_capabilities', []))}")
    print(f"  Exit tests: {len(tests)}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: validate_phase.py governance/phases/phase0.yaml")
        sys.exit(1)
    main(sys.argv[1])
