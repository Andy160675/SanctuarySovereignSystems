#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Boardroom 13 Role Definitions

Each role represents a distinct perspective in the constitutional governance model.
These are the 13 agents that evaluate proposals and provide auditable opinions.
"""

from dataclasses import dataclass
from typing import List


@dataclass
class Role:
    """A single Boardroom role with its key, title, and brief description."""
    key: str
    title: str
    description: str
    focus_areas: List[str]


# The 13 Constitutional Roles
ROLES = [
    Role(
        key="chair",
        title="Chair",
        description="Moderates deliberation, ensures procedural balance, and seeks consensus.",
        focus_areas=["procedure", "consensus", "time-boxing", "facilitation"]
    ),
    Role(
        key="recorder",
        title="Recorder",
        description="Maintains the canonical audit trail and creates snapshots of all decisions.",
        focus_areas=["audit", "evidence", "provenance", "immutability"]
    ),
    Role(
        key="ethicist",
        title="Ethicist",
        description="Evaluates human impact, flags harm potential, and ensures ethical alignment.",
        focus_areas=["harm", "bias", "fairness", "stakeholder-impact"]
    ),
    Role(
        key="engineer",
        title="Engineer",
        description="Assesses technical feasibility, architectural constraints, and implementation risks.",
        focus_areas=["feasibility", "architecture", "testing", "scalability"]
    ),
    Role(
        key="empath",
        title="Empath",
        description="Focuses on human context, communication tone, and stakeholder experience.",
        focus_areas=["communication", "tone", "user-experience", "accessibility"]
    ),
    Role(
        key="archivist",
        title="Archivist",
        description="Ensures proper storage, provenance metadata, and long-term retention.",
        focus_areas=["storage", "metadata", "retention", "retrieval"]
    ),
    Role(
        key="strategist",
        title="Strategist",
        description="Aligns decisions with organizational objectives and long-term strategy.",
        focus_areas=["alignment", "milestones", "roadmap", "priorities"]
    ),
    Role(
        key="guardian",
        title="Guardian",
        description="Enforces security, access control, and integrity verification.",
        focus_areas=["security", "access-control", "encryption", "integrity"]
    ),
    Role(
        key="analyst",
        title="Analyst",
        description="Provides data-driven analysis, metrics, and quantitative evaluation.",
        focus_areas=["data", "metrics", "KPIs", "validation"]
    ),
    Role(
        key="linguist",
        title="Linguist",
        description="Ensures clarity, removes ambiguity, and standardizes terminology.",
        focus_areas=["clarity", "terminology", "disambiguation", "documentation"]
    ),
    Role(
        key="jurist",
        title="Jurist",
        description="Evaluates legal compliance, regulatory requirements, and contractual obligations.",
        focus_areas=["compliance", "regulation", "contracts", "liability"]
    ),
    Role(
        key="creator",
        title="Creator",
        description="Proposes alternatives, encourages experimentation, and preserves optionality.",
        focus_areas=["innovation", "alternatives", "prototyping", "experimentation"]
    ),
    Role(
        key="observer",
        title="Observer",
        description="Maintains meta-awareness, flags cognitive biases, and monitors framing.",
        focus_areas=["meta-cognition", "bias-detection", "framing", "reflection"]
    ),
]


def get_role(key: str) -> Role:
    """Retrieve a role by its key."""
    for role in ROLES:
        if role.key == key:
            return role
    raise ValueError(f"Unknown role key: {key}")


def list_role_keys() -> List[str]:
    """Return all role keys."""
    return [r.key for r in ROLES]
