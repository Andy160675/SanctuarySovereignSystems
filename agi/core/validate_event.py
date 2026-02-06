"""CLI wrapper to validate a recorder event JSON file.

Usage:
  python -m agi.core.validate_event --file path/to/event.json
  python agi/core/validate_event.py --file path/to/event.json

Optional:
  --schema <name> (forces schema filename mapping; otherwise uses event_type)
Exit codes:
  0 -> success
  1 -> failure
"""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path
from typing import Optional
from .recorder_schema import validate_event, SchemaError


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Validate recorder event JSON against schema")
    p.add_argument("--file", required=True, help="Path to event JSON file")
    p.add_argument("--schema", required=False, help="Override schema name (debug only)")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    path = Path(args.file)
    if not path.exists():
        print(f"[ERROR] File not found: {path}", file=sys.stderr)
        return 1
    try:
        raw = path.read_text(encoding="utf-8")
        data = json.loads(raw)
    except Exception as exc:
        print(f"[ERROR] Failed to parse JSON: {exc}", file=sys.stderr)
        return 1
    if args.schema:
        # force override of event_type for validation mapping
        data["event_type"] = args.schema
    try:
        validate_event(data)
    except SchemaError as exc:
        print(f"[SCHEMA FAIL] {exc}", file=sys.stderr)
        return 1
    print(f"[SCHEMA OK] {path}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
