from __future__ import annotations
"""Agent identity and RBAC model.
Phase 5 governance gap #1 implementation.

Minimal, non-invasive: other modules can import `resolve_identity` and `is_tool_allowed`.
"""
from dataclasses import dataclass
from typing import List, Dict
import uuid, yaml, os

IDENTITIES_FILE = os.path.join(os.getcwd(), "constitution", "agent_identities.yml")

@dataclass
class AgentIdentity:
    agent_id: str
    role: str
    allowed_tools: List[str]
    budget_usd: float

_id_cache: Dict[str, AgentIdentity] = {}

DEFAULT_IDENTITY = AgentIdentity(agent_id="anonymous", role="observer", allowed_tools=[], budget_usd=0.0)

ROLE_DEFAULTS = {
    "observer": AgentIdentity(agent_id="anonymous", role="observer", allowed_tools=[], budget_usd=0.0),
    "scout": AgentIdentity(agent_id="temp", role="scout", allowed_tools=["search", "classify"], budget_usd=2.0),
    "executor": AgentIdentity(agent_id="temp", role="executor", allowed_tools=["search", "classify", "run"], budget_usd=10.0),
    "guardian": AgentIdentity(agent_id="temp", role="guardian", allowed_tools=["search", "classify", "verify", "halt"], budget_usd=5.0),
}

def load_identities() -> Dict[str, AgentIdentity]:
    if not os.path.exists(IDENTITIES_FILE):
        return {}
    with open(IDENTITIES_FILE, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}
    out = {}
    for name, spec in raw.items():
        out[name] = AgentIdentity(
            agent_id=spec.get("agent_id") or str(uuid.uuid4()),
            role=spec.get("role", name),
            allowed_tools=spec.get("allowed_tools", []),
            budget_usd=float(spec.get("budget_usd", 0.0))
        )
    return out

def resolve_identity(name: str) -> AgentIdentity:
    if not _id_cache:
        _id_cache.update(load_identities())
    ident = _id_cache.get(name)
    if ident:
        return ident
    # fallback to role default or anonymous
    return ROLE_DEFAULTS.get(name, DEFAULT_IDENTITY)

def is_tool_allowed(identity: AgentIdentity, tool_name: str) -> bool:
    return tool_name in identity.allowed_tools

__all__ = ["AgentIdentity", "resolve_identity", "is_tool_allowed"]
