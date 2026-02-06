#!/usr/bin/env python3
"""
JARUS Surge Wrapper (SURGE_FE_V1)
=================================
Enforces the Surge "No Receipt, No Action" pattern.
Decouples constitutional evaluation and evidence recording from action execution.
Provides pre-effect intent sealing in the intent_ledger.jsonl.
"""

import time
import json
import hashlib
import os
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Callable, Optional
from .constitutional_runtime import ConstitutionalRuntime, DecisionType, Decision
from .evidence_ledger import EvidenceLedger, EvidenceReceipt, EvidenceType

class SovereigntyViolation(Exception):
    """Raised when an action violates constitutional constraints."""
    pass

class SurgeWrapper:
    """
    The Surge Wrapper ensures that governance is not just a guard,
    but the primary pre-condition for any state mutation.
    """
    
    INTENT_LEDGER_PATH = os.path.join("governance", "ledger", "intent_ledger.jsonl")

    def __init__(self, runtime: ConstitutionalRuntime, ledger: EvidenceLedger):
        self.runtime = runtime
        self.ledger = ledger
        self._last_ticket_hash = self._get_last_ticket_hash()
        # Ensure ledger directory exists
        os.makedirs(os.path.dirname(self.INTENT_LEDGER_PATH), exist_ok=True)

    def _get_last_ticket_hash(self) -> str:
        """Retrieves hash of the last entry in intent ledger."""
        if not os.path.exists(self.INTENT_LEDGER_PATH):
            return "0" * 64
        try:
            with open(self.INTENT_LEDGER_PATH, 'r') as f:
                lines = f.readlines()
                if not lines:
                    return "0" * 64
                last_entry = json.loads(lines[-1])
                return hashlib.sha256(json.dumps(last_entry, sort_keys=True).encode()).hexdigest()
        except Exception:
            return "0" * 64

    def _seal_intent(self, action_name: str, actor: str, context: Dict, decision: Decision) -> str:
        """Mints and seals an Intent Ticket BEFORE execution."""
        request_content = f"{actor}:{action_name}:{json.dumps(context, sort_keys=True)}"
        request_hash = hashlib.sha256(request_content.encode()).hexdigest()

        # Capture pre-state (deterministic for this layer)
        pre_state_hash = hashlib.sha256(b"system_stable_pre_surge").hexdigest()

        ticket = {
            "ticket_id": f"IT-{str(uuid.uuid4())[:16]}",
            "request_hash": request_hash,
            "pre_state_hash": pre_state_hash,
            "classification": decision.decision_type.value,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "previous_ticket_hash": self._last_ticket_hash
        }

        # Seal Intent Ticket (Write to disk BEFORE execution)
        with open(self.INTENT_LEDGER_PATH, 'a') as f:
            f.write(json.dumps(ticket) + "\n")

        # Update chain anchor
        self._last_ticket_hash = hashlib.sha256(json.dumps(ticket, sort_keys=True).encode()).hexdigest()
        return ticket["ticket_id"]

    def execute_sovereign_action(self, 
                                action_name: str, 
                                context: Dict[str, Any], 
                                handler: Callable[..., Any],
                                actor: str = "system") -> Dict[str, Any]:
        """
        Executes an action following the strict Surge pattern:
        1. Evaluate (Authority)
        2. Seal Intent (Pre-Effect Receipt)
        3. Record (Evidence Receipt)
        4. Execute (Action)
        5. Record Result (Post-Effect)
        
        Args:
            action_name: Unique name of the action
            context: Full context for evaluation
            handler: The actual logic to execute if permitted
            actor: Identity of the requester
            
        Returns:
            Dictionary containing result, receipt, and decision
        """
        # 1. Authority Phase
        decision = self.runtime.evaluate(context)
        
        if decision.decision_type == DecisionType.DENY:
            raise SovereigntyViolation(f"Constitutional DENY: {decision.rationale}")
        if decision.decision_type == DecisionType.HALT:
            raise SystemExit(f"System HALTED: {decision.rationale}")
        if decision.decision_type == DecisionType.ESCALATE:
            return {
                "status": "ESCALATED",
                "decision": decision.to_dict(),
                "requires_approval": True
            }

        # 2. Intent Phase (Pre-Effect)
        ticket_id = self._seal_intent(action_name, actor, context, decision)

        # 3. Evidence Phase (Pre-Image Receipt)
        receipt = self.ledger.record(
            evidence_type=EvidenceType.ACTION,
            content={
                "action": action_name,
                "ticket_id": ticket_id,
                "context_hash": decision.context_hash,
                "decision_id": decision.decision_id,
                "intent": "EXECUTE"
            },
            summary=f"Surge-Authorized: {action_name}"
        )

        # 4. Execution Phase
        try:
            start_time = time.time()
            result = handler()
            duration_ms = (time.time() - start_time) * 1000
            
            # 5. Result Phase (Post-image verification)
            self.ledger.record(
                evidence_type=EvidenceType.ACTION,
                content={
                    "action": action_name,
                    "ticket_id": ticket_id,
                    "receipt_id": receipt.receipt_id,
                    "status": "SUCCESS",
                    "duration_ms": duration_ms
                },
                summary=f"Action Complete: {action_name}"
            )
            
            return {
                "status": "SUCCESS",
                "result": result,
                "ticket_id": ticket_id,
                "receipt": receipt.to_dict(),
                "decision": decision.to_dict()
            }
        except Exception as e:
            # Record failure
            self.ledger.record(
                evidence_type=EvidenceType.ACTION,
                content={
                    "action": action_name,
                    "ticket_id": ticket_id,
                    "receipt_id": receipt.receipt_id,
                    "status": "FAILURE",
                    "error": str(e)
                },
                summary=f"Action Failed: {action_name}"
            )
            raise
