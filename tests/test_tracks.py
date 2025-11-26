import pytest
import sys
import os
from pathlib import Path

# Add root to path
sys.path.append(os.getcwd())

# Load .env file if present (for local test runs)
env_file = Path(__file__).parent.parent / ".env"
if env_file.exists():
    for line in env_file.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip())

# Import CONFIG after environment is loaded
from src.core.config import GovernanceConfig
CONFIG = GovernanceConfig.load()

def test_evidence_track_is_stable():
    assert CONFIG.get_agent_track("evidence") == "stable"

def test_property_track_is_insider():
    assert CONFIG.get_agent_track("property") == "insider"