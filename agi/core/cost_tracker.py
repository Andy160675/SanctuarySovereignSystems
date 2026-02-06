from __future__ import annotations
"""Cost tracker for Phase 5 governance gap #2.
Tracks cumulative USD cost per agent, enforces max budget.
"""
from dataclasses import dataclass
from typing import Dict
import time

@dataclass
class CostRecord:
    total: float = 0.0
    last_updated: float = 0.0

_costs: Dict[str, CostRecord] = {}

DEFAULT_MAX_COST = 10.0  # USD per agent per session

def add_cost(agent_id: str, amount: float) -> float:
    rec = _costs.get(agent_id) or CostRecord()
    rec.total += amount
    rec.last_updated = time.time()
    _costs[agent_id] = rec
    return rec.total

def get_total(agent_id: str) -> float:
    rec = _costs.get(agent_id)
    return rec.total if rec else 0.0

def is_within_budget(agent_id: str, estimate: float, max_cost: float = DEFAULT_MAX_COST) -> bool:
    current = get_total(agent_id)
    return (current + estimate) <= max_cost

def reset(agent_id: str):
    if agent_id in _costs:
        del _costs[agent_id]

__all__ = ["add_cost", "get_total", "is_within_budget", "reset", "DEFAULT_MAX_COST"]
