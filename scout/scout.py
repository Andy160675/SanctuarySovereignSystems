# scout/scout.py

from typing import Dict, Any, Tuple, List
from datetime import datetime, timezone

from core.governance import (
    CONSTRAINTS,
    ConstitutionalViolationFlag,
    TrialAuditBundle,
    new_trial_bundle,
    validate_scout_trial,
    raise_cvf,
)


class Scout:
    def __init__(self):
        self.daily_proposals = 0      # in-memory; you’ll want persistence
        self.daily_reset_date = datetime.now(timezone.utc).date()

    def _reset_if_new_day(self) -> None:
        today = datetime.now(timezone.utc).date()
        if today != self.daily_reset_date:
            self.daily_reset_date = today
            self.daily_proposals = 0

    def propose_trial(
        self,
        idea: Dict[str, Any],
        confidence: float,
        cost_estimate: float,
    ) -> Tuple[TrialAuditBundle, List[ConstitutionalViolationFlag]]:
        self._reset_if_new_day()
        cvfs: List[ConstitutionalViolationFlag] = []

        max_per_day = CONSTRAINTS["scout"]["max_proposals_per_day"]
        if self.daily_proposals >= max_per_day:
            cvfs.append(
                raise_cvf(
                    code="SCOUT_DAILY_LIMIT",
                    severity="MEDIUM",
                    agent="scout",
                    detail=f"daily_proposals={self.daily_proposals} >= max={max_per_day}",
                )
            )

        cvfs.extend(validate_scout_trial(idea=idea, confidence=confidence))

        trial = new_trial_bundle(
            initiator="scout",
            purpose=idea.get("purpose", "unspecified"),
            inputs={
                "idea": idea,
                "data_access_mode": idea.get("data_access_mode", "logs_only"),
            },
            environment=idea.get("environment", "sandbox_v1"),
            models_used=idea.get("models_used", ["gpt-5.1-mini"]),
            cost_estimate=cost_estimate,
        )

        trial.results["confidence"] = confidence
        trial.results["flags"] = idea.get("flags", [])

        if not cvfs:
            self.daily_proposals += 1

        return trial, cvfs
