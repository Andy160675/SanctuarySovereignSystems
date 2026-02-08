import time
from typing import Callable, Any, Dict, Optional
from .decision_log import DecisionLogger

class Executor:
    def __init__(self, logger: DecisionLogger, max_retries: int = 3, dry_run: bool = True):
        self.logger = logger
        self.max_retries = max_retries
        self.dry_run = dry_run
        self.rollback_hooks: Dict[str, Callable] = {}

    def register_rollback(self, action_id: str, hook: Callable):
        self.rollback_hooks[action_id] = hook

    def execute(self, action_id: str, func: Callable, *args, **kwargs) -> Any:
        attempts = 0
        last_exception = None
        
        self.logger.log_decision(
            action_id=action_id,
            action_type="execution_start",
            details={"dry_run": self.dry_run, "max_retries": self.max_retries}
        )

        if self.dry_run:
            self.logger.log_decision(action_id, "dry_run_skip", {"status": "success"})
            return "DRY_RUN_SUCCESS"

        while attempts < self.max_retries:
            try:
                result = func(*args, **kwargs)
                self.logger.log_decision(action_id, "execution_success", {"attempt": attempts + 1})
                return result
            except Exception as e:
                attempts += 1
                last_exception = e
                self.logger.log_decision(action_id, "execution_failure", {"attempt": attempts, "error": str(e)})
                time.sleep(1) # Basic backoff

        self.logger.log_decision(action_id, "execution_exhausted", {"error": str(last_exception)})
        self.trigger_rollback(action_id)
        raise last_exception

    def trigger_rollback(self, action_id: str):
        if action_id in self.rollback_hooks:
            self.logger.log_decision(action_id, "rollback_start", {})
            try:
                self.rollback_hooks[action_id]()
                self.logger.log_decision(action_id, "rollback_success", {})
            except Exception as e:
                self.logger.log_decision(action_id, "rollback_failure", {"error": str(e)})
