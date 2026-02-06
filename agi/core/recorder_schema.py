"""Recorder event schema validation module.

Provides validate_event(event: dict) that enforces structure using JSON Schema.
Maps event_type -> schema file located under schemas/ (or schemas/recorder/).

Requires: jsonschema (pip install jsonschema)
"""
from __future__ import annotations
from pathlib import Path
import json
from typing import Dict, Any
from jsonschema import Draft7Validator, exceptions as js_exc

# Root of repository (assumes this file lives in agi/core/)
REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMAS_DIR_PRIMARY = REPO_ROOT / "schemas"
SCHEMAS_DIR_RECORDER = SCHEMAS_DIR_PRIMARY / "recorder"

# Mapping of event_type to schema filename (search recorder first, then primary)
EVENT_SCHEMAS: Dict[str, str] = {
    "event_heartbeat": "event_heartbeat.json",
    "event_manifest": "event_manifest.json",
    "event_anchor_created": "event_anchor_created.json",
    "event_agent_safety": "event_agent_safety.json",
    "event_anchor": "event_anchor.json",  # legacy anchor emission
}

class SchemaError(Exception):
    """Raised when schema validation fails or schema cannot be loaded."""


def _load_raw_schema(filename: str) -> Dict[str, Any]:
    # Prefer recorder subdirectory if file exists there
    candidate_recorder = SCHEMAS_DIR_RECORDER / filename
    if candidate_recorder.exists():
        return json.loads(candidate_recorder.read_text(encoding="utf-8"))
    candidate_primary = SCHEMAS_DIR_PRIMARY / filename
    if candidate_primary.exists():
        return json.loads(candidate_primary.read_text(encoding="utf-8"))
    raise SchemaError(f"Schema file not found for: {filename}")


def _build_validator(filename: str) -> Draft7Validator:
    schema_dict = _load_raw_schema(filename)
    return Draft7Validator(schema_dict)


def validate_event(event: Dict[str, Any]) -> None:
    """Validate a recorder event dict against its declared schema.

    Raises SchemaError if validation fails.
    """
    if not isinstance(event, dict):
        raise SchemaError("Event must be a dict")
    etype = event.get("event_type")
    if not etype:
        raise SchemaError("Event missing 'event_type'")
    if etype not in EVENT_SCHEMAS:
        raise SchemaError(f"Unknown event_type: {etype}")
    validator = _build_validator(EVENT_SCHEMAS[etype])
    errors = sorted(validator.iter_errors(event), key=lambda e: e.path)
    if errors:
        formatted = [f"{'/'.join(map(str, err.path)) or '<root>'}: {err.message}" for err in errors]
        raise SchemaError("Schema validation failed: " + " | ".join(formatted))


def load_and_validate_file(path: Path) -> Dict[str, Any]:
    """Load JSON from path and validate; returns the parsed dict."""
    try:
        raw = path.read_text(encoding="utf-8")
        data = json.loads(raw)
    except Exception as exc:  # pragma: no cover
        raise SchemaError(f"Failed to parse JSON {path}: {exc}")
    validate_event(data)
    return data


__all__ = ["validate_event", "SchemaError", "load_and_validate_file"]
