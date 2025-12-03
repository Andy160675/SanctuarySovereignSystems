#!/usr/bin/env python3
"""
Governance Configuration Validator
==================================
Validates governance_config.yaml against its JSON schema.
This is a mandatory check before any system operation.
"""

import json
import sys
from pathlib import Path

import yaml

try:
    from jsonschema import validate, ValidationError
except ImportError:
    print("ERROR: jsonschema is required. Install with: pip install jsonschema")
    sys.exit(1)


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "governance" / "governance_config.yaml"
SCHEMA_PATH = ROOT / "governance" / "governance_config.schema.json"


def main():
    if not CONFIG_PATH.exists():
        print(f"ERROR: Governance config not found: {CONFIG_PATH}")
        sys.exit(1)

    if not SCHEMA_PATH.exists():
        print(f"ERROR: Schema not found: {SCHEMA_PATH}")
        sys.exit(1)

    try:
        config = yaml.safe_load(CONFIG_PATH.read_text())
        schema = json.loads(SCHEMA_PATH.read_text())
    except Exception as e:
        print(f"ERROR: Failed to load files: {e}")
        sys.exit(1)

    try:
        validate(instance=config, schema=schema)
        print("Governance config validation: OK")
        print(f"  Constitution version: {config.get('constitution_version')}")
        print(f"  Active phase: {config.get('phases', {}).get('active')}")
        print(f"  Core principles: {len(config.get('core_principles', []))}")
    except ValidationError as e:
        print(f"Governance config validation: FAILED")
        print(f"  Error: {e.message}")
        print(f"  Path: {list(e.absolute_path)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
