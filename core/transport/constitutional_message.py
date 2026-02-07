"""
core/transport/constitutional_message.py

Constitutional message format primitives (scaffold).
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, asdict
from enum import Enum
from typing import Any, Dict, List, Optional


class MessageType(Enum):
    EVIDENCE = "evidence"
    ATTESTATION = "attestation"
    WORKFLOW = "workflow"
    QUERY = "query"
    RESPONSE = "response"
    EMERGENCY = "emergency"
    HEARTBEAT = "heartbeat"


class MessagePriority(Enum):
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class ConstitutionalMessage:
    message_id: str
    sender: str
    recipients: List[str]
    message_type: MessageType
    priority: MessagePriority
    timestamp: str
    payload: Dict[str, Any]
    evidence_chain: List[str]
    nonce: str
    signature: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["message_type"] = self.message_type.value
        data["priority"] = self.priority.value
        return data

    def generate_hash(self) -> str:
        data = self.to_dict().copy()
        data.pop("signature", None)
        message_json = json.dumps(data, sort_keys=True)
        return hashlib.sha256(message_json.encode()).hexdigest()

    # Signing stubs — integrate with actual key material later
    def sign(self, private_key_pem: Optional[str] = None) -> None:
        # Placeholder: store hash as 'signature' for wiring tests
        self.signature = self.generate_hash()

    def verify(self, public_key_pem: Optional[str] = None) -> bool:
        return self.signature == self.generate_hash()

    # Constitutional validation stubs
    def validate_constitutional(self, rules: Dict[str, Any]) -> bool:
        if not self._check_sender_authorization(rules):
            return False
        if not self._check_message_type_restrictions(rules):
            return False
        if not self._check_evidence_chain():
            return False
        # Timestamp freshness checks would be implemented here
        return True

    def _check_sender_authorization(self, rules: Dict[str, Any]) -> bool:
        allowed = rules.get("allowed_senders", [])
        return (not allowed) or (self.sender in allowed)

    def _check_message_type_restrictions(self, rules: Dict[str, Any]) -> bool:
        mt = self.message_type.value
        restrictions = rules.get("message_type_restrictions", {})
        if not restrictions:
            return True
        allowed = restrictions.get(self.sender, [])
        return (not allowed) or (mt in allowed)

    def _check_evidence_chain(self) -> bool:
        # Ensure the chain elements look like hashes
        return all(isinstance(h, str) and len(h) >= 40 for h in self.evidence_chain)
