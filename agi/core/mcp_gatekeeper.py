"""
MCP Agent Gatekeeper
Fail-Closed Mode
"""
from __future__ import annotations

from pathlib import Path
from .diff_validator import ASTDiffValidator, DiffViolation
from .policy_signature import PolicySignature


class MCPGatekeeper:
    def __init__(self):
        self.validator = ASTDiffValidator()
        self.signature = PolicySignature()

    def check_policy(self) -> None:
        """Reject all operations if manifest signature doesn't match."""
        self.signature.validate_signature()

    def validate_proposed_change(self, old_path: str, new_content: str):
        """
        Compare old vs new content and block unsafe modifications.
        Returns tuple(bool_ok, message)
        """
        self.check_policy()
        path = Path(old_path)
        old_content = path.read_text(encoding="utf-8")
        try:
            self.validator.validate_string(old=old_content, new=new_content, file_path=str(path))
        except DiffViolation as e:
            return False, str(e)
        return True, "Approved"
