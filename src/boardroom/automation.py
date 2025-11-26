# -*- coding: utf-8 -*-
"""
Post-governance automation dispatcher.

This module implements the mechanical layer that drives real automation
off successful governance commits.

Flow:
1. Governance decision is committed
2. Decision is cryptographically anchored
3. dispatch_from_commit() routes to appropriate pipeline
4. Execution outcome is logged

Guarantees:
- One governance decision → zero or one automation execution
- Every trigger is logged
- Automation is replayable, inspectable, and auditable
"""

import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Callable


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DATA_ROOT = Path("DATA")
AUTOMATION_LOG = DATA_ROOT / "_automation_log.json"
PIPELINES_DIR = DATA_ROOT / "_pipelines"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def iso_now() -> str:
    """UTC timestamp in ISO 8601 format."""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def ensure_pipelines_dir() -> None:
    """Ensure the pipelines directory exists."""
    PIPELINES_DIR.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# Log Operations
# ---------------------------------------------------------------------------

def load_log() -> List[Dict[str, Any]]:
    """Load the automation execution log."""
    if not AUTOMATION_LOG.exists():
        return []
    try:
        return json.loads(AUTOMATION_LOG.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, IOError):
        return []


def persist_log_entry(entry: Dict[str, Any]) -> None:
    """Append an entry to the automation log."""
    log = load_log()
    log.append(entry)
    AUTOMATION_LOG.parent.mkdir(parents=True, exist_ok=True)
    AUTOMATION_LOG.write_text(json.dumps(log, indent=2), encoding="utf-8")


def get_recent_executions(limit: int = 10) -> List[Dict[str, Any]]:
    """Get the most recent automation executions."""
    log = load_log()
    return log[-limit:] if log else []


# ---------------------------------------------------------------------------
# Pipeline Handlers
# ---------------------------------------------------------------------------

def run_poc_pipeline(commit: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle PROPOSE_POC action.

    Creates a POC workspace and records the trigger.
    """
    ensure_pipelines_dir()
    poc_dir = PIPELINES_DIR / "poc"
    poc_dir.mkdir(parents=True, exist_ok=True)

    # Create a POC trigger file
    trigger_file = poc_dir / f"poc_trigger_{commit['session_id']}.json"
    trigger_data = {
        "triggered_at": iso_now(),
        "commit_id": commit["commit_id"],
        "session_id": commit["session_id"],
        "topic": commit["topic"],
        "action": "PROPOSE_POC",
        "status": "PENDING_IMPLEMENTATION",
    }
    trigger_file.write_text(json.dumps(trigger_data, indent=2), encoding="utf-8")

    return {
        "pipeline": "poc",
        "trigger_file": str(trigger_file),
        "status": "TRIGGERED",
    }


def run_data_pipeline(commit: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle REQUEST_DATA action.

    Creates a data request workspace.
    """
    ensure_pipelines_dir()
    data_dir = PIPELINES_DIR / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    trigger_file = data_dir / f"data_request_{commit['session_id']}.json"
    trigger_data = {
        "triggered_at": iso_now(),
        "commit_id": commit["commit_id"],
        "session_id": commit["session_id"],
        "topic": commit["topic"],
        "action": "REQUEST_DATA",
        "status": "PENDING_DATA_COLLECTION",
    }
    trigger_file.write_text(json.dumps(trigger_data, indent=2), encoding="utf-8")

    return {
        "pipeline": "data",
        "trigger_file": str(trigger_file),
        "status": "TRIGGERED",
    }


def run_review_pipeline(commit: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle REQUEST_INPUTS action.

    Creates a review request workspace.
    """
    ensure_pipelines_dir()
    review_dir = PIPELINES_DIR / "review"
    review_dir.mkdir(parents=True, exist_ok=True)

    trigger_file = review_dir / f"review_request_{commit['session_id']}.json"
    trigger_data = {
        "triggered_at": iso_now(),
        "commit_id": commit["commit_id"],
        "session_id": commit["session_id"],
        "topic": commit["topic"],
        "action": "REQUEST_INPUTS",
        "status": "PENDING_REVIEW",
    }
    trigger_file.write_text(json.dumps(trigger_data, indent=2), encoding="utf-8")

    return {
        "pipeline": "review",
        "trigger_file": str(trigger_file),
        "status": "TRIGGERED",
    }


def run_approval_pipeline(commit: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle APPROVE_ACTION or similar approval actions.

    Records the approval for downstream processing.
    """
    ensure_pipelines_dir()
    approval_dir = PIPELINES_DIR / "approvals"
    approval_dir.mkdir(parents=True, exist_ok=True)

    trigger_file = approval_dir / f"approval_{commit['session_id']}.json"
    trigger_data = {
        "triggered_at": iso_now(),
        "commit_id": commit["commit_id"],
        "session_id": commit["session_id"],
        "topic": commit["topic"],
        "action": commit["governance"]["consensus_action"],
        "status": "APPROVED",
        "merkle_root": commit.get("merkle_receipt", {}).get("root"),
    }
    trigger_file.write_text(json.dumps(trigger_data, indent=2), encoding="utf-8")

    return {
        "pipeline": "approvals",
        "trigger_file": str(trigger_file),
        "status": "APPROVED",
    }


# ---------------------------------------------------------------------------
# Action Router
# ---------------------------------------------------------------------------

# Map consensus actions to pipeline handlers
ACTION_HANDLERS: Dict[str, Callable[[Dict[str, Any]], Dict[str, Any]]] = {
    "PROPOSE_POC": run_poc_pipeline,
    "REQUEST_DATA": run_data_pipeline,
    "REQUEST_INPUTS": run_review_pipeline,
    "APPROVE_ACTION": run_approval_pipeline,
}


def dispatch_from_commit(commit_path: Path) -> Dict[str, Any]:
    """
    Main dispatch entry point.

    Loads the committed decision, routes to appropriate pipeline,
    and logs the execution outcome.

    Args:
        commit_path: Path to the governance commit JSON file

    Returns:
        Execution result dict
    """
    commit = json.loads(commit_path.read_text(encoding="utf-8"))
    action = commit["governance"]["consensus_action"]

    # Find handler
    handler = ACTION_HANDLERS.get(action)

    execution_result: Dict[str, Any] = {
        "timestamp": iso_now(),
        "commit_id": commit["commit_id"],
        "session_id": commit["session_id"],
        "action": action,
        "commit_path": str(commit_path),
        "status": "IGNORED",
        "pipeline_result": None,
        "error": None,
    }

    if handler:
        try:
            pipeline_result = handler(commit)
            execution_result["status"] = "EXECUTED"
            execution_result["pipeline_result"] = pipeline_result
        except Exception as e:
            execution_result["status"] = "ERROR"
            execution_result["error"] = str(e)
    else:
        execution_result["status"] = "NO_HANDLER"

    # Persist to automation log
    persist_log_entry(execution_result)

    return execution_result


def register_handler(action: str, handler: Callable[[Dict[str, Any]], Dict[str, Any]]) -> None:
    """
    Register a custom handler for an action.

    Args:
        action: The consensus action string (e.g., "DEPLOY_TO_PROD")
        handler: Function that takes a commit dict and returns a result dict
    """
    ACTION_HANDLERS[action] = handler


def list_handlers() -> List[str]:
    """List all registered action handlers."""
    return list(ACTION_HANDLERS.keys())


# ---------------------------------------------------------------------------
# Introspection
# ---------------------------------------------------------------------------

def get_pipeline_status() -> Dict[str, Any]:
    """
    Get current status of all pipelines.

    Returns:
        Dict with pipeline directories and their contents
    """
    ensure_pipelines_dir()

    status: Dict[str, Any] = {
        "pipelines_dir": str(PIPELINES_DIR),
        "pipelines": {},
    }

    for pipeline_dir in PIPELINES_DIR.iterdir():
        if pipeline_dir.is_dir():
            files = list(pipeline_dir.glob("*.json"))
            status["pipelines"][pipeline_dir.name] = {
                "path": str(pipeline_dir),
                "trigger_count": len(files),
                "triggers": [f.name for f in files],
            }

    return status
