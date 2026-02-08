from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
import hmac
import json
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Tuple


class SecurityError(RuntimeError):
    pass


def canonical_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_hex(data: Any) -> str:
    if isinstance(data, str):
        data = data.encode("utf-8")
    elif not isinstance(data, (bytes, bytearray)):
        data = canonical_json(data).encode("utf-8")
    return sha256(data).hexdigest()


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _pow_payload(
    event_type: str,
    source_id: str,
    timestamp: str,
    content: Dict[str, Any],
    previous_record_hash: str,
) -> str:
    return canonical_json(
        {
            "event_type": event_type,
            "source_id": source_id,
            "timestamp": timestamp,
            "content": content,
            "previous_record_hash": previous_record_hash,
        }
    )


def mint_pow(
    event_type: str,
    source_id: str,
    timestamp: str,
    content: Dict[str, Any],
    previous_record_hash: str,
    difficulty: int = 3,
    max_nonce: int = 500_000,
) -> Tuple[int, str]:
    """
    Simple anti-spam PoW: sha256(payload + ":" + nonce) must start with N hex zeros.
    """
    target_prefix = "0" * difficulty
    payload = _pow_payload(event_type, source_id, timestamp, content, previous_record_hash)
    for nonce in range(max_nonce + 1):
        digest = sha256_hex(f"{payload}:{nonce}")
        if digest.startswith(target_prefix):
            return nonce, digest
    raise SecurityError(f"PoW not found within max_nonce={max_nonce}")


def verify_pow(
    event_type: str,
    source_id: str,
    timestamp: str,
    content: Dict[str, Any],
    previous_record_hash: str,
    nonce: int,
    expected_pow_hash: str,
    difficulty: int = 3,
) -> bool:
    payload = _pow_payload(event_type, source_id, timestamp, content, previous_record_hash)
    digest = sha256_hex(f"{payload}:{nonce}")
    return digest == expected_pow_hash and digest.startswith("0" * difficulty)


def sign_hmac(secret: bytes, payload: Dict[str, Any]) -> str:
    msg = canonical_json(payload).encode("utf-8")
    return hmac.new(secret, msg, digestmod="sha256").hexdigest()


def verify_hmac(secret: bytes, payload: Dict[str, Any], signature_hex: str) -> bool:
    computed = sign_hmac(secret, payload)
    return hmac.compare_digest(computed, signature_hex)


@dataclass(frozen=True)
class EvidenceEnvelope:
    event_type: str
    source_id: str
    key_id: str
    timestamp: str
    content: Dict[str, Any]
    previous_record_hash: str
    pow_nonce: int
    pow_hash: str
    signature: str
    record_hash: str


class ZeroTrustEvidenceChain:
    """
    JSONL append-only evidence chain with:
      - source allow-list
      - PoW
      - HMAC signature
      - hash chaining
    """

    REQUIRED_KEYS = {
        "event_type",
        "source_id",
        "key_id",
        "timestamp",
        "content",
        "previous_record_hash",
        "pow_nonce",
        "pow_hash",
        "signature",
        "record_hash",
    }

    def __init__(
        self,
        ledger_path: str | Path,
        allowed_sources: Iterable[str],
        secret_resolver: Callable[[str], bytes],
        pow_difficulty: int = 3,
    ) -> None:
        self.ledger_path = Path(ledger_path)
        self.ledger_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.ledger_path.exists():
            self.ledger_path.write_text("", encoding="utf-8")
        self.allowed_sources = set(allowed_sources)
        self.secret_resolver = secret_resolver
        self.pow_difficulty = pow_difficulty

    def _unsigned_payload(self, record: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "event_type": record["event_type"],
            "source_id": record["source_id"],
            "key_id": record["key_id"],
            "timestamp": record["timestamp"],
            "content": record["content"],
            "previous_record_hash": record["previous_record_hash"],
            "pow_nonce": record["pow_nonce"],
            "pow_hash": record["pow_hash"],
        }

    def last_record_hash(self) -> str:
        last = "0" * 64
        with self.ledger_path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                    last = rec.get("record_hash", last)
                except json.JSONDecodeError:
                    raise SecurityError("Ledger contains invalid JSON line")
        return last

    def append(
        self,
        event_type: str,
        source_id: str,
        content: Dict[str, Any],
        key_id: str,
        max_nonce: int = 500_000,
    ) -> EvidenceEnvelope:
        if source_id not in self.allowed_sources:
            raise SecurityError(f"Unauthorized source: {source_id}")

        previous = self.last_record_hash()
        ts = utc_now_iso()
        nonce, pow_hash = mint_pow(
            event_type=event_type,
            source_id=source_id,
            timestamp=ts,
            content=content,
            previous_record_hash=previous,
            difficulty=self.pow_difficulty,
            max_nonce=max_nonce,
        )

        unsigned = {
            "event_type": event_type,
            "source_id": source_id,
            "key_id": key_id,
            "timestamp": ts,
            "content": content,
            "previous_record_hash": previous,
            "pow_nonce": nonce,
            "pow_hash": pow_hash,
        }

        secret = self.secret_resolver(key_id)
        if not isinstance(secret, (bytes, bytearray)):
            raise SecurityError("secret_resolver must return bytes")

        signature = sign_hmac(bytes(secret), unsigned)

        signed = dict(unsigned)
        signed["signature"] = signature
        signed["record_hash"] = sha256_hex(canonical_json(signed))

        with self.ledger_path.open("a", encoding="utf-8") as f:
            f.write(canonical_json(signed) + "\n")

        return EvidenceEnvelope(**signed)

    def verify_chain(self) -> Tuple[bool, List[str]]:
        errors: List[str] = []
        expected_previous = "0" * 64

        with self.ledger_path.open("r", encoding="utf-8") as f:
            for idx, line in enumerate(f, start=1):
                line = line.strip()
                if not line:
                    continue

                try:
                    rec: Dict[str, Any] = json.loads(line)
                except json.JSONDecodeError:
                    errors.append(f"L{idx}: invalid JSON")
                    continue

                missing = self.REQUIRED_KEYS - set(rec.keys())
                if missing:
                    errors.append(f"L{idx}: missing keys {sorted(missing)}")
                    continue

                if rec["source_id"] not in self.allowed_sources:
                    errors.append(f"L{idx}: unauthorized source {rec['source_id']}")

                if rec["previous_record_hash"] != expected_previous:
                    errors.append(
                        f"L{idx}: chain break previous={rec['previous_record_hash']} expected={expected_previous}"
                    )

                if not verify_pow(
                    event_type=rec["event_type"],
                    source_id=rec["source_id"],
                    timestamp=rec["timestamp"],
                    content=rec["content"],
                    previous_record_hash=rec["previous_record_hash"],
                    nonce=int(rec["pow_nonce"]),
                    expected_pow_hash=rec["pow_hash"],
                    difficulty=self.pow_difficulty,
                ):
                    errors.append(f"L{idx}: invalid PoW")

                unsigned = self._unsigned_payload(rec)
                secret = self.secret_resolver(rec["key_id"])
                if not verify_hmac(bytes(secret), unsigned, rec["signature"]):
                    errors.append(f"L{idx}: invalid signature")

                signed_for_hash = dict(unsigned)
                signed_for_hash["signature"] = rec["signature"]
                expected_record_hash = sha256_hex(canonical_json(signed_for_hash))
                if rec["record_hash"] != expected_record_hash:
                    errors.append(f"L{idx}: invalid record_hash")

                expected_previous = rec["record_hash"]

        return (len(errors) == 0), errors
