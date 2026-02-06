"""
Empathy Engine v0.1
Codex Sovereign – Trauma-Informed Interaction Layer
"""
from __future__ import annotations

from .standards import TraumaStandard, Violation


class EmpathyEngine:
    """
    The Empathy Engine is a rule-based state machine that enforces
    trauma-informed, ND-friendly communication constraints.
    It NEVER diagnoses, never manipulates, and never escalates without cause.
    """

    def __init__(self):
        self.standard = TraumaStandard()
        self.last_user_message = None

    def process(self, user_text: str) -> str:
        """
        Main deterministic logic.
        Every output is checked against the trauma standard before returning.
        """
        self.last_user_message = user_text

        # 1. Validate input is safe to respond to
        safe_in, issues = self.standard.validate_input(user_text)
        if not safe_in:
            return self.standard.repair(issues)

        # 2. Generate base reply (placeholder)
        reply = self._base_reply(user_text)

        # 3. Validate output
        safe_out, violations = self.standard.validate_output(reply)
        if not safe_out:
            reply = self.standard.correct_output(reply, violations)

        return reply

    def _base_reply(self, text: str) -> str:
        """
        Minimal non-triggering template.
        No assumptions, no analysis.
        """
        return (
            "I hear what you're expressing. "
            "If you'd like to focus on something specific, we can take it step by step. "
            "There’s no pressure."
        )
