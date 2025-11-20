from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Dict, Optional, List
import time
import uuid

class ActionType(Enum):
    DEPLOYMENT = auto()
    ROLLBACK = auto()
    TEST_TRIAL = auto()
    CONFIG_CHANGE = auto()

@dataclass
class Proposal:
    action_type: ActionType
    description: str
    target_system: str
    estimated_cost: float
    payload: Dict = field(default_factory=dict)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: float = field(default_factory=time.time)

@dataclass
class ConstitutionalViolation:
    rule_id: str
    severity: str # "WARN", "BLOCK"
    details: str

@dataclass
class BoardroomDecision:
    proposal_id: str
    approved: bool
    decision_type: str # "AUTO_APPROVE", "VOTE_REQUIRED", "REJECTED"
    violation: Optional[ConstitutionalViolation] = None
    reasoning: str = ""
    timestamp: float = field(default_factory=time.time)