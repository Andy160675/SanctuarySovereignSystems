#!/usr/bin/env python3
"""
Keyed Command - Unified Autobuild Ignition
===========================================
Enables autobuild with a single command that combines:
- Passcode verification (authorization)
- Task prompt capture (intent)
- Evidence logging (audit trail)

Usage:
    python keyed_command.py <passcode> <task prompt...>

Example:
    python keyed_command.py 432697 generate cyber threat hunting actuator
    python keyed_command.py 432697 rebuild runtime images
    python keyed_command.py 432697 run full zk-proof regression

The passcode is verified against SHA-256 hash stored in config/autobuild.json.
The task prompt is logged to logs/autobuild_tasks.jsonl for forensic evidence.
"""

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

# Configuration
SCRIPT_DIR = Path(__file__).resolve().parent
ROOT_DIR = SCRIPT_DIR.parents[1]
CONFIG_PATH = ROOT_DIR / "config" / "autobuild.json"
TASK_LOG_PATH = ROOT_DIR / "logs" / "autobuild_tasks.jsonl"


def load_config() -> dict:
    """Load autobuild configuration."""
    if not CONFIG_PATH.exists():
        print(f"ERROR: Config not found: {CONFIG_PATH}")
        sys.exit(1)
    with CONFIG_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_config(cfg: dict) -> None:
    """Save autobuild configuration."""
    with CONFIG_PATH.open("w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)


def hash_passcode(passcode: str) -> str:
    """Hash passcode using SHA-256."""
    return hashlib.sha256(passcode.encode("utf-8")).hexdigest()


def log_task(entry: dict) -> None:
    """Append task entry to JSONL log."""
    TASK_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with TASK_LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def main():
    """Main entry point for keyed command."""
    if len(sys.argv) < 3:
        print("Usage: python keyed_command.py <passcode> <task prompt>")
        print()
        print("Example:")
        print("  python keyed_command.py 432697 generate cyber threat hunting actuator")
        sys.exit(1)

    passcode = sys.argv[1]
    task_prompt = " ".join(sys.argv[2:])

    # Load and verify
    cfg = load_config()

    if hash_passcode(passcode) != cfg.get("passcode_hash"):
        print("INVALID PASSCODE. Autobuild remains locked.")
        sys.exit(1)

    # Enable autobuild
    cfg["enabled"] = True
    cfg["last_changed_by"] = "keyed_command"
    cfg["last_changed_at_utc"] = datetime.now(timezone.utc).isoformat()
    save_config(cfg)

    # Log the task
    task_entry = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "task_prompt": task_prompt,
        "invocation_mode": "passcode_inline",
        "autobuild_enabled": True
    }
    log_task(task_entry)

    print("=" * 60)
    print("AUTOBUILD ENABLED via passcode.")
    print(f"Task captured: {task_prompt}")
    print("=" * 60)
    print()
    print(f"Evidence logged to: {TASK_LOG_PATH}")
    print()

    # Return task prompt for potential chaining
    return task_prompt


if __name__ == "__main__":
    main()
