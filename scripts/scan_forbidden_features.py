#!/usr/bin/env python3
"""
Forbidden Features Scanner
==========================
Scans the codebase for features that are forbidden in the current phase.
"""

import sys
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]

# Pattern mappings for forbidden capabilities
PATTERNS = {
    "autonomous_agents": [
        "AutonomousAgent",
        "auto_execute=True",
        "autonomous_mode",
    ],
    "model_training": [
        "model.fit(",
        "trainer.train(",
        "fine_tune(",
    ],
    "production_writes_from_ai": [
        "ai_write_to_prod",
        "production_write=True",
        "PROD_WRITE_ENABLED",
    ],
    "external_api_calls_without_approval": [
        "requests.post(",
        "httpx.post(",
    ],
    "dynamic_policy_modification": [
        "modify_policy(",
        "update_governance(",
    ],
}


def scan(phase_yaml_path: str):
    """Scan codebase for forbidden capabilities."""
    path = Path(phase_yaml_path)

    if not path.exists():
        print(f"ERROR: Phase file not found: {path}")
        sys.exit(1)

    phase = yaml.safe_load(path.read_text())
    forbidden = phase.get("forbidden_capabilities", [])

    if not forbidden:
        print("No forbidden capabilities defined for this phase.")
        return

    hits = []

    for cap in forbidden:
        patterns = PATTERNS.get(cap, [])
        if not patterns:
            continue

        for py_file in ROOT.rglob("*.py"):
            # Skip virtual environments and caches
            if any(skip in str(py_file) for skip in [".venv", "venv", "__pycache__", ".git"]):
                continue

            try:
                text = py_file.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue

            for pattern in patterns:
                if pattern in text:
                    # Find line number
                    for i, line in enumerate(text.split("\n"), 1):
                        if pattern in line:
                            hits.append({
                                "capability": cap,
                                "pattern": pattern,
                                "file": str(py_file.relative_to(ROOT)),
                                "line": i,
                            })

    if hits:
        print(f"Forbidden capabilities detected: {len(hits)} violations")
        for hit in hits:
            print(f"  [{hit['capability']}] {hit['file']}:{hit['line']}")
            print(f"    Pattern: {hit['pattern']}")
        sys.exit(1)

    print(f"Forbidden features scan: OK (checked {len(forbidden)} capabilities)")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: scan_forbidden_features.py governance/phases/phase0.yaml")
        sys.exit(1)
    scan(sys.argv[1])
