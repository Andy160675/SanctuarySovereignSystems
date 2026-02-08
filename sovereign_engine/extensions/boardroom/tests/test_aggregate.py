from sovereign_engine.extensions.boardroom.models import AgentVerdict, Vote
from sovereign_engine.extensions.boardroom.engine import BoardroomEngine

class DummyClient:
    model = "dummy"

def make(role, vote, conf):
    return AgentVerdict(role=role, vote=vote, confidence=conf, reasoning="", risks=[], actions=[], constitutional_flags=[])

def test_veto_halts():
    eng = BoardroomEngine(DummyClient())
    agents = [
        make("Auditor", Vote.HALT, 0.9),
        make("Sentinel", Vote.APPROVE, 0.9),
    ] + [make(r, Vote.APPROVE, 0.8) for r in [
        "Architect","Engineer","Advocate","Steward","Scholar","Diplomat","Judge","Explorer","Guardian","Catalyst","Witness"
    ]]
    out = eng._aggregate(agents, kernel_flags=[])
    assert out.final == Vote.HALT
