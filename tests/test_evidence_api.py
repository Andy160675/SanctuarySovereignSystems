from pathlib import Path
import json
import pytest
import sys
import os

# Add project root to sys.path
sys.path.append(os.getcwd())

from src.core.evidence.api import EvidenceChain, ChainIntegrityError


def test_append_and_verify(tmp_path: Path):
    p = tmp_path / "chain.jsonl"
    chain = EvidenceChain(p)
    r1 = chain.append("merge_validation", {"ok": True}, "governance-core/v1.0")
    r2 = chain.append("policy_execution", {"policy_id": "P-1"}, "policy-compiler/v1.0")

    assert r1.previous_id == "0" * 64
    assert r2.previous_id == r1.id
    assert chain.verify_chain() is True


def test_tamper_detection_content_hash(tmp_path: Path):
    p = tmp_path / "chain.jsonl"
    chain = EvidenceChain(p)
    chain.append("merge_validation", {"ok": True}, "governance-core/v1.0")

    # Tamper with file content directly
    lines = p.read_text(encoding="utf-8").splitlines()
    obj = json.loads(lines[0])
    obj["content"]["ok"] = False  # breaks content hash
    lines[0] = json.dumps(obj)
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")

    try:
        EvidenceChain(p)
        assert False, "Expected ChainIntegrityError due to tamper"
    except ChainIntegrityError:
        assert True


def test_chain_link_break_detection(tmp_path: Path):
    p = tmp_path / "chain.jsonl"
    chain = EvidenceChain(p)
    chain.append("a", {"x": 1}, "v1")
    chain.append("b", {"y": 2}, "v1")

    lines = p.read_text(encoding="utf-8").splitlines()
    second = json.loads(lines[1])
    second["previous_id"] = "f" * 64  # invalid previous link
    lines[1] = json.dumps(second)
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")

    try:
        EvidenceChain(p)
        assert False, "Expected ChainIntegrityError due to link mismatch"
    except ChainIntegrityError:
        assert True
