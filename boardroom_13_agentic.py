#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Boardroom 13 - Agentic Test Harness (with audit wiring)

- Loads the constitutional genome (prompts/boardroom_master.txt).
- Instantiates the 13 roles (from src.boardroom.roles).
- Runs a console-driven session where each role produces a short, auditable opinion.
- Persists:
  - Per-session snapshot: DATA/_work/snapshots/<session_id>.json
  - Rolling audit index:  DATA/_work/audit.json

Recorder and Archivist evidence anchors are wired to these real files.
"""

import sys
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

# Import role definitions
try:
    from src.boardroom.roles import ROLES
except Exception:
    # If run from repo root where src is not a package path, try relative import fallback
    sys.path.insert(0, str(Path(__file__).parent))
    from src.boardroom.roles import ROLES  # type: ignore

PROMPT_PATH = Path("prompts") / "boardroom_master.txt"

# --- Audit / storage paths ----------------------------------------------------

DATA_ROOT = Path("DATA")
WORK_DIR = DATA_ROOT / "_work"
SNAPSHOT_DIR = WORK_DIR / "snapshots"
AUDIT_FILE = WORK_DIR / "audit.json"


def load_constitution() -> str:
    if not PROMPT_PATH.exists():
        raise FileNotFoundError(f"Constitutional prompt not found: {PROMPT_PATH}")
    return PROMPT_PATH.read_text(encoding="utf-8")


def iso_now() -> str:
    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


def ensure_work_dirs() -> None:
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)


def new_session_id() -> str:
    # Stable, filesystem-safe session identifier
    return datetime.utcnow().strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:8]


def persist_audit(topic: str, outputs: List[Dict[str, Any]], session_id: str) -> Path:
    """
    Write a full snapshot for this topic + role outputs, and update the rolling audit index.

    Snapshot: DATA/_work/snapshots/<session_id>.json
    Audit:    DATA/_work/audit.json (list of shallow entries)
    """
    ensure_work_dirs()

    snapshot_path = SNAPSHOT_DIR / f"{session_id}.json"
    snapshot_record = {
        "session_id": session_id,
        "timestamp": iso_now(),
        "topic": topic,
        "roles": outputs,
        "snapshot_path": str(snapshot_path),
    }

    snapshot_path.write_text(json.dumps(snapshot_record, indent=2), encoding="utf-8")

    # Update/initialise audit.json as a list
    if AUDIT_FILE.exists():
        try:
            existing = json.loads(AUDIT_FILE.read_text(encoding="utf-8"))
            if not isinstance(existing, list):
                existing = []
        except Exception:
            existing = []
    else:
        existing = []

    audit_entry = {
        "session_id": session_id,
        "timestamp": snapshot_record["timestamp"],
        "topic": topic,
        "snapshot_path": str(snapshot_path),
    }
    existing.append(audit_entry)
    AUDIT_FILE.write_text(json.dumps(existing, indent=2), encoding="utf-8")

    return snapshot_path


def wire_recorder_and_archivist(outputs: List[Dict[str, Any]], snapshot_path: Path) -> None:
    """
    Mutate Recorder + Archivist outputs so their evidence anchors point at real files.

    - Recorder.evidence += [file:<snapshot>, file:<audit.json>]
    - Archivist.evidence += [file:<snapshot>]
    """
    snapshot_anchor = f"file:{snapshot_path}"
    audit_anchor = f"file:{AUDIT_FILE}"

    for o in outputs:
        key = o.get("role_key")
        if key not in ("recorder", "archivist"):
            continue

        anchors = list(o.get("evidence") or [])
        if key == "recorder":
            if snapshot_anchor not in anchors:
                anchors.append(snapshot_anchor)
            if audit_anchor not in anchors:
                anchors.append(audit_anchor)
        elif key == "archivist":
            if snapshot_anchor not in anchors:
                anchors.append(snapshot_anchor)

        o["evidence"] = anchors


# --- Heuristic RoleAgent (can later be swapped for LLM-backed agent) ---------

class RoleAgent:
    def __init__(self, role):
        self.role = role

    def evaluate(self, topic: str, context: str = "") -> Dict[str, Any]:
        """
        Produce a small structured output according to the constitutional genome.
        The evaluation is heuristic and deterministic for local testing.
        """
        ts = iso_now()
        verdict = self._verdict(topic, context)
        rationale = self._rationale(topic, context)
        action = self._action(topic, context)
        evidence = self._evidence_anchor(topic, context)

        out = {
            "role_key": self.role.key,
            "role_title": self.role.title,
            "timestamp": ts,
            "verdict": verdict,
            "rationale": rationale,
            "action": action,
            "evidence": evidence,
        }
        return out

    def _verdict(self, topic: str, context: str) -> str:
        t = topic.lower()
        key = self.role.key
        if key == "recorder":
            return f"Record accepted: snapshot created for topic '{topic}'."
        if key == "chair":
            return f"Proceed to deliberation on '{topic}' under standard governance procedure."
        if key == "ethicist":
            return (
                "Flagged for ethical review due to potential human-impact signals."
                if any(w in t for w in ["risk", "harm", "privacy", "bias"])
                else "No immediate ethical red flags detected."
            )
        if key == "engineer":
            return "Technical feasibility appears plausible; requires proof-of-concept for verification."
        if key == "empath":
            return "Prioritise human-context checks and empathetic framing in communications."
        if key == "archivist":
            return "Ensure archival storage and provenance metadata attached to records."
        if key == "strategist":
            return "Align short-term tactics to a 90-day objective; propose milestones."
        if key == "guardian":
            return "Apply security and access restrictions until integrity is verified."
        if key == "analyst":
            return f"Initial analytic check: topic length {len(topic.split())} words; request data for metrics."
        if key == "linguist":
            return "Recommend concise, disambiguated phrasing; remove ambiguous adjectives."
        if key == "jurist":
            return "Preliminary legal scan: escalate if regulated elements (personal data, contracts) are involved."
        if key == "creator":
            return "Offer exploratory alternative that preserves safety constraints and optionality."
        if key == "observer":
            return "Observational note: maintain meta-awareness of framing and bounded assumptions."
        return "No verdict produced."

    def _rationale(self, topic: str, context: str) -> List[str]:
        key = self.role.key
        if key == "recorder":
            return [f"Snapshot at {iso_now()}", "Canonical audit trail entry created."]
        if key == "chair":
            return ["Procedural balance", "Time-box deliberation", "Seek consensus >= 7/13"]
        if key == "ethicist":
            return ["Check for harm indicators", "Assess affected stakeholders"]
        if key == "engineer":
            return ["Feasibility heuristic", "Architectural constraints", "Test plan recommendation"]
        if key == "empath":
            return ["Human impact focus", "Prefer harm-minimising language"]
        if key == "archivist":
            return ["Provenance required", "Store raw and processed copies"]
        if key == "strategist":
            return ["Define measurable milestones", "Map to organizational objectives"]
        if key == "guardian":
            return ["Limit access", "Require integrity proofs", "Check encryption at rest"]
        if key == "analyst":
            return [f"Word count: {len(topic.split())}", "Request structured data for validation"]
        if key == "linguist":
            return ["Clarify ambiguous terms", "Standardise terminology", "Provide short definitions"]
        if key == "jurist":
            return ["Identify applicable regulation", "Recommend legal counsel if needed"]
        if key == "creator":
            return ["Suggest low-risk prototype", "Encourage controlled A/B testing"]
        if key == "observer":
            return ["Note potential groupthink", "Recommend short pause for meta-check"]
        return []

    def _action(self, topic: str, context: str) -> str:
        key = self.role.key
        t = topic.lower()
        if key in ("recorder", "archivist"):
            return "NO_ACTION (recording)"
        if key == "chair":
            return "CALL_RECONCILIATION" if "escalate" in t else "REQUEST_INPUTS"
        if key == "ethicist":
            return "REQUEST_ETHICS_REVIEW" if any(w in t for w in ["risk", "harm", "privacy"]) else "NO_ACTION"
        if key == "engineer":
            return "PROPOSE_POC"
        if key == "guardian":
            return "LOCK_READ_ACCESS" if any(w in t for w in ["secret", "credential", "token"]) else "NO_ACTION"
        if key == "analyst":
            return "REQUEST_DATA"
        if key == "jurist":
            return "REFER_TO_LEGAL" if any(w in t for w in ["contract", "law", "regulation", "privacy"]) else "NO_ACTION"
        return "NO_ACTION"

    def _evidence_anchor(self, topic: str, context: str) -> List[str]:
        return [f"local:{self.role.key}:topic_summary:{len(topic)}"]


# --- Reconciliation logic -----------------------------------------------------

def reconciliation_cycle(topic: str, outputs: List[Dict[str, Any]]):
    print("\n=== Reconciliation Cycle Initiated ===")
    distinct_actions = list({o["action"] for o in outputs if o.get("action") not in (None, "", "NO_ACTION", "NO_ACTION (recording)")})
    print("Distinct actions under contention:", distinct_actions)
    if not distinct_actions:
        print("No actionable conflicts detected; exiting Reconciliation.")
        return
    focus = distinct_actions[0]
    print(f"Chair calls focused responses on: {focus}")
    for o in outputs:
        role = o["role_key"]
        reply = focused_response(role, focus, topic)
        print(f"ROLE: {role} -> {reply}")
    print("Chair will re-evaluate and either call another cycle or defer for evidence retrieval.")
    print("=== Reconciliation Cycle Complete (simulated) ===\n")


def focused_response(role_key: str, focus: str, topic: str) -> str:
    if role_key == "chair":
        return "I moderate: ensure evidence retrieval before final."
    if role_key == "recorder":
        return "Snapshot recorded; await further instruction."
    if role_key == "ethicist":
        return "Support focused review if human-impact potential exists."
    if role_key == "engineer":
        return "Support with PoC only with test harness and safety checks."
    if role_key == "empath":
        return "Ensure stakeholders are consulted before execution."
    if role_key == "archivist":
        return "Provide provenance references; mark for retention."
    if role_key == "strategist":
        return "Assess alignment with strategic objectives before commit."
    if role_key == "guardian":
        return "Require integrity proof and least-privileged access."
    if role_key == "analyst":
        return "Quantify expected benefit vs. risk with a simple KPI."
    if role_key == "linguist":
        return "Clarify language for operational instructions."
    if role_key == "jurist":
        return "Hold until compliance review confirms permissibility."
    if role_key == "creator":
        return "Propose a safe, isolated experiment to validate."
    if role_key == "observer":
        return "Monitor for emergent assumptions and cognitive bias."
    return "No focused response."


# --- Main session loop --------------------------------------------------------

def run_session():
    _constitution = load_constitution()  # Loaded for future LLM use
    print("Loaded constitutional genome:", PROMPT_PATH)
    print("Boardroom 13 - Agentic Test Harness (local, deterministic, audit-wired)")
    print("Recorder/Archivist now write to DATA/_work/*.json")
    print("-" * 72)
    print("Enter a topic or brief request (empty line to quit).")

    while True:
        try:
            topic = input("\nTOPIC> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting.")
            break
        if not topic:
            print("No topic entered. Exiting.")
            break

        context = ""  # placeholder for future context parameter
        session_id = new_session_id()

        agents = [RoleAgent(r) for r in ROLES]
        outputs: List[Dict[str, Any]] = []
        for agent in agents:
            out = agent.evaluate(topic, context)
            outputs.append(out)

        # Persist snapshot + audit index, then wire anchors
        snapshot_path = persist_audit(topic, outputs, session_id)
        wire_recorder_and_archivist(outputs, snapshot_path)

        # Print each role's output in canonical audited structure
        print("\n--- ROLE OUTPUTS ---")
        for o in outputs:
            header = f"ROLE: {o['role_key']} | TIMESTAMP: {o['timestamp']}"
            print(header)
            print("VERDICT:", o['verdict'])
            print("RATIONALE:")
            for r in o['rationale']:
                print("-", r)
            print("ACTION:", o['action'])
            print("EVIDENCE:", ", ".join(o['evidence']))
            print("-" * 40)

        # Simple consensus check (keyword aggregation)
        recommendations = [o["action"] for o in outputs if o.get("action") and not str(o["action"]).startswith("NO_ACTION")]
        if recommendations:
            freq: Dict[str, int] = {}
            for r in recommendations:
                freq[r] = freq.get(r, 0) + 1
            most_common_action, count = max(freq.items(), key=lambda x: x[1])
            print("\nChair summary:")
            print(f"Most common recommended action: {most_common_action} (count={count})")
            if count >= 7:
                print("Consensus achieved (>=7). System may proceed with:", most_common_action)
            else:
                print("No supermajority. Chair recommends a Reconciliation Cycle.")
                reconciliation_cycle(topic, outputs)
        else:
            print("\nNo role requested an explicit action. Chair may close the session.")

        print(f"\nRecorder: Final snapshot written to {snapshot_path}")
        print(f"Audit index updated at {AUDIT_FILE}")
        print("-" * 72)


if __name__ == "__main__":
    try:
        run_session()
    except Exception as exc:
        print("Error running Boardroom harness:", str(exc))
        raise
