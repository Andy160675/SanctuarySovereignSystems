from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from enum import Enum

class RiskLevel(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3

@dataclass
class ProposedAction:
    action_id: str
    description: str
    risk_score: int
    payload: Dict[str, Any]

class DecisionEngine:
    def __init__(self, threshold: int = 70):
        self.threshold = threshold

    def score_action(self, action: ProposedAction) -> RiskLevel:
        if action.risk_score < 30:
            return RiskLevel.LOW
        elif action.risk_score < self.threshold:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.HIGH

    def select_action(self, actions: List[ProposedAction]) -> Optional[ProposedAction]:
        # Simple selection: pick the lowest risk action that is below threshold
        valid_actions = [a for a in actions if a.risk_score < self.threshold]
        if not valid_actions:
            return None
        return min(valid_actions, key=lambda x: x.risk_score)
