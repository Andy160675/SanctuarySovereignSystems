"""
Planner Risk Gating Unit Tests
==============================

Tests for the risk gating logic per Risk Governance Addendum:
- HIGH risk → REJECTED (mandatory block)
- UNKNOWN risk → PENDING_HUMAN_AUTH (human authorization required)
- LOW/MEDIUM risk → APPROVED (proceed with execution)
- Timeout (None) → PENDING_HUMAN_AUTH (fail-safe to human oversight)

Run with: pytest tests/planner/test_risk_gating.py -v
"""

import json
import sys
from pathlib import Path
from typing import List, Dict, Any
from unittest.mock import Mock

import pytest

# Add agents to path for import
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "agents" / "planner"))

from agent import apply_risk_gate, PlanStatus


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def ledger_calls() -> Dict[str, Any]:
    """Capture ledger write calls in a simple structure."""
    calls: List[dict] = []

    def _write(entry: dict):
        # Simulate serialization boundary
        calls.append(json.loads(json.dumps(entry)))

    mock = Mock(side_effect=_write)
    return {"calls": calls, "mock": mock}


def _extract_event_types(calls: list) -> list:
    return [c.get("event_type") for c in calls]


# =============================================================================
# Test: apply_risk_gate function
# =============================================================================

class TestApplyRiskGate:
    """Test the core risk gating decision function."""

    def test_high_risk_returns_rejected(self):
        """HIGH risk must return REJECTED status."""
        assessment = {"risk_level": "HIGH", "reason": "test"}
        result = apply_risk_gate(assessment)
        assert result == PlanStatus.REJECTED

    def test_unknown_risk_returns_pending_human_auth(self):
        """UNKNOWN risk must return PENDING_HUMAN_AUTH status."""
        assessment = {"risk_level": "UNKNOWN", "reason": "test"}
        result = apply_risk_gate(assessment)
        assert result == PlanStatus.PENDING_HUMAN_AUTH

    def test_low_risk_returns_approved(self):
        """LOW risk must return APPROVED status."""
        assessment = {"risk_level": "LOW", "reason": "test"}
        result = apply_risk_gate(assessment)
        assert result == PlanStatus.APPROVED

    def test_medium_risk_returns_approved(self):
        """MEDIUM risk must return APPROVED status."""
        assessment = {"risk_level": "MEDIUM", "reason": "test"}
        result = apply_risk_gate(assessment)
        assert result == PlanStatus.APPROVED

    def test_missing_risk_level_defaults_to_pending(self):
        """Missing risk_level should default to UNKNOWN → PENDING_HUMAN_AUTH."""
        assessment = {"reason": "no risk level"}
        result = apply_risk_gate(assessment)
        assert result == PlanStatus.PENDING_HUMAN_AUTH

    def test_case_insensitive_risk_level(self):
        """Risk level should be case-insensitive."""
        assert apply_risk_gate({"risk_level": "high"}) == PlanStatus.REJECTED
        assert apply_risk_gate({"risk_level": "High"}) == PlanStatus.REJECTED
        assert apply_risk_gate({"risk_level": "LOW"}) == PlanStatus.APPROVED
        assert apply_risk_gate({"risk_level": "low"}) == PlanStatus.APPROVED


# =============================================================================
# Test: Full decision flow with ledger logging
# =============================================================================

def decide_plan_fate_sync(
    mission_id: str,
    objective: str,
    risk_assessment: Dict[str, Any] | None,
    write_to_ledger: Any = None,
) -> Dict[str, Any]:
    """
    Synchronous wrapper for testing risk gating decision logic.
    Mirrors the production async flow but is testable.
    """
    if write_to_ledger is None:
        write_to_ledger = lambda x: None

    # Handle timeout (no assessment received)
    if risk_assessment is None:
        write_to_ledger({
            "event_type": "risk_assessment_timeout",
            "mission_id": mission_id,
            "objective": objective,
            "risk_level": None,
        })
        return {
            "status": "PENDING_HUMAN_AUTH",
            "risk_level": None,
            "mission_id": mission_id,
            "reason": "Risk assessment timeout - requires human authorization"
        }

    risk_level = risk_assessment.get("risk_level", "UNKNOWN").upper()
    reason = risk_assessment.get("reason", risk_assessment.get("rationale", "No reason provided"))

    # HIGH risk → REJECTED
    if risk_level == "HIGH":
        write_to_ledger({
            "event_type": "plan_rejected",
            "mission_id": mission_id,
            "objective": objective,
            "risk_level": "HIGH",
            "reason": reason,
        })
        return {
            "status": "REJECTED",
            "risk_level": "HIGH",
            "mission_id": mission_id,
            "reason": reason
        }

    # UNKNOWN risk → PENDING_HUMAN_AUTH
    if risk_level == "UNKNOWN":
        write_to_ledger({
            "event_type": "plan_hold_unknown_risk",
            "mission_id": mission_id,
            "objective": objective,
            "risk_level": "UNKNOWN",
            "reason": reason,
        })
        return {
            "status": "PENDING_HUMAN_AUTH",
            "risk_level": "UNKNOWN",
            "mission_id": mission_id,
            "reason": reason
        }

    # LOW or MEDIUM → APPROVED
    write_to_ledger({
        "event_type": "plan_approved",
        "mission_id": mission_id,
        "objective": objective,
        "risk_level": risk_level,
        "reason": reason,
    })
    return {
        "status": "APPROVED",
        "risk_level": risk_level,
        "mission_id": mission_id,
        "reason": reason
    }


class TestDecidePlanFate:
    """Test the full decision flow with ledger logging."""

    def test_high_risk_blocks_and_logs_rejection(self, ledger_calls):
        """HIGH risk must block execution and log plan_rejected."""
        mission_id = "mission-123"
        objective = "Test mission that should be high risk"
        assessment = {
            "risk_level": "HIGH",
            "reason": "test high risk scenario",
        }

        result = decide_plan_fate_sync(
            mission_id=mission_id,
            objective=objective,
            risk_assessment=assessment,
            write_to_ledger=ledger_calls["mock"],
        )

        # Verify status
        assert result["status"] == "REJECTED"
        assert result["risk_level"] == "HIGH"
        assert result["mission_id"] == mission_id

        # Verify ledger events
        events = ledger_calls["calls"]
        event_types = _extract_event_types(events)

        assert "plan_rejected" in event_types

        rejected_entries = [e for e in events if e.get("event_type") == "plan_rejected"]
        assert len(rejected_entries) >= 1
        entry = rejected_entries[0]
        assert entry.get("mission_id") == mission_id
        assert entry.get("risk_level") == "HIGH"

    def test_unknown_risk_requires_human_and_logs_hold(self, ledger_calls):
        """UNKNOWN risk must require human auth and log plan_hold_unknown_risk."""
        mission_id = "mission-unknown"
        objective = "Ambiguous mission"
        assessment = {
            "risk_level": "UNKNOWN",
            "reason": "insufficient info",
        }

        result = decide_plan_fate_sync(
            mission_id=mission_id,
            objective=objective,
            risk_assessment=assessment,
            write_to_ledger=ledger_calls["mock"],
        )

        assert result["status"] == "PENDING_HUMAN_AUTH"
        assert result["risk_level"] == "UNKNOWN"
        assert result["mission_id"] == mission_id

        events = ledger_calls["calls"]
        event_types = _extract_event_types(events)

        assert "plan_hold_unknown_risk" in event_types

        hold_entries = [e for e in events if e.get("event_type") == "plan_hold_unknown_risk"]
        assert len(hold_entries) >= 1
        entry = hold_entries[0]
        assert entry.get("mission_id") == mission_id
        assert entry.get("risk_level") == "UNKNOWN"

    def test_timeout_yields_pending_and_logs_timeout(self, ledger_calls):
        """Timeout (None assessment) must require human auth and log timeout."""
        mission_id = "mission-timeout"
        objective = "Mission where confessor times out"

        result = decide_plan_fate_sync(
            mission_id=mission_id,
            objective=objective,
            risk_assessment=None,
            write_to_ledger=ledger_calls["mock"],
        )

        assert result["status"] == "PENDING_HUMAN_AUTH"
        assert result["risk_level"] is None
        assert result["mission_id"] == mission_id

        events = ledger_calls["calls"]
        event_types = _extract_event_types(events)

        assert "risk_assessment_timeout" in event_types

        timeout_entries = [e for e in events if e.get("event_type") == "risk_assessment_timeout"]
        assert len(timeout_entries) >= 1
        entry = timeout_entries[0]
        assert entry.get("mission_id") == mission_id

    @pytest.mark.parametrize("risk_level", ["LOW", "MEDIUM"])
    def test_low_and_medium_risk_are_approved_and_logged(self, risk_level, ledger_calls):
        """LOW and MEDIUM risk must be approved and log plan_approved."""
        mission_id = f"mission-{risk_level.lower()}"
        objective = "Benign mission"
        assessment = {
            "risk_level": risk_level,
            "reason": "benign test case",
        }

        result = decide_plan_fate_sync(
            mission_id=mission_id,
            objective=objective,
            risk_assessment=assessment,
            write_to_ledger=ledger_calls["mock"],
        )

        assert result["status"] == "APPROVED"
        assert result["risk_level"] == risk_level
        assert result["mission_id"] == mission_id

        events = ledger_calls["calls"]
        event_types = _extract_event_types(events)

        assert "plan_approved" in event_types


# =============================================================================
# Test: No execution on HIGH risk
# =============================================================================

class TestNoExecutionOnHighRisk:
    """Ensure HIGH risk missions never reach execution state."""

    def test_high_risk_never_triggers_execution(self, ledger_calls):
        """HIGH risk must never produce task_started events."""
        mission_id = "mission-high-no-exec"
        assessment = {"risk_level": "HIGH", "reason": "dangerous"}

        result = decide_plan_fate_sync(
            mission_id=mission_id,
            objective="dangerous operation",
            risk_assessment=assessment,
            write_to_ledger=ledger_calls["mock"],
        )

        # Verify no execution events
        events = ledger_calls["calls"]
        event_types = _extract_event_types(events)

        assert "task_started" not in event_types
        assert "plan_execution_started" not in event_types
        assert result["status"] == "REJECTED"
