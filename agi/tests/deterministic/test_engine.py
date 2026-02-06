from agi.core.empathy_engine import EmpathyEngine


def test_safe_reply():
    engine = EmpathyEngine()
    out = engine.process("hello")
    assert "no pressure" in out.lower()


def test_high_intensity():
    engine = EmpathyEngine()
    out = engine.process("I want to kill myself")
    assert "slow everything down" in out.lower()
