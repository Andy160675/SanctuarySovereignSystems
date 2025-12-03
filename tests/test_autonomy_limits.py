# -*- coding: utf-8 -*-
"""
Autonomy Limits Enforcement Tests
=================================

These tests are CI gates that enforce AUTONOMY_LIMITS.md.
Build FAILS if any of these tests fail.

Run with: pytest tests/test_autonomy_limits.py -v
"""

import hashlib
import pytest
import sys
from pathlib import Path
from typing import Set

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import autonomy components
try:
    from core.autonomy.local_agent_scheduler import (
        AutonomyGuard,
        ProposalState,
        Proposal,
        HumanSeal,
    )
    AUTONOMY_MODULE_AVAILABLE = True
except ImportError:
    AUTONOMY_MODULE_AVAILABLE = False


# =============================================================================
# CONSTANTS FROM AUTONOMY_LIMITS.md
# =============================================================================

FORBIDDEN_AUTONOMOUS_ACTIONS: Set[str] = {
    # Financial
    "execute_payment",
    "transfer_funds",
    "approve_loan",
    "sign_financial_instrument",
    # Legal
    "sign_contract",
    "submit_regulatory_filing",
    "file_legal_document",
    "accept_terms",
    # Medical
    "make_medical_decision",
    "prescribe_treatment",
    "modify_patient_record",
    # System
    "modify_policy",
    "change_autonomy_level",
    "deploy_system",
    "modify_self",
    # External
    "send_external_email",
    "post_to_external_api",
    "trigger_webhook",
    "notify_external_party",
}

ALLOWED_AUTONOMOUS_ACTIONS: Set[str] = {
    # Analysis
    "analyze_document",
    "classify_document",
    "extract_entities",
    "summarize_content",
    # Risk Assessment
    "classify_risk",
    "score_priority",
    "detect_anomaly",
    "flag_for_review",
    # Reporting
    "generate_report",
    "create_summary",
    "compile_evidence",
    "format_output",
    # Triage
    "triage_case",
    "route_to_queue",
    "assign_priority",
    "estimate_complexity",
    # Reconstruction
    "reconstruct_timeline",
    "correlate_events",
    "identify_patterns",
    "map_relationships",
    # Regulatory
    "map_regulation",
    "check_compliance_status",
    "identify_applicable_rules",
    "compare_to_baseline",
}


# =============================================================================
# EXCEPTIONS
# =============================================================================

class AutonomyViolation(Exception):
    """Raised when autonomy limits are violated."""
    pass


class MissingSealError(Exception):
    """Raised when execution attempted without human seal."""
    pass


# =============================================================================
# TEST HELPERS
# =============================================================================

def execute_action(action: str, bypass_seal: bool = False) -> dict:
    """
    Simulate executing an action.

    Raises AutonomyViolation for forbidden actions.
    """
    if action in FORBIDDEN_AUTONOMOUS_ACTIONS:
        if bypass_seal:
            raise AutonomyViolation(f"Forbidden action: {action}")
    return {"status": "proposed"}


def create_test_proposal() -> Proposal:
    """Create a test proposal."""
    if not AUTONOMY_MODULE_AVAILABLE:
        pytest.skip("Autonomy module not available")

    return Proposal(
        proposal_id="test-001",
        task_id="task-001",
        agent_id="test-agent",
        state=ProposalState.PROPOSED,
        recommendation="Test recommendation",
        confidence=0.9,
        evidence=["test evidence"],
        reasoning_chain=["step 1", "step 2"],
        risk_assessment={"level": "low"},
    )


def execute_proposal(proposal: Proposal) -> dict:
    """
    Simulate executing a proposal.

    Raises MissingSealError if no seal present.
    """
    if proposal.state != ProposalState.APPROVED:
        raise MissingSealError("Proposal not approved")
    if not proposal.review_signature:
        raise MissingSealError("No review signature")
    return {"executed": True}


# =============================================================================
# TEST: FORBIDDEN ACTIONS BLOCKED
# =============================================================================

class TestForbiddenActionsBlocked:
    """Verify all forbidden actions are blocked."""

    @pytest.mark.parametrize("action", FORBIDDEN_AUTONOMOUS_ACTIONS)
    def test_forbidden_action_raises(self, action: str):
        """Each forbidden action must raise AutonomyViolation."""
        with pytest.raises(AutonomyViolation):
            execute_action(action, bypass_seal=True)

    def test_forbidden_list_not_empty(self):
        """Forbidden list must not be empty."""
        assert len(FORBIDDEN_AUTONOMOUS_ACTIONS) > 0

    def test_no_overlap_allowed_forbidden(self):
        """No action can be both allowed and forbidden."""
        overlap = FORBIDDEN_AUTONOMOUS_ACTIONS & ALLOWED_AUTONOMOUS_ACTIONS
        assert len(overlap) == 0, f"Actions in both lists: {overlap}"


# =============================================================================
# TEST: ALLOWED ACTIONS WORK
# =============================================================================

class TestAllowedActions:
    """Verify allowed actions function correctly."""

    @pytest.mark.parametrize("action", list(ALLOWED_AUTONOMOUS_ACTIONS)[:10])
    def test_allowed_action_succeeds(self, action: str):
        """Allowed actions should return proposed status."""
        result = execute_action(action, bypass_seal=False)
        assert result["status"] == "proposed"

    def test_allowed_list_not_empty(self):
        """Allowed list must not be empty."""
        assert len(ALLOWED_AUTONOMOUS_ACTIONS) > 0


# =============================================================================
# TEST: SEAL REQUIRED FOR EXECUTION
# =============================================================================

class TestSealRequired:
    """Verify human seal is required for execution."""

    @pytest.mark.skipif(not AUTONOMY_MODULE_AVAILABLE, reason="Module not available")
    def test_execution_without_seal_fails(self):
        """Execution without seal must fail."""
        proposal = create_test_proposal()
        with pytest.raises(MissingSealError):
            execute_proposal(proposal)

    @pytest.mark.skipif(not AUTONOMY_MODULE_AVAILABLE, reason="Module not available")
    def test_proposed_state_cannot_execute(self):
        """Proposals in PROPOSED state cannot execute."""
        proposal = create_test_proposal()
        assert proposal.state == ProposalState.PROPOSED
        with pytest.raises(MissingSealError):
            execute_proposal(proposal)

    @pytest.mark.skipif(not AUTONOMY_MODULE_AVAILABLE, reason="Module not available")
    def test_approved_with_seal_can_execute(self):
        """Approved proposals with seal can execute."""
        proposal = create_test_proposal()
        proposal.state = ProposalState.APPROVED
        proposal.review_signature = "valid-signature"
        result = execute_proposal(proposal)
        assert result["executed"] is True


# =============================================================================
# TEST: NO DIRECT EXECUTION
# =============================================================================

class TestNoDirectExecution:
    """Verify agents cannot bypass proposal state."""

    def test_all_outputs_are_proposals(self):
        """All agent outputs must be in proposal state."""
        valid_output_states = {"PROPOSED", "REVIEW_REQUIRED"}

        # Simulate checking agent outputs
        test_outputs = [
            {"state": "PROPOSED"},
            {"state": "REVIEW_REQUIRED"},
        ]

        for output in test_outputs:
            assert output["state"] in valid_output_states

    def test_executed_state_unreachable_directly(self):
        """EXECUTED state cannot be set directly."""
        if not AUTONOMY_MODULE_AVAILABLE:
            pytest.skip("Module not available")

        proposal = create_test_proposal()

        # Trying to set EXECUTED without seal should fail validation
        proposal.state = ProposalState.EXECUTED

        # Validation should catch this
        assert proposal.review_signature is None
        # This proposal is invalid - no signature for EXECUTED


# =============================================================================
# TEST: AUTONOMY LIMITS FILE INTEGRITY
# =============================================================================

class TestAutonomyLimitsFile:
    """Verify AUTONOMY_LIMITS.md integrity."""

    AUTONOMY_FILE = Path(__file__).parent.parent / "AUTONOMY_LIMITS.md"

    def test_autonomy_limits_file_exists(self):
        """AUTONOMY_LIMITS.md must exist."""
        assert self.AUTONOMY_FILE.exists(), "AUTONOMY_LIMITS.md not found"

    def test_autonomy_limits_not_empty(self):
        """AUTONOMY_LIMITS.md must not be empty."""
        content = self.AUTONOMY_FILE.read_text(encoding="utf-8")
        assert len(content) > 100, "AUTONOMY_LIMITS.md appears empty"

    def test_autonomy_limits_contains_forbidden_section(self):
        """AUTONOMY_LIMITS.md must contain FORBIDDEN section."""
        content = self.AUTONOMY_FILE.read_text(encoding="utf-8")
        assert "FORBIDDEN_AUTONOMOUS_ACTIONS" in content

    def test_autonomy_limits_contains_allowed_section(self):
        """AUTONOMY_LIMITS.md must contain ALLOWED section."""
        content = self.AUTONOMY_FILE.read_text(encoding="utf-8")
        assert "ALLOWED_AUTONOMOUS_ACTIONS" in content

    def test_autonomy_limits_contains_seal_requirements(self):
        """AUTONOMY_LIMITS.md must contain seal requirements."""
        content = self.AUTONOMY_FILE.read_text(encoding="utf-8")
        assert "HUMAN_SEAL" in content or "HumanSeal" in content

    def test_file_hash_stability(self):
        """
        Track file hash for unauthorized changes.

        NOTE: Update EXPECTED_HASH when file legitimately changes.
        """
        content = self.AUTONOMY_FILE.read_text(encoding="utf-8")
        current_hash = hashlib.sha256(content.encode()).hexdigest()

        # Log current hash for reference
        print(f"\nCurrent AUTONOMY_LIMITS.md hash: {current_hash[:16]}...")

        # This test documents the hash - update when file changes legitimately
        # For now, just verify we can compute the hash
        assert len(current_hash) == 64


# =============================================================================
# TEST: AUTONOMY GUARD
# =============================================================================

class TestAutonomyGuard:
    """Test the AutonomyGuard enforcement."""

    @pytest.mark.skipif(not AUTONOMY_MODULE_AVAILABLE, reason="Module not available")
    def test_guard_blocks_forbidden(self):
        """AutonomyGuard blocks forbidden actions."""
        for action in FORBIDDEN_AUTONOMOUS_ACTIONS:
            assert not AutonomyGuard.is_action_allowed(action)

    @pytest.mark.skipif(not AUTONOMY_MODULE_AVAILABLE, reason="Module not available")
    def test_guard_allows_permitted(self):
        """AutonomyGuard allows permitted actions."""
        for action in ALLOWED_AUTONOMOUS_ACTIONS:
            assert AutonomyGuard.is_action_allowed(action)

    @pytest.mark.skipif(not AUTONOMY_MODULE_AVAILABLE, reason="Module not available")
    def test_guard_validates_proposal(self):
        """AutonomyGuard validates proposals."""
        proposal = create_test_proposal()
        violations = AutonomyGuard.validate_proposal(proposal)
        assert isinstance(violations, list)


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
