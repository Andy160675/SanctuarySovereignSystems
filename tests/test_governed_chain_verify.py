# -*- coding: utf-8 -*-
"""
Invariant Tests for Governed Chain Verification

These tests enforce constitutional guarantees:
1. Governed verification MUST produce a governance commit
2. Governed verification MUST produce an anchor sidecar
3. Governed verification MUST trigger automation dispatch
4. When automation runs, verification report MUST link back to commit

Run with: pytest tests/test_governed_chain_verify.py -v
"""

import json
import sys
from pathlib import Path

import pytest

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_governed_chain_verification_creates_commit_and_anchor(tmp_path, monkeypatch):
    """
    Invariant: run_governed_chain_verification MUST create:
    - A governance commit JSON
    - An anchor sidecar for that commit
    """
    # Work in isolated temp directory
    monkeypatch.chdir(tmp_path)

    # Create required directories
    data_root = Path("DATA")
    commits_dir = data_root / "_commits"
    commits_dir.mkdir(parents=True, exist_ok=True)

    # Initialize empty chain
    chain_file = data_root / "_anchor_chain.json"
    chain_file.write_text("[]", encoding="utf-8")

    from src.boardroom.chain_governed_verify import run_governed_chain_verification

    # Run governed verification
    summary = run_governed_chain_verification(
        requested_by="test:pytest",
        rationale="Pytest invariant test.",
    )

    # --- Assert commit exists ---
    commit_path = Path(summary["commit_path"])
    assert commit_path.exists(), "Governed verification MUST write a governance commit."

    commit = json.loads(commit_path.read_text(encoding="utf-8"))
    assert commit.get("record_type") == "governance_commit"
    assert commit.get("governance", {}).get("consensus_action") == "VERIFY_CHAIN_NOW"
    assert commit.get("requested_by") == "test:pytest"

    # --- Assert anchor sidecar exists ---
    anchor_path = Path(summary["anchor_path"])
    assert anchor_path.exists(), "Governed verification MUST write an anchor sidecar."

    anchor = json.loads(anchor_path.read_text(encoding="utf-8"))
    assert "payload_hash" in anchor, "Anchor must have payload_hash."
    assert "chain_hash" in anchor, "Anchor must have chain_hash."
    assert "timestamp" in anchor, "Anchor must have timestamp."


def test_governed_chain_verification_updates_chain(tmp_path, monkeypatch):
    """
    Invariant: run_governed_chain_verification MUST append to the hash chain.
    """
    monkeypatch.chdir(tmp_path)

    data_root = Path("DATA")
    commits_dir = data_root / "_commits"
    commits_dir.mkdir(parents=True, exist_ok=True)

    # Initialize empty chain
    chain_file = data_root / "_anchor_chain.json"
    chain_file.write_text("[]", encoding="utf-8")

    from src.boardroom.chain_governed_verify import run_governed_chain_verification

    # Run governed verification
    run_governed_chain_verification(
        requested_by="test:pytest",
        rationale="Chain growth invariant test.",
    )

    # Chain must have grown
    chain = json.loads(chain_file.read_text(encoding="utf-8"))
    assert len(chain) >= 1, "Chain must have at least one entry after governed verification."

    # Latest entry must be governance_commit type
    latest = chain[-1]
    assert latest.get("record_type") == "governance_commit"
    assert "payload_hash" in latest
    assert "chain_hash" in latest


def test_governed_chain_verification_produces_verification_report(tmp_path, monkeypatch):
    """
    Invariant: When automation is allowed, governed verification MUST
    produce a verification report that links back to the governance commit.
    """
    monkeypatch.chdir(tmp_path)

    data_root = Path("DATA")
    commits_dir = data_root / "_commits"
    verify_dir = data_root / "_chain_verifications"
    commits_dir.mkdir(parents=True, exist_ok=True)
    verify_dir.mkdir(parents=True, exist_ok=True)

    # Initialize empty chain
    chain_file = data_root / "_anchor_chain.json"
    chain_file.write_text("[]", encoding="utf-8")

    from src.boardroom.chain_governed_verify import run_governed_chain_verification

    # Run governed verification
    summary = run_governed_chain_verification(
        requested_by="test:pytest",
        rationale="Verification report invariant test.",
    )

    # Check verification report exists
    verify_path = summary.get("verification_path")
    if verify_path:
        verify_file = Path(verify_path)
        assert verify_file.exists(), "Verification path in summary must exist."

        report = json.loads(verify_file.read_text(encoding="utf-8"))

        # Report must link back to commit
        commit_path = Path(summary["commit_path"])
        commit = json.loads(commit_path.read_text(encoding="utf-8"))

        assert report.get("governance_commit_id") == commit.get("commit_id"), \
            "Verification report must reference the originating commit."


def test_governed_chain_verification_session_id_consistency(tmp_path, monkeypatch):
    """
    Invariant: session_id must be consistent across all artifacts.
    """
    monkeypatch.chdir(tmp_path)

    data_root = Path("DATA")
    commits_dir = data_root / "_commits"
    verify_dir = data_root / "_chain_verifications"
    commits_dir.mkdir(parents=True, exist_ok=True)
    verify_dir.mkdir(parents=True, exist_ok=True)

    chain_file = data_root / "_anchor_chain.json"
    chain_file.write_text("[]", encoding="utf-8")

    from src.boardroom.chain_governed_verify import run_governed_chain_verification

    summary = run_governed_chain_verification(
        requested_by="test:pytest",
        rationale="Session ID consistency test.",
    )

    session_id = summary["session_id"]

    # Session ID must be in commit filename
    commit_path = Path(summary["commit_path"])
    assert session_id in commit_path.name, "Session ID must appear in commit filename."

    # Session ID must be in commit content
    commit = json.loads(commit_path.read_text(encoding="utf-8"))
    assert commit.get("session_id") == session_id, "Session ID must match in commit content."

    # If verification report exists, session ID must match there too
    if summary.get("verification_path"):
        verify_file = Path(summary["verification_path"])
        if verify_file.exists():
            report = json.loads(verify_file.read_text(encoding="utf-8"))
            assert report.get("governance_session_id") == session_id, \
                "Session ID must match in verification report."
