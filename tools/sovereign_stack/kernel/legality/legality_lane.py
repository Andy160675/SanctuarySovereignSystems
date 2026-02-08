"""
Article III: The Legality Lane
===============================
Before any inference or execution, all signals pass through
the Legality Lane. This guard stops domain violations, undefined
operations, and constitutional singularities.

This makes the downstream representation of an illegal state impossible.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Callable, List
from tools.sovereign_stack.engine.signals.typed_signal import (
    TypedSignal, SignalType, AuthorityLevel, SIGNAL_AUTHORITY_MAP,
)


@dataclass(frozen=True)
class LegalityResult:
    """Immutable result of a legality check."""
    passed: bool
    reason: str
    signal_id: str
    checks_run: int
    checks_passed: int


class LegalityLane:
    """
    Constitutional guard. Every signal must pass ALL checks
    before it can be routed. A single failure = process_block.
    """

    def __init__(self):
        self._checks: List[Callable[[TypedSignal], tuple[bool, str]]] = [
            self._check_type_exists,
            self._check_authority_sufficient,
            self._check_jurisdiction_defined,
            self._check_payload_present,
            self._check_source_identified,
            self._check_evidence_hash_valid,
        ]

    def check(self, signal: TypedSignal) -> LegalityResult:
        """
        Run all constitutional checks. ALL must pass.
        Axiom III: Illegality is Unrepresentable.
        """
        checks_passed = 0
        for check_fn in self._checks:
            passed, reason = check_fn(signal)
            if not passed:
                return LegalityResult(
                    passed=False,
                    reason=reason,
                    signal_id=signal.signal_id,
                    checks_run=len(self._checks),
                    checks_passed=checks_passed,
                )
            checks_passed += 1

        return LegalityResult(
            passed=True,
            reason="all_checks_passed",
            signal_id=signal.signal_id,
            checks_run=len(self._checks),
            checks_passed=checks_passed,
        )

    @staticmethod
    def _check_type_exists(signal: TypedSignal) -> tuple[bool, str]:
        """Signal must have a recognized type."""
        if signal.signal_type not in SignalType:
            return False, "unrecognized_signal_type"
        return True, "type_valid"

    @staticmethod
    def _check_authority_sufficient(signal: TypedSignal) -> tuple[bool, str]:
        """Signal authority must meet minimum for its type."""
        required = SIGNAL_AUTHORITY_MAP.get(signal.signal_type)
        if required is None:
            return False, "no_authority_mapping"
        rank = {
            AuthorityLevel.OPERATOR: 0,
            AuthorityLevel.INNOVATOR: 1,
            AuthorityLevel.STEWARD: 2,
        }
        if rank[signal.authority] < rank[required]:
            return False, f"insufficient_authority: need {required.value}, have {signal.authority.value}"
        return True, "authority_sufficient"

    @staticmethod
    def _check_jurisdiction_defined(signal: TypedSignal) -> tuple[bool, str]:
        """Signal must declare a jurisdiction context (Article VIII)."""
        if not signal.jurisdiction or signal.jurisdiction.strip() == "":
            return False, "undefined_jurisdiction"
        return True, "jurisdiction_defined"

    @staticmethod
    def _check_payload_present(signal: TypedSignal) -> tuple[bool, str]:
        """Signal must carry a payload. Empty signals are noise."""
        if signal.payload is None:
            return False, "null_payload"
        return True, "payload_present"

    @staticmethod
    def _check_source_identified(signal: TypedSignal) -> tuple[bool, str]:
        """Signal must identify its source. Anonymous signals are rejected."""
        if not signal.source or signal.source == "unknown":
            return False, "unidentified_source"
        return True, "source_identified"

    @staticmethod
    def _check_evidence_hash_valid(signal: TypedSignal) -> tuple[bool, str]:
        """Signal must have a computed evidence hash (Axiom I)."""
        if not signal.evidence_hash or len(signal.evidence_hash) != 64:
            return False, "invalid_evidence_hash"
        return True, "evidence_hash_valid"

