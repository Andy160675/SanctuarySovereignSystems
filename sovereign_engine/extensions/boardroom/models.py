from dataclasses import dataclass, asdict
from enum import Enum
from typing import List, Dict, Any


class Vote(str, Enum):
    APPROVE = "APPROVE"
    REJECT = "REJECT"
    AMEND = "AMEND"
    ABSTAIN = "ABSTAIN"
    HALT = "HALT"


@dataclass
class AgentVerdict:
    role: str
    vote: Vote
    confidence: float
    reasoning: str
    risks: List[str]
    actions: List[str]
    constitutional_flags: List[str]

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["vote"] = self.vote.value
        return d


@dataclass
class FinalVerdict:
    final: Vote
    reason: str
    score: float
    distribution: Dict[str, int]
    vetoes: List[str]

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["final"] = self.final.value
        return d


@dataclass
class DecisionBundle:
    decision: str
    context: str
    model: str
    final: FinalVerdict
    agents: List[AgentVerdict]
