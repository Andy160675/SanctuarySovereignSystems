from .tasks import TASK_REGISTRY
from src.core.governance import Proposal

class Executor:
    def __init__(self, boardroom=None):
        self.boardroom = boardroom

    def run_trial(self, proposal: Proposal):
        task_func = TASK_REGISTRY.get(proposal.payload.get("task_name"))
        if not task_func:
            return {"success": False, "error": "Unknown Task"}
        
        try:
            # In a real system, this runs in a sandbox container
            success, metrics = task_func(proposal.payload.get("params", {}))
            return {"success": success, "metrics": metrics}
        except Exception as e:
            return {"success": False, "error": str(e)}