from typing import Optional
from .decision_engine import RiskLevel

class OverrideGate:
    def __init__(self, auto_approve_low_risk: bool = True):
        self.auto_approve_low_risk = auto_approve_low_risk

    def check(self, risk_level: RiskLevel, action_description: str) -> bool:
        if self.auto_approve_low_risk and risk_level == RiskLevel.LOW:
            return True
        
        # In a real system, this would prompt for user input or check an external policy service
        # For v1, we default to requiring manual intervention for MEDIUM/HIGH
        print(f"ATTENTION: Manual approval required for action: {action_description}")
        print(f"Risk Level: {risk_level.name}")
        
        # Simulated manual override logic
        # For tests/automation, we can mock this. 
        # By default, we return False to stay safe.
        return False
