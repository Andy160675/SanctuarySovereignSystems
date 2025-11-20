from src.core.governance import Proposal, ActionType

class Scout:
    def propose_log_cleanup(self):
        return Proposal(
            action_type=ActionType.TEST_TRIAL,
            description="Cleanup old logs to save space",
            target_system="LogServer",
            estimated_cost=0.05,
            payload={"task_name": "log_cleanup", "params": {"days": 30}}
        )