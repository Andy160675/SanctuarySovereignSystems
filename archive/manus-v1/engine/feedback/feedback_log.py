"""
Article VI: The Minimal Feedback Log
======================================
Every action is logged as a minimal, atomic record:
  type → route → handler → outcome

This is the seed of observability.
This makes un-auditable actions impossible.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from hashlib import sha256
from typing import List, Optional
import json


@dataclass(frozen=True)
class LogEntry:
    """
    Atomic, immutable log record. Axiom I enforcement.
    Once created, a log entry cannot be altered.
    """
    signal_type: str
    route_target: str
    handler: str
    outcome: str
    reason: str
    evidence_hash: str
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    entry_hash: str = field(default="", repr=False)

    def __post_init__(self):
        if not self.entry_hash:
            content = json.dumps({
                "signal_type": self.signal_type,
                "route_target": self.route_target,
                "handler": self.handler,
                "outcome": self.outcome,
                "reason": self.reason,
                "evidence_hash": self.evidence_hash,
                "timestamp": self.timestamp,
            }, sort_keys=True)
            object.__setattr__(
                self, "entry_hash", sha256(content.encode()).hexdigest()
            )


class FeedbackLog:
    """
    Append-only feedback log. Axiom I: Evidence is Immutable.
    Entries can be appended but never modified or deleted.
    The chain is hash-linked for tamper detection.
    """

    def __init__(self):
        self._entries: List[LogEntry] = []
        self._chain_hash: str = sha256(b"GENESIS").hexdigest()

    @property
    def entries(self) -> tuple[LogEntry, ...]:
        """Return immutable view of all entries."""
        return tuple(self._entries)

    @property
    def chain_hash(self) -> str:
        """Current chain hash — verifiable integrity marker."""
        return self._chain_hash

    @property
    def length(self) -> int:
        return len(self._entries)

    def append(self, entry: LogEntry) -> str:
        """
        Append an entry and extend the hash chain.
        Returns the new chain hash.
        """
        chain_input = f"{self._chain_hash}:{entry.entry_hash}"
        self._chain_hash = sha256(chain_input.encode()).hexdigest()
        self._entries.append(entry)
        return self._chain_hash

    def verify_integrity(self) -> bool:
        """
        Verify the entire chain from genesis.
        Returns False if any tampering is detected.
        """
        computed_hash = sha256(b"GENESIS").hexdigest()
        for entry in self._entries:
            chain_input = f"{computed_hash}:{entry.entry_hash}"
            computed_hash = sha256(chain_input.encode()).hexdigest()
        return computed_hash == self._chain_hash

    def export_json(self) -> str:
        """Export the full log as JSON for external audit."""
        return json.dumps({
            "chain_hash": self._chain_hash,
            "entry_count": len(self._entries),
            "entries": [
                {
                    "signal_type": e.signal_type,
                    "route_target": e.route_target,
                    "handler": e.handler,
                    "outcome": e.outcome,
                    "reason": e.reason,
                    "evidence_hash": e.evidence_hash,
                    "timestamp": e.timestamp,
                    "entry_hash": e.entry_hash,
                }
                for e in self._entries
            ],
        }, indent=2)
