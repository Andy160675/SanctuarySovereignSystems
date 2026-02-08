from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from threading import RLock
from typing import Any, Dict, List, Optional
import json


def _canonical_json(obj: Any) -> str:
    # Deterministic serialization for stable hashing.
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _sha256_hex(text: str) -> str:
    return sha256(text.encode("utf-8")).hexdigest()


def utc_now_iso() -> str:
    # Always UTC, explicit Z suffix.
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


class ChainIntegrityError(RuntimeError):
    """Raised when the evidence chain fails integrity checks."""


@dataclass(frozen=True)
class EvidenceRecord:
    id: str
    timestamp: str  # ISO 8601 UTC string
    event_type: str
    content_hash: str
    content: Dict[str, Any]
    previous_id: str
    bolt_on_version: str
    metadata: Optional[Dict[str, Any]] = None

    @staticmethod
    def compute_content_hash(content: Dict[str, Any]) -> str:
        return _sha256_hex(_canonical_json(content))

    @staticmethod
    def compute_id(
        timestamp: str,
        event_type: str,
        content_hash: str,
        previous_id: str,
        bolt_on_version: str,
    ) -> str:
        payload = {
            "timestamp": timestamp,
            "event_type": event_type,
            "content_hash": content_hash,
            "previous_id": previous_id,
            "bolt_on_version": bolt_on_version,
        }
        return _sha256_hex(_canonical_json(payload))

    def validate_self(self) -> None:
        expected_content_hash = self.compute_content_hash(self.content)
        if self.content_hash != expected_content_hash:
            raise ChainIntegrityError(
                f"Tamper detected: content_hash mismatch on record {self.id}"
            )

        expected_id = self.compute_id(
            self.timestamp,
            self.event_type,
            self.content_hash,
            self.previous_id,
            self.bolt_on_version,
        )
        if self.id != expected_id:
            raise ChainIntegrityError(
                f"Tamper detected: id mismatch on record {self.id}"
            )

    def to_json_line(self) -> str:
        return _canonical_json(asdict(self))

    @classmethod
    def from_json_line(cls, line: str) -> "EvidenceRecord":
        data = json.loads(line)
        return cls(**data)


class JsonlEvidenceStore:
    """
    Append-only JSONL store.
    One record per line, deterministic structure.
    """
    def __init__(self, file_path: Path):
        self.file_path = Path(file_path)
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = RLock()

        if not self.file_path.exists():
            self.file_path.touch()

    def read_all(self) -> List[EvidenceRecord]:
        with self._lock:
            records: List[EvidenceRecord] = []
            for raw in self.file_path.read_text(encoding="utf-8").splitlines():
                raw = raw.strip()
                if not raw:
                    continue
                records.append(EvidenceRecord.from_json_line(raw))
            return records

    def append(self, record: EvidenceRecord) -> None:
        with self._lock:
            with self.file_path.open("a", encoding="utf-8", newline="\n") as f:
                f.write(record.to_json_line() + "\n")


class EvidenceChain:
    GENESIS_PREVIOUS_ID = "0" * 64

    def __init__(self, storage_path: str | Path):
        self.store = JsonlEvidenceStore(Path(storage_path))
        self._lock = RLock()
        # Load + verify on boot; fail hard if tampered.
        self._records = self.store.read_all()
        self._verify_all()

    def _verify_all(self) -> None:
        prev = self.GENESIS_PREVIOUS_ID
        for idx, rec in enumerate(self._records):
            rec.validate_self()

            if rec.previous_id != prev:
                raise ChainIntegrityError(
                    f"Chain link mismatch at index {idx}: "
                    f"expected previous_id {prev}, got {rec.previous_id}"
                )
            prev = rec.id

    @property
    def records(self) -> List[EvidenceRecord]:
        return list(self._records)

    @property
    def tip(self) -> str:
        return self._records[-1].id if self._records else self.GENESIS_PREVIOUS_ID

    def append(
        self,
        event_type: str,
        content: Dict[str, Any],
        bolt_on_version: str,
        metadata: Optional[Dict[str, Any]] = None,
        timestamp: Optional[str] = None,
    ) -> EvidenceRecord:
        if not event_type or not isinstance(event_type, str):
            raise ValueError("event_type must be a non-empty string")
        if not isinstance(content, dict):
            raise ValueError("content must be a dict")
        if not bolt_on_version or not isinstance(bolt_on_version, str):
            raise ValueError("bolt_on_version must be a non-empty string")

        with self._lock:
            ts = timestamp or utc_now_iso()
            previous_id = self.tip
            content_hash = EvidenceRecord.compute_content_hash(content)
            rec_id = EvidenceRecord.compute_id(
                timestamp=ts,
                event_type=event_type,
                content_hash=content_hash,
                previous_id=previous_id,
                bolt_on_version=bolt_on_version,
            )

            record = EvidenceRecord(
                id=rec_id,
                timestamp=ts,
                event_type=event_type,
                content_hash=content_hash,
                content=content,
                previous_id=previous_id,
                bolt_on_version=bolt_on_version,
                metadata=metadata,
            )

            record.validate_self()
            self.store.append(record)
            self._records.append(record)
            return record

    def verify_chain(self) -> bool:
        try:
            self._verify_all()
            return True
        except ChainIntegrityError:
            return False


# Optional singleton accessor for app-wide usage.
_GLOBAL_CHAIN: Optional[EvidenceChain] = None
_GLOBAL_LOCK = RLock()


def get_global_evidence_chain(storage_path: str | Path = "audit/evidence/chain.jsonl") -> EvidenceChain:
    global _GLOBAL_CHAIN
    with _GLOBAL_LOCK:
        if _GLOBAL_CHAIN is None:
            _GLOBAL_CHAIN = EvidenceChain(storage_path)
        return _GLOBAL_CHAIN
