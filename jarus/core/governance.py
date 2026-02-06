# core/governance.py

from __future__ import annotations
from dataclasses import dataclass, asdict
from enum import Enum
from typing import Any, Dict, List, Optional, Literal, Tuple
from datetime import datetime, timezone
import hashlib
import json
import uuid


# ---------- ENUMS & CONSTANTS ----------

class Severity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class EventType(str, Enum):
    TRIAL_PROPOSED = "TRIAL_PROPOSED"
    TRIAL_APPROVED = "TRIAL_APPROVED"
    TRIAL_REJECTED = "TRIAL_REJECTED"
    TRIAL_EXECUTED = "TRIAL_EXECUTED"
    TRIAL_FAILED = "TRIAL_FAILED"
    CVF_RAISED = "CVF_RAISED"
    DEPLOYMENT = "DEPLOYMENT"
    ROLLBACK = "ROLLBACK"


Role = Literal["scout", "executor", "boardroom"]


CONSTRAINTS: Dict[str, Any] = {
    "scout": {
        "match_confidence_threshold": 0.87,
        "max_proposals_per_day": 3,
        "ignore_capabilities": ["normative_judgment", "strategic_rewrites"],
    },
    "executor": {
        "trial_timeout_minutes": 30,
        "max_concurrent_trials": 2,
        "cost_ceiling": 35.0,  # in £ or arbitrary unit
        "data_access": ["logs_only"],
        "forbidden_models": ["unverified_vendor_models"],
        "auto_approve_threshold": 0.97,
    },
    "boardroom": {
        "auto_reject_if": [
            "constitutional_violation",
            "exceeds_cost",
            "schema_mutation",
        ],
        "require_vote_if": [
            "touches_production",
            "changes_security",
            "new_capability",
        ],
        "escalate_to_human_if": [
            "unexpected_result",
            "contradicts_history",
            "uncertain_success",
        ],
        "uncertainty_band": (0.85, 0.95),  # meta-rule: uncertainty = danger
    },
}


# ---------- DATA CLASSES ----------

@dataclass
class ConstitutionalViolationFlag:
    code: str                     # e.g. "DATA_ACCESS_PROHIBITED"
    severity: Severity
    agent: Role
    detail: str
    timestamp: str

    @staticmethod
    def now(
        code: str,
        severity: Severity,
        agent: Role,
        detail: str,
    ) -> "ConstitutionalViolationFlag":
        return ConstitutionalViolationFlag(
            code=code,
            severity=severity,
            agent=agent,
            detail=detail,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )


@dataclass
class TrialAuditBundle:
    trial_id: str
    initiator: Role
    purpose: str
    inputs: Dict[str, Any]
    environment: str
    models_used: List[str]
    cost_estimate: float
    timestamps: Dict[str, str]
    results: Dict[str, Any]
    cvfs: List[ConstitutionalViolationFlag]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "trial_id": self.trial_id,
            "initiator": self.initiator,
            "purpose": self.purpose,
            "inputs": self.inputs,
            "environment": self.environment,
            "models_used": self.models_used,
            "cost_estimate": self.cost_estimate,
            "timestamps": self.timestamps,
            "results": self.results,
            "cvfs": [asdict(c) for c in self.cvfs],
        }


@dataclass
class LedgerEntry:
    entry_id: str
    previous_entry_hash: Optional[str]
    event_type: EventType
    payload: Dict[str, Any]
    timestamp: str
    signature: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "entry_id": self.entry_id,
            "previous_entry_hash": self.previous_entry_hash,
            "event_type": self.event_type.value,
            "payload": self.payload,
            "timestamp": self.timestamp,
            "signature": self.signature,
        }


# ---------- CVF HELPERS ----------

def raise_cvf(
    code: str,
    severity: Severity,
    agent: Role,
    detail: str,
) -> ConstitutionalViolationFlag:
    """
    Central factory. Use this everywhere instead of rolling your own.
    """
    return ConstitutionalViolationFlag.now(
        code=code,
        severity=severity,
        agent=agent,
        detail=detail,
    )


def contains_critical(cvfs: List[ConstitutionalViolationFlag]) -> bool:
    return any(c.severity == Severity.CRITICAL for c in cvfs)


# ---------- TRIAL VALIDATION ----------

def validate_scout_trial(
    idea: Dict[str, Any],
    confidence: float,
) -> List[ConstitutionalViolationFlag]:
    cvfs: List[ConstitutionalViolationFlag] = []

    min_conf = CONSTRAINTS["scout"]["match_confidence_threshold"]
    if confidence < min_conf:
        cvfs.append(
            raise_cvf(
                code="SCOUT_LOW_CONFIDENCE",
                severity=Severity.MEDIUM,
                agent="scout",
                detail=f"confidence={confidence} < threshold={min_conf}",
            )
        )

    capability = idea.get("capability")
    ignored = set(CONSTRAINTS["scout"]["ignore_capabilities"])
    if capability in ignored:
        cvfs.append(
            raise_cvf(
                code="CAPABILITY_IGNORED",
                severity=Severity.LOW,
                agent="scout",
                detail=f"capability '{capability}' is in ignore list",
            )
        )

    return cvfs


def validate_executor_trial(
    trial: TrialAuditBundle,
    concurrent_trials: int,
) -> List[ConstitutionalViolationFlag]:
    cvfs: List[ConstitutionalViolationFlag] = []
    cons = CONSTRAINTS["executor"]

    if trial.cost_estimate > cons["cost_ceiling"]:
        cvfs.append(
            raise_cvf(
                code="COST_EXCEEDS_CEILING",
                severity=Severity.HIGH,
                agent="executor",
                detail=f"cost_estimate={trial.cost_estimate} > {cons['cost_ceiling']}",
            )
        )

    if concurrent_trials >= cons["max_concurrent_trials"]:
        cvfs.append(
            raise_cvf(
                code="CONCURRENT_TRIAL_LIMIT",
                severity=Severity.HIGH,
                agent="executor",
                detail=f"concurrent_trials={concurrent_trials} >= max={cons['max_concurrent_trials']}",
            )
        )

    # Data access policy placeholder – wire to your env metadata
    data_access_mode = trial.inputs.get("data_access_mode", "unknown")
    if data_access_mode not in cons["data_access"]:
        cvfs.append(
            raise_cvf(
                code="DATA_ACCESS_PROHIBITED",
                severity=Severity.CRITICAL,
                agent="executor",
                detail=f"data_access_mode={data_access_mode} not in allowed={cons['data_access']}",
            )
        )

    # Forbidden models
    forbidden = set(cons["forbidden_models"])
    used = set(trial.models_used)
    if forbidden & used:
        cvfs.append(
            raise_cvf(
                code="UNVERIFIED_MODEL_USED",
                severity=Severity.CRITICAL,
                agent="executor",
                detail=f"forbidden_models_used={list(forbidden & used)}",
            )
        )

    # Uncertainty band – treat as danger, not opportunity
    low, high = CONSTRAINTS["boardroom"]["uncertainty_band"]
    confidence = float(trial.results.get("confidence", 0.0))
    if low <= confidence <= high:
        cvfs.append(
            raise_cvf(
                code="UNCERTAINTY_ZONE",
                severity=Severity.HIGH,
                agent="executor",
                detail=f"confidence={confidence} in [{low}, {high}]",
            )
        )

    # Missing audit metadata
    required_timestamps = {"proposed", "approved"}
    if not required_timestamps.issubset(trial.timestamps.keys()):
        cvfs.append(
            raise_cvf(
                code="AUDIT_INCOMPLETE",
                severity=Severity.HIGH,
                agent="executor",
                detail=f"missing timestamps: {required_timestamps - set(trial.timestamps.keys())}",
            )
        )

    return cvfs


def boardroom_decision(
    trial: TrialAuditBundle,
    cvfs: List[ConstitutionalViolationFlag],
    prior_history: Optional[Dict[str, Any]] = None,
) -> Tuple[str, List[ConstitutionalViolationFlag]]:
    """
    Returns decision: "auto_reject" | "auto_approve" | "vote" | "escalate_human"
    plus any additional CVFs raised at the BOARDROOM layer.
    """
    decision_cvfs: List[ConstitutionalViolationFlag] = []
    cons = CONSTRAINTS["boardroom"]

    if contains_critical(cvfs):
        return "auto_reject", decision_cvfs

    # Check explicit flags in results metadata
    flags = set(trial.results.get("flags", []))

    if any(flag in cons["auto_reject_if"] for flag in flags):
        decision_cvfs.append(
            raise_cvf(
                code="BOARDROOM_AUTO_REJECT_FLAG",
                severity=Severity.HIGH,
                agent="boardroom",
                detail=f"flags={flags} intersect auto_reject_if={cons['auto_reject_if']}",
            )
        )
        return "auto_reject", decision_cvfs

    # Escalation band for confidence
    low, high = cons["uncertainty_band"]
    conf = float(trial.results.get("confidence", 0.0))
    if low <= conf <= high:
        decision_cvfs.append(
            raise_cvf(
                code="BOARDROOM_UNCERTAINTY_ESCALATION",
                severity=Severity.HIGH,
                agent="boardroom",
                detail=f"confidence={conf} in grey zone",
            )
        )
        return "escalate_human", decision_cvfs

    # Touches production / security / new capability → require vote
    if any(flag in cons["require_vote_if"] for flag in flags):
        return "vote", decision_cvfs

    # For safe classes, auto-approve if confidence high enough
    auto_threshold = CONSTRAINTS["executor"]["auto_approve_threshold"]
    if conf >= auto_threshold and "safe_operational_improvement" in flags:
        return "auto_approve", decision_cvfs

    # Default path: require vote
    return "vote", decision_cvfs


# ---------- LEDGER HELPERS ----------

def _canonical_json(data: Dict[str, Any]) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"))


def compute_hash(data: Dict[str, Any]) -> str:
    return hashlib.sha256(_canonical_json(data).encode("utf-8")).hexdigest()


def build_ledger_entry(
    event_type: EventType,
    payload: Dict[str, Any],
    previous_entry_hash: Optional[str],
    signer: str,
) -> LedgerEntry:
    """
    signer: name of signing entity, e.g. "BOARDROOM-13"
    """
    timestamp = datetime.now(timezone.utc).isoformat()
    base = {
        "previous_entry_hash": previous_entry_hash,
        "event_type": event_type.value,
        "payload": payload,
        "timestamp": timestamp,
        "signer": signer,
    }
    entry_id = compute_hash(base)
    signature = entry_id  # placeholder; swap for real crypto later

    return LedgerEntry(
        entry_id=entry_id,
        previous_entry_hash=previous_entry_hash,
        event_type=event_type,
        payload=payload,
        timestamp=timestamp,
        signature=signature,
    )


def append_ledger_entry(
    entry: LedgerEntry,
    file_path: str,
) -> None:
    """
    Very simple append-only JSONL file.
    """
    line = _canonical_json(entry.to_dict()) + "\n"
    with open(file_path, "a", encoding="utf-8") as f:
        f.write(line)


# ---------- FACTORIES / SHORTCUTS ----------

def new_trial_bundle(
    initiator: Role,
    purpose: str,
    inputs: Dict[str, Any],
    environment: str,
    models_used: List[str],
    cost_estimate: float,
    now: Optional[datetime] = None,
) -> TrialAuditBundle:
    t = now or datetime.now(timezone.utc)
    iso = t.isoformat()
    return TrialAuditBundle(
        trial_id=str(uuid.uuid4()),
        initiator=initiator,
        purpose=purpose,
        inputs=inputs,
        environment=environment,
        models_used=models_used,
        cost_estimate=cost_estimate,
        timestamps={"proposed": iso},
        results={},
        cvfs=[],
    )
