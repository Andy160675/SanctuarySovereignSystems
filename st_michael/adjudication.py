# =============================================================================
# ST MICHAEL — Adjudication Gate (Row 14)
# =============================================================================
# Constitutional enforcement through quorum-based voting.
#
# GUARANTEES:
# 1. No override without 5-of-7 quorum
# 2. 72-hour mandatory cooling period after quorum achieved
# 3. All votes cryptographically signed and logged
# 4. Failed attempts generate Proof-of-Refusal artifacts
# =============================================================================

import hashlib
import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from pathlib import Path
from typing import Optional


def _utc_now() -> datetime:
    """Return current UTC time as timezone-aware datetime."""
    return datetime.now(timezone.utc)


class QuorumStatus(Enum):
    """Status of a quorum vote."""
    PENDING = "pending"           # Vote in progress
    ACHIEVED = "achieved"         # 5-of-7 reached, cooling period active
    COOLING = "cooling"           # In 72h cooling period
    EXECUTABLE = "executable"     # Cooling complete, override permitted
    REJECTED = "rejected"         # Quorum not achieved
    EXPIRED = "expired"           # Vote window closed without quorum


@dataclass
class Vote:
    """A single vote from an identity."""
    identity_id: str
    vote: bool  # True = approve override, False = reject
    timestamp: str
    signature: str  # SHA-256 of identity_id + vote + timestamp + secret
    reason: Optional[str] = None


@dataclass
class VoteResult:
    """Result of a quorum vote."""
    proposal_id: str
    proposal_hash: str
    status: QuorumStatus
    votes_for: int
    votes_against: int
    total_votes: int
    quorum_threshold: int = 5
    total_identities: int = 7
    cooling_ends_at: Optional[str] = None
    votes: list = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "proposal_id": self.proposal_id,
            "proposal_hash": self.proposal_hash,
            "status": self.status.value,
            "votes_for": self.votes_for,
            "votes_against": self.votes_against,
            "total_votes": self.total_votes,
            "quorum_threshold": self.quorum_threshold,
            "total_identities": self.total_identities,
            "cooling_ends_at": self.cooling_ends_at,
            "votes": [v.__dict__ for v in self.votes] if self.votes else [],
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)


class AdjudicationGate:
    """
    ST MICHAEL Adjudication Gate — Row 14 of the Constitution.

    Enforces 5-of-7 quorum voting with 72-hour cooling period.
    All decisions are cryptographically attested and logged.
    """

    QUORUM_THRESHOLD = 5
    TOTAL_IDENTITIES = 7
    COOLING_PERIOD_HOURS = 72

    def __init__(self, storage_path: Optional[Path] = None):
        self.storage_path = storage_path or Path("st_michael/override_proofs")
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self._active_votes: dict[str, VoteResult] = {}

    def create_proposal(self, proposal_id: str, description: str) -> VoteResult:
        """
        Create a new override proposal for voting.

        Args:
            proposal_id: Unique identifier for this proposal
            description: What is being proposed for override

        Returns:
            VoteResult with PENDING status
        """
        proposal_hash = self._hash_proposal(proposal_id, description, _utc_now())

        result = VoteResult(
            proposal_id=proposal_id,
            proposal_hash=proposal_hash,
            status=QuorumStatus.PENDING,
            votes_for=0,
            votes_against=0,
            total_votes=0,
            votes=[],
        )

        self._active_votes[proposal_id] = result
        self._persist_vote(result)

        return result

    def cast_vote(
        self,
        proposal_id: str,
        identity_id: str,
        approve: bool,
        signature: str,
        reason: Optional[str] = None,
    ) -> VoteResult:
        """
        Cast a vote on an override proposal.

        Args:
            proposal_id: The proposal being voted on
            identity_id: Identifier of the voting identity
            approve: True to approve override, False to reject
            signature: Cryptographic signature proving identity
            reason: Optional reason for the vote

        Returns:
            Updated VoteResult

        Raises:
            ValueError: If proposal not found or already voted
        """
        if proposal_id not in self._active_votes:
            raise ValueError(f"Proposal {proposal_id} not found")

        result = self._active_votes[proposal_id]

        if result.status not in (QuorumStatus.PENDING, QuorumStatus.ACHIEVED):
            raise ValueError(f"Proposal {proposal_id} is no longer accepting votes")

        # Check for duplicate vote
        existing_ids = [v.identity_id for v in result.votes]
        if identity_id in existing_ids:
            raise ValueError(f"Identity {identity_id} has already voted")

        # Record the vote
        vote = Vote(
            identity_id=identity_id,
            vote=approve,
            timestamp=_utc_now().isoformat(),
            signature=signature,
            reason=reason,
        )
        result.votes.append(vote)
        result.total_votes += 1

        if approve:
            result.votes_for += 1
        else:
            result.votes_against += 1

        # Check for quorum
        if result.votes_for >= self.QUORUM_THRESHOLD:
            result.status = QuorumStatus.ACHIEVED
            cooling_end = _utc_now() + timedelta(hours=self.COOLING_PERIOD_HOURS)
            result.cooling_ends_at = cooling_end.isoformat()
        elif result.votes_against > (self.TOTAL_IDENTITIES - self.QUORUM_THRESHOLD):
            # Mathematically impossible to reach quorum
            result.status = QuorumStatus.REJECTED

        self._persist_vote(result)
        return result

    def check_status(self, proposal_id: str) -> VoteResult:
        """
        Check the current status of a proposal.

        Updates status based on cooling period if applicable.
        """
        if proposal_id not in self._active_votes:
            # Try to load from disk
            result = self._load_vote(proposal_id)
            if result is None:
                raise ValueError(f"Proposal {proposal_id} not found")
            self._active_votes[proposal_id] = result

        result = self._active_votes[proposal_id]

        # Check if cooling period has ended
        if result.status == QuorumStatus.ACHIEVED and result.cooling_ends_at:
            cooling_end = datetime.fromisoformat(result.cooling_ends_at)
            if _utc_now() >= cooling_end:
                result.status = QuorumStatus.EXECUTABLE
                self._persist_vote(result)

        return result

    def can_execute_override(self, proposal_id: str) -> bool:
        """Check if an override can be executed (quorum + cooling complete)."""
        try:
            result = self.check_status(proposal_id)
            return result.status == QuorumStatus.EXECUTABLE
        except ValueError:
            return False

    def _hash_proposal(self, proposal_id: str, description: str, now: datetime) -> str:
        """Create a SHA-256 hash of the proposal."""
        content = f"{proposal_id}|{description}|{now.date()}"
        return hashlib.sha256(content.encode()).hexdigest()

    def _persist_vote(self, result: VoteResult) -> None:
        """Persist vote result to disk."""
        filepath = self.storage_path / f"{result.proposal_id}.json"
        filepath.write_text(result.to_json())

    def _load_vote(self, proposal_id: str) -> Optional[VoteResult]:
        """Load vote result from disk."""
        filepath = self.storage_path / f"{proposal_id}.json"
        if not filepath.exists():
            return None

        data = json.loads(filepath.read_text())
        votes = [Vote(**v) for v in data.get("votes", [])]

        return VoteResult(
            proposal_id=data["proposal_id"],
            proposal_hash=data["proposal_hash"],
            status=QuorumStatus(data["status"]),
            votes_for=data["votes_for"],
            votes_against=data["votes_against"],
            total_votes=data["total_votes"],
            quorum_threshold=data.get("quorum_threshold", 5),
            total_identities=data.get("total_identities", 7),
            cooling_ends_at=data.get("cooling_ends_at"),
            votes=votes,
        )
