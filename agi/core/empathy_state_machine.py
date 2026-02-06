from __future__ import annotations
from dataclasses import dataclass
from typing import Literal, Optional

from .agency_metrics import AgencyVector

State = Literal["ENTRY","STEADY","WARN","REDIRECT","VAULT","DISENGAGE"]

@dataclass
class StateContext:
    AgencyDelta_7d: float = 0.0
    AgencyDelta_30d: float = 0.0
    truth_violation: bool = False


class EmpathyStateMachine:
    def __init__(self, initial: State = "ENTRY") -> None:
        self.state: State = initial

    def step(self, vec: AgencyVector, ctx: Optional[StateContext] = None) -> State:
        ctx = ctx or StateContext()

        # Safety overrides
        if ctx.truth_violation:
            self.state = "VAULT"
            return self.state
        if vec.A3 < 0.30 or vec.A4 < 0.30:
            self.state = "REDIRECT"
            return self.state
        if ctx.AgencyDelta_7d < -0.05:
            self.state = "WARN"
            return self.state

        # Base rules
        agg = vec.aggregate
        if agg >= 0.80 and ctx.AgencyDelta_7d >= 0.02:
            self.state = "VAULT"
        elif agg >= 0.60:
            self.state = "STEADY"
        elif agg >= 0.40:
            self.state = "WARN"
        else:
            self.state = "REDIRECT"
        return self.state
