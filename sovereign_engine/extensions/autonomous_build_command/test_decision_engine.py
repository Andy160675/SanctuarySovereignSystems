import pytest
from sovereign_engine.extensions.autonomous_build_command.decision_engine import DecisionEngine, ProposedAction, RiskLevel

def test_score_action():
    engine = DecisionEngine(threshold=70)
    low_risk = ProposedAction("1", "low", 10, {})
    med_risk = ProposedAction("2", "med", 50, {})
    high_risk = ProposedAction("3", "high", 80, {})
    
    assert engine.score_action(low_risk) == RiskLevel.LOW
    assert engine.score_action(med_risk) == RiskLevel.MEDIUM
    assert engine.score_action(high_risk) == RiskLevel.HIGH

def test_select_action():
    engine = DecisionEngine(threshold=70)
    actions = [
        ProposedAction("1", "med", 50, {}),
        ProposedAction("2", "low", 10, {}),
        ProposedAction("3", "high", 80, {})
    ]
    selected = engine.select_action(actions)
    assert selected.action_id == "2"

def test_select_action_none_below_threshold():
    engine = DecisionEngine(threshold=30)
    actions = [
        ProposedAction("1", "med", 50, {}),
        ProposedAction("3", "high", 80, {})
    ]
    selected = engine.select_action(actions)
    assert selected is None
