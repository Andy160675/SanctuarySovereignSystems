import pytest
import sys
import os

# Add root to path
sys.path.append(os.getcwd())

from src.core.config import CONFIG

def test_evidence_track_is_stable():
    assert CONFIG.get_agent_track("evidence") == "stable"

def test_property_track_is_insider():
    assert CONFIG.get_agent_track("property") == "insider"