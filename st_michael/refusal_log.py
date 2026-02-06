# =============================================================================
# ST MICHAEL — Proof of Refusal Logger
# =============================================================================
# Every failed attempt generates an immutable Proof-of-Refusal artifact.
#
# PURPOSE:
# 1. Audit trail of all blocked actions
# 2. Evidence for governance review
# 3. Pattern detection for malicious attempts
# 4. Constitutional compliance proof
# =============================================================================

import hashlib
import json
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


def _utc_now() -> datetime:
    """Return current UTC time as timezone-aware datetime."""
    return datetime.now(timezone.utc)


@dataclass
class ProofOfRefusal:
    """
    Immutable record of a refused action.

    Every failed override attempt, blocked execution, or policy violation
    generates a ProofOfRefusal that is hashed, timestamped, and persisted.
    """
    refusal_id: str
    timestamp: str
    action_type: str  # e.g., "override_attempt", "policy_violation", "quorum_failure"
    action_details: dict
    reason: str
    requestor_id: Optional[str]
    evidence_hash: str  # SHA-256 of the action that was refused
    refusal_hash: str = ""  # Computed hash of this refusal record

    def __post_init__(self):
        if not self.refusal_hash:
            self.refusal_hash = self._compute_hash()

    def _compute_hash(self) -> str:
        """Compute SHA-256 hash of this refusal record."""
        content = (
            f"{self.refusal_id}|{self.timestamp}|{self.action_type}|"
            f"{json.dumps(self.action_details, sort_keys=True)}|{self.reason}|"
            f"{self.requestor_id}|{self.evidence_hash}"
        )
        return hashlib.sha256(content.encode()).hexdigest()

    def to_dict(self) -> dict:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)


class RefusalLogger:
    """
    Logger for Proof-of-Refusal artifacts.

    All refusals are persisted to /logs/refusals/ with:
    - Unique ID based on timestamp
    - Full action details
    - Cryptographic hash for tamper detection
    - Chain linking to previous refusal (optional)
    """

    def __init__(self, log_path: Optional[Path] = None):
        self.log_path = log_path or Path("logs/refusals")
        self.log_path.mkdir(parents=True, exist_ok=True)
        self._last_refusal_hash: Optional[str] = None

    def log_refusal(
        self,
        action_type: str,
        action_details: dict,
        reason: str,
        requestor_id: Optional[str] = None,
    ) -> ProofOfRefusal:
        """
        Log a refused action and generate Proof-of-Refusal.

        Args:
            action_type: Category of the refused action
            action_details: Full details of what was attempted
            reason: Why the action was refused
            requestor_id: Who/what attempted the action

        Returns:
            ProofOfRefusal artifact (also persisted to disk)
        """
        timestamp = _utc_now().isoformat()
        # Add a counter or use more precision if needed, but for now just ensure uniqueness
        import uuid
        refusal_id = f"REFUSAL-{timestamp.replace(':', '-').replace('.', '-')}-{uuid.uuid4().hex[:8]}"

        # Hash the evidence (what was refused)
        evidence_content = json.dumps(action_details, sort_keys=True)
        evidence_hash = hashlib.sha256(evidence_content.encode()).hexdigest()

        proof = ProofOfRefusal(
            refusal_id=refusal_id,
            timestamp=timestamp,
            action_type=action_type,
            action_details=action_details,
            reason=reason,
            requestor_id=requestor_id,
            evidence_hash=evidence_hash,
        )

        self._persist(proof)
        self._last_refusal_hash = proof.refusal_hash

        return proof

    def log_override_failure(
        self,
        proposal_id: str,
        votes_for: int,
        votes_required: int,
        requestor_id: Optional[str] = None,
    ) -> ProofOfRefusal:
        """Log a failed override attempt due to insufficient quorum."""
        return self.log_refusal(
            action_type="quorum_failure",
            action_details={
                "proposal_id": proposal_id,
                "votes_for": votes_for,
                "votes_required": votes_required,
                "shortfall": votes_required - votes_for,
            },
            reason=f"Quorum not achieved: {votes_for}/{votes_required} votes",
            requestor_id=requestor_id,
        )

    def log_cooling_violation(
        self,
        proposal_id: str,
        cooling_ends_at: str,
        attempted_at: str,
        requestor_id: Optional[str] = None,
    ) -> ProofOfRefusal:
        """Log an attempt to execute override before cooling period ends."""
        return self.log_refusal(
            action_type="cooling_violation",
            action_details={
                "proposal_id": proposal_id,
                "cooling_ends_at": cooling_ends_at,
                "attempted_at": attempted_at,
            },
            reason="Attempted execution during mandatory 72h cooling period",
            requestor_id=requestor_id,
        )

    def log_policy_violation(
        self,
        policy_name: str,
        violation_details: dict,
        requestor_id: Optional[str] = None,
    ) -> ProofOfRefusal:
        """Log a policy violation."""
        return self.log_refusal(
            action_type="policy_violation",
            action_details={
                "policy_name": policy_name,
                **violation_details,
            },
            reason=f"Violated policy: {policy_name}",
            requestor_id=requestor_id,
        )

    def get_refusal_count(self) -> int:
        """Count total refusals logged."""
        return len(list(self.log_path.glob("REFUSAL-*.json")))

    def get_recent_refusals(self, limit: int = 10) -> list[ProofOfRefusal]:
        """Get most recent refusals."""
        files = sorted(self.log_path.glob("REFUSAL-*.json"), reverse=True)[:limit]
        refusals = []

        for f in files:
            data = json.loads(f.read_text())
            refusals.append(ProofOfRefusal(**data))

        return refusals

    def _persist(self, proof: ProofOfRefusal) -> None:
        """Persist proof to disk."""
        filepath = self.log_path / f"{proof.refusal_id}.json"
        filepath.write_text(proof.to_json())
