# executor/executor.py

from typing import Tuple, List
from datetime import datetime, timezone, timedelta

from core.governance import (
    TrialAuditBundle,
    ConstitutionalViolationFlag,
    validate_executor_trial,
    raise_cvf,
    Severity,
)


class Executor:
    def __init__(self):
        self.concurrent_trials = 0

    def run_trial(
        self,
        trial: TrialAuditBundle,
    ) -> Tuple[TrialAuditBundle, List[ConstitutionalViolationFlag]]:
        cvfs: List[ConstitutionalViolationFlag] = []

        # Pre-checks
        pre_cvfs = validate_executor_trial(
            trial=trial,
            concurrent_trials=self.concurrent_trials,
        )
        cvfs.extend(pre_cvfs)

        if any(c.severity == Severity.CRITICAL for c in cvfs):
            # Hard stop; do not run
            trial.timestamps["approved"] = datetime.now(timezone.utc).isoformat()
            trial.timestamps["executed"] = trial.timestamps["approved"]
            trial.results["success"] = False
            trial.results["reason"] = "CRITICAL_CVF_PRE_EXECUTION"
            trial.cvfs.extend(cvfs)
            return trial, cvfs

        # Simulate execution with timeout
        self.concurrent_trials += 1
        try:
            start = datetime.now(timezone.utc)
            trial.timestamps["approved"] = start.isoformat()

            # --- PLACEHOLDER: run real work here ---
            # This is where you’d spin up your sandbox, call models, etc.
            # For now we simulate success.
            simulated_duration = timedelta(minutes=3)
            end = start + simulated_duration

            trial.timestamps["executed"] = end.isoformat()
            trial.timestamps["completed"] = end.isoformat()
            trial.results.setdefault("metrics", {})
            trial.results["metrics"]["simulated_duration_seconds"] = simulated_duration.total_seconds()
            trial.results.setdefault("success", True)

        finally:
            self.concurrent_trials -= 1

        trial.cvfs.extend(cvfs)
        return trial, cvfs
