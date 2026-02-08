"""
G.I.y — Git Intelligence for Authority-Grade Truth Alignment
==============================================================
Condensed from bLADE2-OFFFLINE into constitutional production form.
All operations are typed signals routed through the constitutional kernel.

Original concept: BLADE2/VENICE GIT INTELLIGENCE SUITE
Production form: Sovereign Audit Operations under Season 2 Codex
"""

from __future__ import annotations
import subprocess
import json
from datetime import datetime, timezone
from typing import Optional
from engine.signals.typed_signal import (
    TypedSignal, SignalType, AuthorityLevel, create_signal,
)


class GitIntelligence:
    """
    Constitutional Git audit operations.
    Every operation produces a TypedSignal for kernel routing.
    """

    def __init__(self, repo_path: str, operator_id: str):
        self._repo_path = repo_path
        self._operator_id = operator_id

    def state_check(self) -> Optional[TypedSignal]:
        """
        Instruction 1: State Check
        Branch, latest commit, remotes — as a typed signal.
        """
        result = self._run_commands([
            "git rev-parse --abbrev-ref HEAD",
            'git log -1 --pretty=format:"%h - %an, %ar : %s"',
            "git remote -v",
        ])
        return create_signal(
            signal_type=SignalType.STATE_CHECK,
            authority=AuthorityLevel.OPERATOR,
            jurisdiction="audit",
            payload={"state_check": result},
            source=self._operator_id,
        )

    def usage_verification(self) -> Optional[TypedSignal]:
        """
        Instruction 2: Usage Verification
        Recent actions and file changes.
        """
        result = self._run_commands([
            "git reflog --date=iso | head -5",
            "git diff --stat HEAD",
        ])
        return create_signal(
            signal_type=SignalType.USAGE_VERIFICATION,
            authority=AuthorityLevel.OPERATOR,
            jurisdiction="audit",
            payload={"usage_verification": result},
            source=self._operator_id,
        )

    def integrity_audit(self) -> Optional[TypedSignal]:
        """
        Instruction 3: Integrity Audit
        Uncommitted changes, corruption, detached HEAD.
        """
        result = self._run_commands([
            "git status",
            "git fsck",
        ])
        return create_signal(
            signal_type=SignalType.INTEGRITY_AUDIT,
            authority=AuthorityLevel.OPERATOR,
            jurisdiction="integrity",
            payload={"integrity_audit": result},
            source=self._operator_id,
        )

    def trust_anchor_verification(self) -> Optional[TypedSignal]:
        """
        Instruction 4: Trust Anchor Verification
        Commits from non-verified agents in last 72 hours.
        """
        result = self._run_commands([
            'git log --since="72 hours ago" --pretty=format:"%an <%ae>"',
        ])
        return create_signal(
            signal_type=SignalType.TRUST_ANCHOR,
            authority=AuthorityLevel.INNOVATOR,
            jurisdiction="integrity",
            payload={"trust_anchor": result},
            source=self._operator_id,
        )

    def loop_confirmation(self) -> Optional[TypedSignal]:
        """
        Instruction 5: Loop Confirmation
        Remote reachability and sync status.
        """
        result = self._run_commands([
            "git remote show origin",
            "git fetch --dry-run",
            "git status",
        ])
        return create_signal(
            signal_type=SignalType.LOOP_CONFIRMATION,
            authority=AuthorityLevel.OPERATOR,
            jurisdiction="sync",
            payload={"loop_confirmation": result},
            source=self._operator_id,
        )

    def environment_fit(self) -> Optional[TypedSignal]:
        """
        Instruction 6: Environment Fit
        Correct directory, correct git context.
        """
        result = self._run_commands([
            "pwd",
            "ls -la",
            "cat .git/config",
        ])
        return create_signal(
            signal_type=SignalType.ENVIRONMENT_FIT,
            authority=AuthorityLevel.OPERATOR,
            jurisdiction="audit",
            payload={"environment_fit": result},
            source=self._operator_id,
        )

    def timeline_trace(self) -> Optional[TypedSignal]:
        """
        Instruction 7: Timeline Trace
        Commit timeline for anomaly detection.
        """
        result = self._run_commands([
            'git log --since="48 hours ago" --oneline --graph --decorate',
        ])
        return create_signal(
            signal_type=SignalType.TIMELINE_TRACE,
            authority=AuthorityLevel.OPERATOR,
            jurisdiction="audit",
            payload={"timeline_trace": result},
            source=self._operator_id,
        )

    def truth_reconcile(self) -> Optional[TypedSignal]:
        """
        Instruction 8: Truth Reconciliation
        Elevated operation — requires Innovator authority.
        """
        timestamp = datetime.now(timezone.utc).isoformat()
        return create_signal(
            signal_type=SignalType.TRUTH_RECONCILE,
            authority=AuthorityLevel.INNOVATOR,
            jurisdiction="integrity",
            payload={
                "truth_signature": f"SOVEREIGN_TRUTH:{timestamp}",
                "reconciliation_type": "full",
            },
            source=self._operator_id,
        )

    def _run_commands(self, commands: list[str]) -> dict[str, str]:
        """Execute git commands and capture output. Safe failure on error."""
        results = {}
        for cmd in commands:
            try:
                proc = subprocess.run(
                    cmd, shell=True, capture_output=True, text=True,
                    cwd=self._repo_path, timeout=30,
                )
                results[cmd] = proc.stdout.strip() if proc.returncode == 0 else f"ERROR: {proc.stderr.strip()}"
            except Exception as e:
                results[cmd] = f"EXCEPTION: {str(e)}"
        return results
