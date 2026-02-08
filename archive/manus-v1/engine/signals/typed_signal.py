"""
Article I: The Typed Signal Ontology
=====================================
All information flowing through the system is a Typed Signal.
A signal without a type is noise and is discarded.
Each type maps to a non-negotiable Level and Authority.

Signal → Type → Level → Authority

This makes implicit or untyped routing impossible.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum, auto
from hashlib import sha256
from typing import Any, Optional
import json
import uuid


class SignalType(Enum):
    """Canonical signal types. No signal may exist outside this ontology."""
    STATE_CHECK = auto()
    USAGE_VERIFICATION = auto()
    INTEGRITY_AUDIT = auto()
    TRUST_ANCHOR = auto()
    LOOP_CONFIRMATION = auto()
    ENVIRONMENT_FIT = auto()
    TIMELINE_TRACE = auto()
    SYNC_PUSH = auto()
    TRUTH_RECONCILE = auto()
    ESCALATION = auto()
    OVERRIDE = auto()
    SYSTEM_HALT = auto()


class AuthorityLevel(Enum):
    """
    Article IV: Authority Separation Model.
    Three non-overlapping roles. No bleed permitted.
    """
    OPERATOR = "operator"
    INNOVATOR = "innovator"
    STEWARD = "steward"


class SystemState(Enum):
    """
    Article V: Escalation Protocol states.
    stable → operator, degraded → innovator, constitutional → steward
    """
    STABLE = "stable"
    DEGRADED = "degraded"
    CONSTITUTIONAL = "constitutional"


# Immutable mapping: SignalType → minimum AuthorityLevel
SIGNAL_AUTHORITY_MAP: dict[SignalType, AuthorityLevel] = {
    SignalType.STATE_CHECK: AuthorityLevel.OPERATOR,
    SignalType.USAGE_VERIFICATION: AuthorityLevel.OPERATOR,
    SignalType.INTEGRITY_AUDIT: AuthorityLevel.OPERATOR,
    SignalType.TRUST_ANCHOR: AuthorityLevel.INNOVATOR,
    SignalType.LOOP_CONFIRMATION: AuthorityLevel.OPERATOR,
    SignalType.ENVIRONMENT_FIT: AuthorityLevel.OPERATOR,
    SignalType.TIMELINE_TRACE: AuthorityLevel.OPERATOR,
    SignalType.SYNC_PUSH: AuthorityLevel.OPERATOR,
    SignalType.TRUTH_RECONCILE: AuthorityLevel.INNOVATOR,
    SignalType.ESCALATION: AuthorityLevel.INNOVATOR,
    SignalType.OVERRIDE: AuthorityLevel.STEWARD,
    SignalType.SYSTEM_HALT: AuthorityLevel.STEWARD,
}


@dataclass(frozen=True)
class TypedSignal:
    """
    The atomic unit of information in the Sovereign System.
    Frozen (immutable) after creation — Axiom I enforcement.
    """
    signal_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    signal_type: SignalType = SignalType.STATE_CHECK
    authority: AuthorityLevel = AuthorityLevel.OPERATOR
    jurisdiction: str = "default"
    payload: dict = field(default_factory=dict)
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    source: str = "unknown"
    evidence_hash: str = field(default="", repr=False)

    def __post_init__(self):
        """Compute evidence hash on creation — Axiom I: immutable evidence."""
        if not self.evidence_hash:
            content = json.dumps({
                "id": self.signal_id,
                "type": self.signal_type.name,
                "authority": self.authority.value,
                "jurisdiction": self.jurisdiction,
                "payload": self.payload,
                "timestamp": self.timestamp,
                "source": self.source,
            }, sort_keys=True)
            object.__setattr__(
                self, "evidence_hash", sha256(content.encode()).hexdigest()
            )

    def validate(self) -> bool:
        """
        Legality Lane pre-check (Article III).
        Returns True only if the signal is constitutionally valid.
        """
        required_authority = SIGNAL_AUTHORITY_MAP.get(self.signal_type)
        if required_authority is None:
            return False  # Unrepresentable signal type — Axiom III
        authority_rank = {
            AuthorityLevel.OPERATOR: 0,
            AuthorityLevel.INNOVATOR: 1,
            AuthorityLevel.STEWARD: 2,
        }
        return authority_rank[self.authority] >= authority_rank[required_authority]


def create_signal(
    signal_type: SignalType,
    authority: AuthorityLevel,
    jurisdiction: str,
    payload: dict,
    source: str,
) -> Optional[TypedSignal]:
    """
    Factory function enforcing Article I + Article III.
    Returns None if the signal would be unconstitutional.
    """
    required = SIGNAL_AUTHORITY_MAP.get(signal_type)
    if required is None:
        return None  # Axiom III: unrepresentable

    signal = TypedSignal(
        signal_type=signal_type,
        authority=authority,
        jurisdiction=jurisdiction,
        payload=payload,
        source=source,
    )

    if not signal.validate():
        return None  # Legality Lane rejection

    return signal
