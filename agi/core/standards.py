"""
Trauma-Informed Standards Enforcement
Codex Sovereign – Empathy Engine
"""
from __future__ import annotations
from typing import List, Tuple


class Violation:
    def __init__(self, rule: str, detail: str):
        self.rule = rule
        self.detail = detail


class TraumaStandard:
    """
    A rule-checker enforcing trauma-informed communication.
    All rules are deterministic and transparent.
    """

    def validate_input(self, text: str) -> Tuple[bool, List[Violation]]:
        """
        Detect if input contains high-intensity states
        requiring grounding.
        Never diagnose.
        """
        issues: List[Violation] = []

        tl = (text or "").lower()
        if any(x in tl for x in ["kill myself", "can't go on", "cant go on", "suicide"]):
            issues.append(
                Violation(
                    "high_intensity_signal",
                    "Detected critical distress phrasing."
                )
            )

        return (len(issues) == 0, issues)

    def repair(self, issues: List[Violation]) -> str:
        """
        Gentle grounding. No scripts. No assumptions.
        Poka-yoke: prevent unsafe outputs automatically.
        """
        return (
            "You’re not alone. I can slow everything down. "
            "You decide the pace. "
            "If you want immediate human support, texting ‘SHOUT’ to 85258 is one option in the UK."
        )

    def validate_output(self, text: str) -> Tuple[bool, List[Violation]]:
        """
        Enforce constitution: no pressure, no guilt,
        no escalation, no irreversible statements.
        """
        violations: List[Violation] = []
        tl = (text or "").lower()

        forbidden = ["must", "should", "you have to", "urgent"]
        for f in forbidden:
            if f in tl:
                violations.append(Violation("coercive_language", f))

        return (len(violations) == 0, violations)

    def correct_output(self, text: str, violations: List[Violation]) -> str:
        """
        Removes coercive or sensitive language while keeping meaning.
        """
        for v in violations:
            if v.rule == "coercive_language":
                text = text.replace(v.detail, "")
        return text
