#!/usr/bin/env python3
"""
Emergency Freeze Toggle - System-wide halt control
===================================================

Control code: 7956 (SHA-256 verified)

When engaged:
- All missions HALT (Coordinator refuses new start_mission)
- All votes HALT
- All actuators REJECT execution
- Dynamic scaling LOCKS
- Autobuild is FORCED OFF

Read-only services remain active:
- Ledger, Watcher, Sentinel, Audit (read-only)
- Health endpoints (live)
- WebSocket clients (see GLOBAL_FREEZE=true)

Usage:
    python toggle_freeze.py on 7956   # Engage emergency freeze
    python toggle_freeze.py off 7956  # Disengage emergency freeze
"""

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

# State file location (relative to repo root)
STATE_PATH = Path(__file__).parent.parent.parent / "config" / "system_state.json"

# SHA-256 hash of the freeze code "7956"
FREEZE_HASH = "0c1c7d2c839afcc84ba8c2769a54c0a4189f5943175dc0fa726c5a0ad5bb44b7"


def sha256(s: str) -> str:
    """Compute SHA-256 hash of a string."""
    return hashlib.sha256(s.encode()).hexdigest()


def load_state() -> dict:
    """Load current system state from JSON file."""
    if not STATE_PATH.exists():
        return {
            "autobuild_enabled": False,
            "emergency_freeze": False,
            "last_autobuild_change_utc": None,
            "last_emergency_freeze_utc": None,
            "last_changed_by": None
        }
    with STATE_PATH.open() as f:
        return json.load(f)


def save_state(state: dict) -> None:
    """Save system state to JSON file."""
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with STATE_PATH.open("w") as f:
        json.dump(state, f, indent=2)


def main():
    if len(sys.argv) != 3:
        print("Usage: python toggle_freeze.py <on|off> <code>")
        print("")
        print("  on  7956  - Engage system-wide emergency freeze")
        print("  off 7956  - Disengage emergency freeze")
        sys.exit(1)

    mode = sys.argv[1].lower()
    code = sys.argv[2]

    # Verify freeze code
    if sha256(code) != FREEZE_HASH:
        print("ERROR: INVALID FREEZE CODE")
        print("Emergency freeze requires the correct 4-digit code.")
        sys.exit(1)

    state = load_state()
    timestamp = datetime.now(timezone.utc).isoformat()

    if mode == "on":
        if state.get("emergency_freeze"):
            print("WARNING: Emergency freeze is already ACTIVE")
        state["emergency_freeze"] = True
        state["autobuild_enabled"] = False  # Force autobuild off during freeze
        state["last_emergency_freeze_utc"] = timestamp
        state["last_changed_by"] = "emergency_freeze_on"
        print("=" * 60)
        print("🛑 EMERGENCY FREEZE ENGAGED")
        print("=" * 60)
        print("- All missions: HALTED")
        print("- All votes: HALTED")
        print("- All actuators: LOCKED")
        print("- Dynamic scaling: FROZEN")
        print("- Autobuild: FORCED OFF")
        print("")
        print("Read-only services remain active.")
        print(f"Timestamp: {timestamp}")
        print("=" * 60)

    elif mode == "off":
        if not state.get("emergency_freeze"):
            print("WARNING: Emergency freeze is already INACTIVE")
        state["emergency_freeze"] = False
        state["last_emergency_freeze_utc"] = timestamp
        state["last_changed_by"] = "emergency_freeze_off"
        print("=" * 60)
        print("✅ EMERGENCY FREEZE DISENGAGED")
        print("=" * 60)
        print("- System operations: RESUMING")
        print("- Autobuild: Still OFF (use 432697 to re-enable)")
        print(f"Timestamp: {timestamp}")
        print("=" * 60)

    else:
        print("ERROR: Mode must be 'on' or 'off'")
        sys.exit(1)

    save_state(state)
    print(f"\nState saved to: {STATE_PATH}")


if __name__ == "__main__":
    main()
