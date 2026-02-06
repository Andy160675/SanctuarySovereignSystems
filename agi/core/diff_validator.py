"""
AST Semantic Diff Validator
Fail-Closed Gatekeeper (Mode 1)
Codex Sovereign – Empathy Engine
"""
from __future__ import annotations

import ast
from pathlib import Path
from typing import List

FORBIDDEN = [
    "must",
    "should",
    "you have to",
    "urgent",
    "time-sensitive",
    "pressure",
]

class DiffViolation(Exception):
    pass


class ASTDiffValidator:
    """
    This validator compares the previous and proposed versions of a file,
    and blocks changes that violate the safety rules.
    """

    def __init__(self, manifest_path: str = "constitution/policy_manifest.yml"):
        self.manifest_path = Path(manifest_path)

    def load_file(self, path: Path) -> str:
        return path.read_text(encoding="utf-8")

    def validate_string(self, old: str, new: str, file_path: str) -> None:
        """
        Validate proposed code changes. Blocks dangerous diff patterns.
        """
        violations = self._scan_forbidden(new)
        if violations:
            raise DiffViolation(
                f"Rejected update to {file_path}. Forbidden patterns found: {violations}"
            )

        try:
            old_ast = ast.parse(old)
            new_ast = ast.parse(new)
        except SyntaxError:
            raise DiffViolation(f"Syntax error in proposed update for {file_path}")

        self._compare_asts(old_ast, new_ast, file_path)

    def _scan_forbidden(self, content: str) -> List[str]:
        return [f for f in FORBIDDEN if f in (content or "").lower()]

    def _compare_asts(self, old_ast: ast.AST, new_ast: ast.AST, file_path: str) -> None:
        """
        Compare nodes for red-flag behaviour: coercion, inference,
        forced introspection, manipulation, escalations.
        """
        old_nodes = {type(n).__name__ for n in ast.walk(old_ast)}
        new_nodes = {type(n).__name__ for n in ast.walk(new_ast)}

        newly_added = new_nodes - old_nodes

        forbidden_constructs = {
            "Try",          # manipulation attempts hidden in try/except
            "Assert",       # forced state assertions
            "Raise",        # raising exceptions at user-level flow
            "YieldFrom",    # generator-based manipulation patterns
            "AsyncFunctionDef",  # async escalation mechanisms
        }

        bad = newly_added & forbidden_constructs
        if bad:
            raise DiffViolation(
                f"Rejected update to {file_path}. Unsafe AST constructs introduced: {bad}"
            )
