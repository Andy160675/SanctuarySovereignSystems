import json
import os
import hashlib
from datetime import datetime
from src.core.governance import Proposal, BoardroomDecision, ConstitutionalViolation
from src.core.config import CONFIG

class Boardroom:
    def __init__(self):
        self.ledger_path = CONFIG.LEDGER_PATH
        self.state_path = CONFIG.STATE_PATH
        self.last_hash = "GENESIS_HASH_0000000000000000"
        self._load_state()

    def _load_state(self):
        """Recover the chain head from disk."""
        if os.path.exists(self.state_path):
            with open(self.state_path, 'r') as f:
                state = json.load(f)
                self.last_hash = state.get("last_hash", self.last_hash)

    def _save_state(self):
        """Persist the chain head."""
        # Ensure directory exists
        os.makedirs(os.path.dirname(self.state_path), exist_ok=True)
        with open(self.state_path, 'w') as f:
            json.dump({"last_hash": self.last_hash, "updated_at": datetime.now().isoformat()}, f)

    def _append_to_ledger(self, entry: dict):
        """Cryptographic append-only log."""
        entry_str = json.dumps(entry, sort_keys=True)
        new_hash = hashlib.sha256(f"{self.last_hash}{entry_str}".encode()).hexdigest()
        
        entry['prev_hash'] = self.last_hash
        entry['hash'] = new_hash
        
        # 1. Write to Ledger
        os.makedirs(os.path.dirname(self.ledger_path), exist_ok=True)
        with open(self.ledger_path, "a") as f:
            f.write(json.dumps(entry) + "\n")
        
        # 2. Update State Memory & Disk
        self.last_hash = new_hash
        self._save_state()

    def evaluate_proposal(self, proposal: Proposal, trial_result: dict) -> BoardroomDecision:
        # 1. Constitutional Checks
        if proposal.estimated_cost > CONFIG.GLOBAL_MAX_DAILY_COST:
            violation = ConstitutionalViolation("COST_OVERRUN", "BLOCK", f"Cost {proposal.estimated_cost} > {CONFIG.GLOBAL_MAX_DAILY_COST}")
            decision = BoardroomDecision(proposal.id, False, "REJECTED", violation, "Budget Exceeded")
            self._append_to_ledger(decision.__dict__)
            return decision

        # 2. Logic Checks (Simplified)
        if trial_result.get("success"):
            decision = BoardroomDecision(proposal.id, True, "AUTO_APPROVE", reasoning="Trial Passed")
            self._append_to_ledger(decision.__dict__)
            return decision
        
        decision = BoardroomDecision(proposal.id, False, "REJECTED", reasoning="Trial Failed")
        self._append_to_ledger(decision.__dict__)
        return decision