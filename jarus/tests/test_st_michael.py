# =============================================================================
# ST MICHAEL — Test Suite
# =============================================================================
# Tests for the Adjudication Gate and Proof-of-Refusal logging.
#
# Run with: pytest tests/test_st_michael.py -v
# =============================================================================

import json
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from st_michael.adjudication import AdjudicationGate, QuorumStatus, VoteResult
from st_michael.refusal_log import RefusalLogger, ProofOfRefusal


class TestAdjudicationGate:
    """Tests for the 5-of-7 quorum voting system."""

    @pytest.fixture
    def gate(self, tmp_path):
        """Create a gate with temporary storage."""
        return AdjudicationGate(storage_path=tmp_path / "override_proofs")

    def test_create_proposal(self, gate):
        """Test creating a new override proposal."""
        result = gate.create_proposal("PROP-001", "Test override")

        assert result.proposal_id == "PROP-001"
        assert result.status == QuorumStatus.PENDING
        assert result.votes_for == 0
        assert result.votes_against == 0
        assert result.total_votes == 0
        assert result.quorum_threshold == 5
        assert result.total_identities == 7

    def test_cast_single_vote(self, gate):
        """Test casting a single vote."""
        gate.create_proposal("PROP-002", "Single vote test")

        result = gate.cast_vote(
            proposal_id="PROP-002",
            identity_id="voter-1",
            approve=True,
            signature="sig-123",
            reason="Approved for testing",
        )

        assert result.votes_for == 1
        assert result.votes_against == 0
        assert result.total_votes == 1
        assert result.status == QuorumStatus.PENDING

    def test_quorum_achieved_at_five_votes(self, gate):
        """Test that quorum is achieved with 5 approve votes."""
        gate.create_proposal("PROP-003", "Quorum test")

        # Cast 5 approving votes
        for i in range(5):
            result = gate.cast_vote(
                proposal_id="PROP-003",
                identity_id=f"voter-{i}",
                approve=True,
                signature=f"sig-{i}",
            )

        assert result.votes_for == 5
        assert result.status == QuorumStatus.ACHIEVED
        assert result.cooling_ends_at is not None

    def test_quorum_rejected_when_impossible(self, gate):
        """Test that proposal is rejected when quorum becomes impossible."""
        gate.create_proposal("PROP-004", "Rejection test")

        # Cast 3 rejecting votes (means max 4 approvals possible)
        for i in range(3):
            result = gate.cast_vote(
                proposal_id="PROP-004",
                identity_id=f"voter-{i}",
                approve=False,
                signature=f"sig-{i}",
            )

        assert result.votes_against == 3
        assert result.status == QuorumStatus.REJECTED

    def test_duplicate_vote_rejected(self, gate):
        """Test that the same identity cannot vote twice."""
        gate.create_proposal("PROP-005", "Duplicate test")

        gate.cast_vote(
            proposal_id="PROP-005",
            identity_id="voter-1",
            approve=True,
            signature="sig-1",
        )

        with pytest.raises(ValueError, match="already voted"):
            gate.cast_vote(
                proposal_id="PROP-005",
                identity_id="voter-1",
                approve=False,
                signature="sig-1-again",
            )

    def test_vote_on_nonexistent_proposal(self, gate):
        """Test that voting on nonexistent proposal raises error."""
        with pytest.raises(ValueError, match="not found"):
            gate.cast_vote(
                proposal_id="PROP-FAKE",
                identity_id="voter-1",
                approve=True,
                signature="sig-1",
            )

    def test_cannot_execute_before_cooling(self, gate):
        """Test that override cannot execute during cooling period."""
        gate.create_proposal("PROP-006", "Cooling test")

        # Achieve quorum
        for i in range(5):
            gate.cast_vote(
                proposal_id="PROP-006",
                identity_id=f"voter-{i}",
                approve=True,
                signature=f"sig-{i}",
            )

        # Should not be executable yet (72h cooling)
        assert not gate.can_execute_override("PROP-006")

    def test_vote_result_serialization(self, gate):
        """Test that VoteResult serializes to JSON correctly."""
        gate.create_proposal("PROP-007", "Serialization test")
        result = gate.cast_vote(
            proposal_id="PROP-007",
            identity_id="voter-1",
            approve=True,
            signature="sig-1",
        )

        json_str = result.to_json()
        data = json.loads(json_str)

        assert data["proposal_id"] == "PROP-007"
        assert data["status"] == "pending"
        assert len(data["votes"]) == 1


class TestRefusalLogger:
    """Tests for the Proof-of-Refusal logging system."""

    @pytest.fixture
    def logger(self, tmp_path):
        """Create a logger with temporary storage."""
        return RefusalLogger(log_path=tmp_path / "refusals")

    def test_log_refusal(self, logger):
        """Test logging a basic refusal."""
        proof = logger.log_refusal(
            action_type="test_refusal",
            action_details={"test": "data"},
            reason="Test reason",
            requestor_id="test-user",
        )

        assert proof.action_type == "test_refusal"
        assert proof.reason == "Test reason"
        assert proof.requestor_id == "test-user"
        assert proof.refusal_hash  # Should be computed
        assert proof.evidence_hash  # Should be computed

    def test_log_override_failure(self, logger):
        """Test logging a quorum failure."""
        proof = logger.log_override_failure(
            proposal_id="PROP-FAIL",
            votes_for=3,
            votes_required=5,
            requestor_id="attacker",
        )

        assert proof.action_type == "quorum_failure"
        assert proof.action_details["shortfall"] == 2
        assert "3/5" in proof.reason

    def test_log_cooling_violation(self, logger):
        """Test logging a cooling period violation attempt."""
        proof = logger.log_cooling_violation(
            proposal_id="PROP-EAGER",
            cooling_ends_at="2025-12-06T12:00:00",
            attempted_at="2025-12-04T12:00:00",
            requestor_id="impatient-user",
        )

        assert proof.action_type == "cooling_violation"
        assert "72h cooling" in proof.reason

    def test_refusal_count(self, logger):
        """Test counting refusals."""
        assert logger.get_refusal_count() == 0

        logger.log_refusal("test", {}, "reason 1")
        logger.log_refusal("test", {}, "reason 2")
        logger.log_refusal("test", {}, "reason 3")

        assert logger.get_refusal_count() == 3

    def test_get_recent_refusals(self, logger):
        """Test retrieving recent refusals."""
        for i in range(5):
            logger.log_refusal("test", {"index": i}, f"reason {i}")

        recent = logger.get_recent_refusals(limit=3)
        assert len(recent) == 3

    def test_refusal_hash_is_deterministic(self, logger):
        """Test that same input produces same hash."""
        # Create two proofs with same content
        proof1 = ProofOfRefusal(
            refusal_id="REF-1",
            timestamp="2025-12-03T12:00:00",
            action_type="test",
            action_details={"key": "value"},
            reason="test reason",
            requestor_id="user-1",
            evidence_hash="abc123",
        )

        proof2 = ProofOfRefusal(
            refusal_id="REF-1",
            timestamp="2025-12-03T12:00:00",
            action_type="test",
            action_details={"key": "value"},
            reason="test reason",
            requestor_id="user-1",
            evidence_hash="abc123",
        )

        assert proof1.refusal_hash == proof2.refusal_hash

    def test_proof_to_json(self, logger):
        """Test that ProofOfRefusal serializes correctly."""
        proof = logger.log_refusal(
            action_type="serialization_test",
            action_details={"nested": {"data": [1, 2, 3]}},
            reason="Testing JSON output",
        )

        json_str = proof.to_json()
        data = json.loads(json_str)

        assert data["action_type"] == "serialization_test"
        assert data["action_details"]["nested"]["data"] == [1, 2, 3]


class TestIntegration:
    """Integration tests for ST MICHAEL components."""

    def test_full_quorum_workflow(self, tmp_path):
        """Test complete workflow: proposal → votes → refusal logging."""
        gate = AdjudicationGate(storage_path=tmp_path / "proofs")
        logger = RefusalLogger(log_path=tmp_path / "refusals")

        # Create proposal
        gate.create_proposal("INTEG-001", "Integration test override")

        # Cast 4 approving votes (not enough for quorum)
        for i in range(4):
            gate.cast_vote(
                proposal_id="INTEG-001",
                identity_id=f"voter-{i}",
                approve=True,
                signature=f"sig-{i}",
            )

        # Check status
        result = gate.check_status("INTEG-001")
        assert result.status == QuorumStatus.PENDING
        assert result.votes_for == 4

        # Log the failed attempt
        proof = logger.log_override_failure(
            proposal_id="INTEG-001",
            votes_for=4,
            votes_required=5,
        )

        assert proof.action_type == "quorum_failure"
        assert logger.get_refusal_count() == 1
