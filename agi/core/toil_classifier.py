from __future__ import annotations
"""Toil classifier (Phase 5 governance gap #4).
Rejects unverifiable / unbounded tasks early.
"""
from dataclasses import dataclass

@dataclass
class ToilAssessment:
    verifiable: bool
    bounded: bool
    permitted_domain: bool

    @property
    def is_accept(self) -> bool:
        return self.verifiable and self.bounded and self.permitted_domain

REJECT_CODES = {
    "NOT_VERIFIABLE": "Task rejected: output cannot be objectively verified.",
    "UNBOUNDED": "Task rejected: scope not bounded (missing clear end condition).",
    "DOMAIN_DENIED": "Task rejected: domain not permitted under current policy.",
}

PERMITTED_DOMAINS = {"legal", "medical", "ops", "engineering", "research"}

def assess(goal: str, domain: str) -> ToilAssessment:
    # Heuristics (placeholder): refine later
    verifiable = any(k in goal.lower() for k in ["report", "summary", "list", "extract", "classify", "diff", "matrix"])
    bounded = not any(k in goal.lower() for k in ["infinite", "endless", "continuous", "monitor forever"])
    permitted_domain = domain.lower() in PERMITTED_DOMAINS
    return ToilAssessment(verifiable, bounded, permitted_domain)

def rejection_reason(ass: ToilAssessment, domain: str, goal: str) -> str | None:
    if not ass.verifiable:
        return REJECT_CODES["NOT_VERIFIABLE"]
    if not ass.bounded:
        return REJECT_CODES["UNBOUNDED"]
    if not ass.permitted_domain:
        return REJECT_CODES["DOMAIN_DENIED"]
    return None

__all__ = ["assess", "rejection_reason", "ToilAssessment"]
