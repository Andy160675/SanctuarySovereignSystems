"""
PHASE 4 — Audit Ledger & Evidence Spine
CSS-ENG-MOD-004 | Sovereign Recursion Engine

Append-only hash-chained audit trail.
SHA-256 chain integrity. Boot validation. Truncation on corruption.

Dependency: Phase 0
Invariant: No write without hash.
Invariant: Corruption → truncation at last valid entry.
Invariant: Boot validation must pass before routing resumes.
"""

import hashlib
import json
import time
from dataclasses import dataclass, field
from typing import Any, Optional
from .phase0_constitution import Constitution, ConstitutionalError


class AuditError(Exception):
    pass


GENESIS_HASH = "0" * 64


@dataclass(frozen=True)
class AuditEntry:
    index: int
    signal_type: str
    route: str
    handler: str
    outcome: str
    signal_id: str
    signal_domain: str
    timestamp: float
    previous_hash: str
    hash: str
    extra: Optional[str] = None   # JSON-encoded additional data


@dataclass
class LedgerStats:
    written: int = 0
    verified: int = 0
    corrupted: int = 0
    truncated: int = 0


class AuditLedger:
    """
    Append-only hash-chained audit trail.
    
    Each entry chains to the previous via SHA-256.
    Boot validation verifies entire chain.
    Corruption triggers truncation at last valid entry.
    """

    def __init__(self, constitution: Constitution):
        self._constitution = constitution
        self._config = constitution.get("audit_requirements")
        self._entries: list[AuditEntry] = []
        self._last_hash = GENESIS_HASH
        self._sealed = False
        self._stats = LedgerStats()

    def write(self, record: dict) -> AuditEntry:
        """
        Write an audit entry. Enforces append-only + hash chain.
        
        INVARIANT: No write without hash.
        INVARIANT: Each entry chains to previous.
        """
        if self._sealed:
            raise AuditError("Ledger sealed — integrity compromised")

        # Validate minimum fields
        for f in ["signal_type", "route", "handler", "outcome"]:
            if f not in record:
                raise AuditError(f"Missing required field: {f}")

        idx = len(self._entries)
        ts = record.get("timestamp", time.time())

        # Build entry (without hash first)
        entry_data = {
            "index": idx,
            "signal_type": record["signal_type"],
            "route": record["route"],
            "handler": record["handler"],
            "outcome": record["outcome"],
            "signal_id": record.get("signal_id", ""),
            "signal_domain": record.get("signal_domain", ""),
            "timestamp": ts,
            "previous_hash": self._last_hash,
        }

        # Compute hash
        h = self._compute_hash(entry_data)

        entry = AuditEntry(
            index=idx,
            signal_type=record["signal_type"],
            route=record["route"],
            handler=record["handler"],
            outcome=record["outcome"],
            signal_id=record.get("signal_id", ""),
            signal_domain=record.get("signal_domain", ""),
            timestamp=ts,
            previous_hash=self._last_hash,
            hash=h,
            extra=record.get("extra"),
        )

        self._entries.append(entry)
        self._last_hash = h
        self._stats.written += 1
        return entry

    def write_routing_decision(self, signal, decision) -> AuditEntry:
        """Convenience: write a routing decision."""
        return self.write({
            "signal_type": signal.type,
            "route": decision.target or "none",
            "handler": decision.target or "none",
            "outcome": decision.action,
            "signal_id": signal.id,
            "signal_domain": signal.domain,
            "extra": decision.reason,
        })

    def write_containment(self, event) -> AuditEntry:
        """Convenience: write a containment event."""
        return self.write({
            "signal_type": event.signal_type,
            "route": "legality_gate",
            "handler": "legality_gate",
            "outcome": "terminated",
            "signal_id": event.signal_id,
            "signal_domain": event.signal_domain,
            "extra": json.dumps([{"rule": v.rule, "reason": v.reason} for v in event.violations]),
        })

    def verify(self) -> dict:
        """
        Verify entire chain from genesis.
        Returns {valid, last_valid_index, corruptions}.
        """
        prev = GENESIS_HASH
        last_valid = -1
        corruptions = []

        for i, entry in enumerate(self._entries):
            # Check chain link
            if entry.previous_hash != prev:
                corruptions.append({
                    "index": i,
                    "reason": "previous_hash mismatch",
                    "expected": prev,
                    "got": entry.previous_hash,
                })
                break

            # Check self hash
            entry_data = {
                "index": entry.index,
                "signal_type": entry.signal_type,
                "route": entry.route,
                "handler": entry.handler,
                "outcome": entry.outcome,
                "signal_id": entry.signal_id,
                "signal_domain": entry.signal_domain,
                "timestamp": entry.timestamp,
                "previous_hash": entry.previous_hash,
            }
            computed = self._compute_hash(entry_data)
            if entry.hash != computed:
                corruptions.append({
                    "index": i,
                    "reason": "entry hash mismatch",
                    "expected": computed,
                    "got": entry.hash,
                })
                break

            prev = entry.hash
            last_valid = i

        self._stats.verified += 1
        valid = len(corruptions) == 0
        if not valid:
            self._stats.corrupted += 1

        return {
            "valid": valid,
            "last_valid_index": last_valid,
            "total_entries": len(self._entries),
            "corruptions": corruptions,
        }

    def truncate_at_last_valid(self) -> dict:
        """Truncate at last valid entry on corruption."""
        v = self.verify()
        if v["valid"]:
            return {"truncated": False, "reason": "Chain is valid"}

        cut = v["last_valid_index"] + 1
        removed = len(self._entries) - cut
        self._entries = self._entries[:cut]
        self._last_hash = self._entries[-1].hash if self._entries else GENESIS_HASH
        self._stats.truncated += 1

        return {"truncated": True, "removed": removed, "new_length": len(self._entries)}

    def boot_validation(self) -> dict:
        """Verify chain at boot. Truncate if corrupted."""
        v = self.verify()
        if v["valid"]:
            return {"boot_valid": True, "entries": v["total_entries"],
                    "last_hash": self._last_hash}
        trunc = self.truncate_at_last_valid()
        return {"boot_valid": False, "action": "truncated", **trunc}

    def seal(self, reason: str):
        self._sealed = True

    @property
    def entries(self) -> list[AuditEntry]:
        return list(self._entries)

    @property
    def length(self) -> int:
        return len(self._entries)

    @property
    def last_hash(self) -> str:
        return self._last_hash

    @property
    def stats(self) -> LedgerStats:
        return self._stats

    def _compute_hash(self, data: dict) -> str:
        content = json.dumps(data, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()
