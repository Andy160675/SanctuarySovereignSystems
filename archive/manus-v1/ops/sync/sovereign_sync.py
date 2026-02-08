"""
Sovereign Sync Operations
==========================
Condensed from bLADE2-OFFFLINE sync/push macro.
All sync operations are constitutional signals routed through the kernel.
No silent pushes. No unaudited commits.
"""

from __future__ import annotations
import subprocess
from datetime import datetime, timezone
from typing import Optional
from engine.signals.typed_signal import (
    TypedSignal, SignalType, AuthorityLevel, create_signal,
)


class SovereignSync:
    """
    Constitutional sync engine.
    Every push is a typed signal with evidence hash.
    """

    def __init__(self, repo_path: str, operator_id: str):
        self._repo_path = repo_path
        self._operator_id = operator_id

    def sync_push(self, commit_message: Optional[str] = None) -> Optional[TypedSignal]:
        """
        Constitutional commit and push.
        Auto-generates sovereign commit message if none provided.
        """
        timestamp = datetime.now(timezone.utc).isoformat()
        if commit_message is None:
            commit_message = f"sovereign-sync: auto-commit | {timestamp}"

        # Stage, commit, push
        results = {}
        commands = [
            "git add .",
            f'git commit -m "{commit_message}"',
            "git push origin $(git rev-parse --abbrev-ref HEAD)",
        ]
        for cmd in commands:
            try:
                proc = subprocess.run(
                    cmd, shell=True, capture_output=True, text=True,
                    cwd=self._repo_path, timeout=60,
                )
                results[cmd] = {
                    "returncode": proc.returncode,
                    "stdout": proc.stdout.strip(),
                    "stderr": proc.stderr.strip(),
                }
            except Exception as e:
                results[cmd] = {"returncode": -1, "error": str(e)}

        return create_signal(
            signal_type=SignalType.SYNC_PUSH,
            authority=AuthorityLevel.OPERATOR,
            jurisdiction="sync",
            payload={
                "commit_message": commit_message,
                "timestamp": timestamp,
                "results": results,
            },
            source=self._operator_id,
        )
