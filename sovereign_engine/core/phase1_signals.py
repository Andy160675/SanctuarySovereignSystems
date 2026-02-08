"""
PHASE 1 — Typed Signal Substrate
CSS-ENG-MOD-001 | Sovereign Recursion Engine

Canonical signal tuple: (type, domain, authority, payload, hash, timestamp)
Strict validation rejects untyped or malformed signals.
Signal bus provides schema-guarded channels with priority escalation lane.

Dependency: Phase 0 (Constitution must be loaded and validated)
Invariant: No untyped signal can exist downstream of this module.
"""

import hashlib
import json
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Optional
from .phase0_constitution import Constitution, ConstitutionalError


class SignalValidationError(Exception):
    """Raised when a signal fails schema validation."""
    pass


@dataclass
class Signal:
    """
    Canonical signal. Created ONLY via SignalFactory.create().

    Once created, the hash locks the content. Any mutation
    will cause integrity verification to fail.
    """
    id: str
    type: str
    domain: str
    authority: str
    payload: Any
    source: Optional[str]
    correlation_id: Optional[str]
    timestamp: float
    hash: str

    # Mutable state — set by router/handlers
    routed: bool = False
    handled: bool = False
    outcome: Optional[str] = None

    def verify_integrity(self) -> bool:
        """Verify hash matches content. Detects any tampering."""
        expected = self._compute_hash()
        return self.hash == expected

    def _compute_hash(self) -> str:
        content = json.dumps({
            "id": self.id,
            "type": self.type,
            "domain": self.domain,
            "authority": self.authority,
            "payload": _serialize_payload(self.payload),
            "timestamp": self.timestamp,
        }, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()

    def to_record(self) -> dict:
        """Minimal record for audit trail."""
        return {
            "id": self.id,
            "type": self.type,
            "domain": self.domain,
            "authority": self.authority,
            "source": self.source,
            "correlation_id": self.correlation_id,
            "timestamp": self.timestamp,
            "hash": self.hash,
            "routed": self.routed,
            "handled": self.handled,
            "outcome": self.outcome,
        }


def _serialize_payload(payload: Any) -> str:
    """Deterministic payload serialisation for hashing."""
    if isinstance(payload, str):
        return payload
    try:
        return json.dumps(payload, sort_keys=True, default=str)
    except (TypeError, ValueError):
        return str(payload)


class SignalFactory:
    """
    Schema-enforced signal constructor.
    This is the ONLY way to create signals that enter the bus.
    """

    def __init__(self, constitution: Constitution):
        schema = constitution.get("signal_schema")
        self._valid_types = frozenset(schema["valid_types"])
        self._valid_domains = frozenset(schema["valid_domains"])
        self._valid_authorities = frozenset(schema["valid_authorities"])
        self._required_fields = frozenset(schema["required_fields"])

    def create(
        self,
        type: str,
        domain: str,
        authority: str,
        payload: Any,
        source: Optional[str] = None,
        correlation_id: Optional[str] = None,
    ) -> Signal:
        """Create a validated signal. Throws on schema violation."""

        if not type or type not in self._valid_types:
            raise SignalValidationError(
                f"Invalid signal type: '{type}'. Valid: {sorted(self._valid_types)}"
            )
        if not domain or domain not in self._valid_domains:
            raise SignalValidationError(
                f"Invalid signal domain: '{domain}'. Valid: {sorted(self._valid_domains)}"
            )
        if not authority or authority not in self._valid_authorities:
            raise SignalValidationError(
                f"Invalid signal authority: '{authority}'. Valid: {sorted(self._valid_authorities)}"
            )
        if payload is None:
            raise SignalValidationError("Signal payload cannot be None")

        sig = Signal(
            id=str(uuid.uuid4()),
            type=type,
            domain=domain,
            authority=authority,
            payload=payload,
            source=source,
            correlation_id=correlation_id,
            timestamp=time.time(),
            hash="",  # placeholder
        )
        sig.hash = sig._compute_hash()

        if not sig.verify_integrity():
            raise SignalValidationError("Signal failed integrity check after creation")

        return sig

    def validate(self, signal: Signal) -> tuple[bool, list[str]]:
        """Validate an existing signal against schema. Returns (valid, errors)."""
        errors = []

        if not isinstance(signal, Signal):
            return False, ["Not a Signal instance"]

        if signal.type not in self._valid_types:
            errors.append(f"Invalid type: {signal.type}")
        if signal.domain not in self._valid_domains:
            errors.append(f"Invalid domain: {signal.domain}")
        if signal.authority not in self._valid_authorities:
            errors.append(f"Invalid authority: {signal.authority}")
        if not signal.hash:
            errors.append("Missing hash")
        if not signal.timestamp:
            errors.append("Missing timestamp")
        if not signal.verify_integrity():
            errors.append("Hash integrity failure")

        return (len(errors) == 0, errors)


@dataclass
class BusStats:
    received: int = 0
    rejected: int = 0
    dispatched: int = 0
    halted: int = 0


class SignalBus:
    """
    Schema-guarded signal bus with priority channels.

    Channel priority: halt > escalation > normal
    When halted, only halt signals pass.
    """

    def __init__(self, factory: SignalFactory, constitution: Constitution):
        self._factory = factory
        self._constitution = constitution
        self._channels: dict[str, list[Signal]] = {
            "halt": [],
            "escalation": [],
            "normal": [],
        }
        self._halted = False
        self._stats = BusStats()

    def submit(self, signal: Signal) -> dict:
        """
        Submit a signal to the bus. Schema-validates before accepting.
        Returns {accepted, channel?, error?}
        """
        self._stats.received += 1

        # Halt gate
        if self._halted and signal.type != "halt":
            self._stats.rejected += 1
            return {"accepted": False, "error": "Bus halted. Only halt signals accepted."}

        # Schema validation
        valid, errors = self._factory.validate(signal)
        if not valid:
            self._stats.rejected += 1
            return {"accepted": False, "error": f"Schema violation: {'; '.join(errors)}"}

        # Classify and enqueue
        channel = self._classify(signal)
        self._channels[channel].append(signal)

        return {"accepted": True, "channel": channel, "signal_id": signal.id}

    def drain(self, channel: str = "all") -> list[Signal]:
        """Drain signals. 'all' drains in priority order: halt > escalation > normal."""
        if channel == "all":
            result = []
            for ch in ["halt", "escalation", "normal"]:
                result.extend(self._channels[ch])
                self._channels[ch] = []
            return result

        if channel not in self._channels:
            raise ConstitutionalError(f"Unknown channel: {channel}")

        signals = self._channels[channel]
        self._channels[channel] = []
        return signals

    def pending(self) -> dict:
        return {
            ch: len(signals) for ch, signals in self._channels.items()
        } | {"total": sum(len(s) for s in self._channels.values())}

    def halt(self, reason: str) -> dict:
        self._halted = True
        self._stats.halted += 1
        return {"halted": True, "reason": reason, "timestamp": time.time()}

    def resume(self) -> dict:
        self._halted = False
        return {"halted": False, "timestamp": time.time()}

    @property
    def is_halted(self) -> bool:
        return self._halted

    @property
    def stats(self) -> BusStats:
        return self._stats

    def _classify(self, signal: Signal) -> str:
        if signal.type == "halt":
            return "halt"
        if signal.type == "escalation" or signal.domain == "emergency":
            return "escalation"
        return "normal"
