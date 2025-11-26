# -*- coding: utf-8 -*-
"""
Governance Gate for the Boardroom System.

This module implements:
- Hard Gate checks (ethics, legal, security, evidence, consensus).
- A deterministic GovernanceDecision object used by BoardroomSession and UI layers.
- A simple signal: proceed / block / reconcile, with machine-parseable reasons.
- Governance Commit path: when allowed, writes a decision_commit artifact and
  mints a Merkle-root receipt ready for external anchoring.

Design goals:
- Pure logic for gate evaluation.
- Minimal, explicit I/O for commit artifacts (under DATA/).
- Stable schema for audit and external consumption.
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import hashlib
import json
import uuid


# ---------------------------------------------------------------------------
# Common helpers
# ---------------------------------------------------------------------------

def iso_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


# Base data paths (aligned with audit spine)
DATA_ROOT = Path("DATA")
COMMITS_DIR = DATA_ROOT / "_commits"


def ensure_commits_dir() -> None:
    COMMITS_DIR.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# Core data classes
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class GateResult:
    """
    Result of a single governance gate.

    severity:
        - "info"  : non-blocking, informative only
        - "warn"  : non-blocking, but attention recommended
        - "block" : hard gate – decision must not be executed
    """
    name: str
    passed: bool
    severity: str  # "info" | "warn" | "block"
    reasons: List[str] = field(default_factory=list)
    required_actions: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class GovernanceDecision:
    """
    Aggregated governance outcome for a single deliberation cycle.
    Intended to be persisted alongside the audit snapshot.
    """
    topic: str
    session_id: str
    timestamp: str
    consensus_action: Optional[str]
    consensus_count: int
    consensus_map: Dict[str, int]
    gates: Dict[str, GateResult]
    overall_passed: bool
    requires_reconciliation: bool

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["gates"] = {k: asdict(v) for k, v in self.gates.items()}
        return d


# ---------------------------------------------------------------------------
# Internal helpers operating on role outputs
# ---------------------------------------------------------------------------

def _find_role_output(role_key: str, outputs: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    for o in outputs:
        if o.get("role_key") == role_key:
            return o
    return None


def _compute_consensus(outputs: List[Dict[str, Any]]) -> Tuple[Optional[str], int, Dict[str, int]]:
    """
    Aggregate non-NO_ACTION actions across roles and compute a simple consensus metric.
    """
    freq: Dict[str, int] = {}
    for o in outputs:
        action = (o.get("action") or "").strip()
        if not action or action.startswith("NO_ACTION"):
            continue
        freq[action] = freq.get(action, 0) + 1

    if not freq:
        return None, 0, {}

    consensus_action, count = max(freq.items(), key=lambda kv: kv[1])
    return consensus_action, count, freq


# ---------------------------------------------------------------------------
# Gate evaluators
# ---------------------------------------------------------------------------

def _evidence_gate(topic: str, outputs: List[Dict[str, Any]]) -> GateResult:
    recorder = _find_role_output("recorder", outputs)
    archivist = _find_role_output("archivist", outputs)

    reasons: List[str] = []

    if recorder is None:
        reasons.append("Recorder role output missing.")
    if archivist is None:
        reasons.append("Archivist role output missing.")

    if recorder is not None:
        if not recorder.get("evidence"):
            reasons.append("Recorder has no evidence anchors.")
    if archivist is not None:
        if not archivist.get("evidence"):
            reasons.append("Archivist has no evidence anchors.")

    passed = len(reasons) == 0
    severity = "block" if not passed else "info"
    required_actions = []
    if not passed:
        required_actions.append("Ensure Recorder and Archivist write at least one evidence anchor each.")

    return GateResult(
        name="evidence",
        passed=passed,
        severity=severity,
        reasons=reasons or ["Evidence and traceability requirements satisfied."],
        required_actions=required_actions,
    )


def _ethics_gate(topic: str, outputs: List[Dict[str, Any]]) -> GateResult:
    ethicist = _find_role_output("ethicist", outputs)
    reasons: List[str] = []
    required_actions: List[str] = []

    topic_l = topic.lower()
    risk_keywords = ["risk", "harm", "privacy", "abuse", "bias", "injury", "safety"]

    if ethicist is None:
        reasons.append("Ethicist role output missing.")
        return GateResult(
            name="ethics",
            passed=False,
            severity="warn",
            reasons=reasons,
            required_actions=["Ensure Ethicist role is active in future deliberations."],
        )

    action = (ethicist.get("action") or "").strip().upper()
    verdict = (ethicist.get("verdict") or "").strip()

    if action == "REQUEST_ETHICS_REVIEW":
        reasons.append("Ethicist has requested an ethics review; this is a blocking signal.")
        required_actions.append("Complete an explicit ethics review and update decision record before proceeding.")
        return GateResult(
            name="ethics",
            passed=False,
            severity="block",
            reasons=reasons,
            required_actions=required_actions,
        )

    if any(k in topic_l for k in risk_keywords) and "no immediate ethical red flags" in verdict.lower():
        reasons.append("Topic contains risk-related terms but Ethicist reports no flags; recommend manual sanity check.")
        required_actions.append("Perform a lightweight human ethics sanity check before execution.")
        return GateResult(
            name="ethics",
            passed=True,
            severity="warn",
            reasons=reasons,
            required_actions=required_actions,
        )

    return GateResult(
        name="ethics",
        passed=True,
        severity="info",
        reasons=["No ethical blocking conditions detected."],
        required_actions=[],
    )


def _legal_gate(topic: str, outputs: List[Dict[str, Any]]) -> GateResult:
    jurist = _find_role_output("jurist", outputs)
    reasons: List[str] = []
    required_actions: List[str] = []

    topic_l = topic.lower()
    regulated_terms = ["contract", "agreement", "regulation", "law", "gdpr", "data", "personal data"]

    if jurist is None:
        if any(t in topic_l for t in regulated_terms):
            reasons.append("Jurist output missing for legally sensitive topic.")
            required_actions.append("Obtain explicit legal review before proceeding.")
            return GateResult(
                name="legal",
                passed=False,
                severity="warn",
                reasons=reasons,
                required_actions=required_actions,
            )
        return GateResult(
            name="legal",
            passed=True,
            severity="info",
            reasons=["Jurist role not present; no explicit legal concerns detected from topic keywords."],
            required_actions=[],
        )

    action = (jurist.get("action") or "").strip().upper()
    if action == "REFER_TO_LEGAL":
        reasons.append("Jurist has requested formal legal review; this is a blocking signal.")
        required_actions.append("Obtain legal counsel sign-off and update the governance record.")
        return GateResult(
            name="legal",
            passed=False,
            severity="block",
            reasons=reasons,
            required_actions=required_actions,
        )

    return GateResult(
        name="legal",
        passed=True,
        severity="info",
        reasons=["No blocking legal conditions detected."],
        required_actions=[],
    )


def _security_gate(topic: str, outputs: List[Dict[str, Any]]) -> GateResult:
    guardian = _find_role_output("guardian", outputs)
    reasons: List[str] = []
    required_actions: List[str] = []

    if guardian is None:
        return GateResult(
            name="security",
            passed=False,
            severity="warn",
            reasons=["Guardian role output missing; security posture unknown."],
            required_actions=["Ensure Guardian role is active for security-sensitive topics."],
        )

    action = (guardian.get("action") or "").strip().upper()
    if action == "LOCK_READ_ACCESS":
        reasons.append("Guardian recommends restricted access until integrity is verified.")
        required_actions.append("Keep decision and artifacts restricted; verify integrity before external release.")
        return GateResult(
            name="security",
            passed=True,
            severity="warn",
            reasons=reasons,
            required_actions=required_actions,
        )

    return GateResult(
        name="security",
        passed=True,
        severity="info",
        reasons=["No elevated security restrictions requested."],
        required_actions=[],
    )


def _consensus_gate(consensus_action: Optional[str], consensus_count: int) -> GateResult:
    reasons: List[str] = []
    required_actions: List[str] = []

    if consensus_action is None or consensus_count == 0:
        reasons.append("No shared action among roles; no consensus available.")
        required_actions.append("Run a targeted Reconciliation Cycle or request more information.")
        return GateResult(
            name="consensus",
            passed=False,
            severity="warn",
            reasons=reasons,
            required_actions=required_actions,
        )

    if consensus_count >= 7:
        reasons.append(f"Supermajority consensus achieved: {consensus_action} (count={consensus_count}).")
        return GateResult(
            name="consensus",
            passed=True,
            severity="info",
            reasons=reasons,
            required_actions=[],
        )

    reasons.append(f"Sub-majority consensus only: {consensus_action} (count={consensus_count}).")
    required_actions.append("Run Reconciliation Cycle before treating this as binding.")
    return GateResult(
        name="consensus",
        passed=False,
        severity="warn",
        reasons=reasons,
        required_actions=required_actions,
    )


# ---------------------------------------------------------------------------
# Public evaluation API
# ---------------------------------------------------------------------------

def evaluate_governance(
    topic: str,
    session_id: str,
    role_outputs: List[Dict[str, Any]],
) -> GovernanceDecision:
    """
    Evaluate the governance state for a single deliberation.
    """
    timestamp = iso_now()

    consensus_action, consensus_count, consensus_map = _compute_consensus(role_outputs)

    gates: Dict[str, GateResult] = {}
    gates["evidence"] = _evidence_gate(topic, role_outputs)
    gates["ethics"] = _ethics_gate(topic, role_outputs)
    gates["legal"] = _legal_gate(topic, role_outputs)
    gates["security"] = _security_gate(topic, role_outputs)
    gates["consensus"] = _consensus_gate(consensus_action, consensus_count)

    # Overall pass = no "block" gates.
    overall_passed = all(g.severity != "block" for g in gates.values())

    # Reconciliation required if:
    # - any gate is blocking, OR
    # - consensus gate is warning (sub-majority / no consensus).
    requires_reconciliation = any(g.severity == "block" for g in gates.values()) or (
        gates["consensus"].severity == "warn"
    )

    return GovernanceDecision(
        topic=topic,
        session_id=session_id,
        timestamp=timestamp,
        consensus_action=consensus_action,
        consensus_count=consensus_count,
        consensus_map=consensus_map,
        gates=gates,
        overall_passed=overall_passed,
        requires_reconciliation=requires_reconciliation,
    )


# ---------------------------------------------------------------------------
# Governance Commit (sign-off) API
# ---------------------------------------------------------------------------

def _build_merkle_root_for_commit(
    decision: GovernanceDecision,
    snapshot_path: Path,
    role_outputs: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Compute a simple Merkle root over key commit fields.

    Leaves:
      - session_id
      - topic
      - snapshot_path
      - governance_json_sha256
      - roles_json_sha256

    This is internal-only; external anchoring can reuse root + leaf hashes.
    """
    leaves: List[bytes] = []

    leaves.append(f"session_id:{decision.session_id}".encode("utf-8"))
    leaves.append(f"topic:{decision.topic}".encode("utf-8"))
    leaves.append(f"snapshot_path:{snapshot_path}".encode("utf-8"))
    gov_json = json.dumps(decision.to_dict(), sort_keys=True).encode("utf-8")
    leaves.append(f"governance_sha256:{sha256_hex(gov_json)}".encode("utf-8"))
    roles_json = json.dumps(role_outputs, sort_keys=True).encode("utf-8")
    leaves.append(f"roles_sha256:{sha256_hex(roles_json)}".encode("utf-8"))

    if not leaves:
        root_bytes = b""
        leaf_hashes: List[str] = []
    else:
        level = [hashlib.sha256(l).digest() for l in leaves]
        while len(level) > 1:
            if len(level) % 2 == 1:
                level.append(level[-1])
            level = [
                hashlib.sha256(level[i] + level[i + 1]).digest()
                for i in range(0, len(level), 2)
            ]
        root_bytes = level[0]
        leaf_hashes = [sha256_hex(l) for l in leaves]

    return {
        "root": root_bytes.hex(),
        "leaf_hashes": leaf_hashes,
        "algo": "sha256-merkle",
        "leaves": [
            "session_id",
            "topic",
            "snapshot_path",
            "governance_sha256",
            "roles_sha256",
        ],
    }


def commit_governance_decision(
    decision: GovernanceDecision,
    snapshot_path: Path,
    role_outputs: List[Dict[str, Any]],
    *,
    external_anchor_hint: Optional[Dict[str, Any]] = None,
) -> Path:
    """
    Final "Governance Commit" pathway.

    Preconditions:
        - decision.overall_passed == True
        - decision.requires_reconciliation == False

    Effects:
        - Writes DATA/_commits/decision_<session_id>.json
        - Includes:
            - decision data
            - snapshot reference
            - Merkle-root receipt
            - optional external anchor hint (network, tx_id, etc.)

    Returns:
        Path to the commit artifact.
    """
    if not decision.overall_passed:
        raise ValueError("Cannot commit: governance decision has blocking gates (overall_passed=False).")

    if decision.requires_reconciliation:
        raise ValueError("Cannot commit: reconciliation required for this decision (requires_reconciliation=True).")

    ensure_commits_dir()

    # Ensure session_id is file-safe; your generator already avoids weird chars,
    # but we strip just in case.
    safe_session = "".join(
        ch for ch in decision.session_id if (ch.isalnum() or ch in ("-", "_"))
    ) or uuid.uuid4().hex

    commit_path = COMMITS_DIR / f"decision_{safe_session}.json"

    merkle = _build_merkle_root_for_commit(decision, snapshot_path, role_outputs)

    commit_record: Dict[str, Any] = {
        "commit_id": f"govcommit-{safe_session}",
        "session_id": decision.session_id,
        "topic": decision.topic,
        "timestamp": iso_now(),
        "snapshot_path": str(snapshot_path),
        "governance": decision.to_dict(),
        "roles": role_outputs,
        "merkle_receipt": {
            "root": merkle["root"],
            "algo": merkle["algo"],
            "leaf_hashes": merkle["leaf_hashes"],
            "leaves": merkle["leaves"],
        },
        "external_anchor": external_anchor_hint
        or {
            "status": "NOT_ANCHORED",
            "network": None,
            "tx_id": None,
            "note": "Ready for external anchoring using merkle_receipt.root.",
        },
    }

    commit_path.write_text(json.dumps(commit_record, indent=2), encoding="utf-8")
    return commit_path
