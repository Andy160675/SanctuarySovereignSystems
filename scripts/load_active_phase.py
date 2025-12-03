#!/usr/bin/env python3
"""
Active Phase Loader
===================
Loads the active phase configuration from the governance directory.
"""

import json
import os
import sys
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
PHASE_FILE = ROOT / "governance" / "ACTIVE_PHASE"


def load_active_phase():
    """Load the active phase configuration."""
    if PHASE_FILE.exists():
        phase = int(PHASE_FILE.read_text().strip())
    else:
        phase = int(os.environ.get("ACTIVE_PHASE", "0"))

    phase_path = ROOT / "governance" / "phases" / f"phase{phase}.yaml"

    if not phase_path.exists():
        raise FileNotFoundError(f"Phase definition not found: {phase_path}")

    data = yaml.safe_load(phase_path.read_text())
    data["_loaded_from"] = str(phase_path)
    return data


if __name__ == "__main__":
    try:
        phase_data = load_active_phase()
        print(json.dumps(phase_data, indent=2, default=str))
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)
