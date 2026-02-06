from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any

# All metrics are bounded [0,1]

def _clamp(x: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, float(x)))


def compute_A1(features: Dict[str, Any]) -> float:
    # grounded_options: count normalized to 5
    # counterfactual_quality: [0,1]
    # reality_contact: boolean -> 1 if True else 0
    go = _clamp((features.get("grounded_options", 0) or 0) / 5.0)
    cq = _clamp(features.get("counterfactual_quality", 0) or 0)
    rc = 1.0 if bool(features.get("reality_contact", False)) else 0.0
    # simple average; tune later
    return _clamp((go + cq + rc) / 3.0)


def compute_A2(features: Dict[str, Any]) -> float:
    pd = _clamp(features.get("plan_detail", 0) or 0)
    ra = _clamp(features.get("resources_available", 0) or 0)
    cf = _clamp(features.get("capability_fit", 0) or 0)
    tr = _clamp(features.get("timeline_realism", 0) or 0)
    return _clamp((pd + ra + cf + tr) / 4.0)


def compute_A3(features: Dict[str, Any]) -> float:
    il = _clamp(features.get("internal_locus", 0) or 0)
    va = _clamp(features.get("values_alignment", 0) or 0)
    nc = _clamp(features.get("narrative_coherence", 0) or 0)
    ns = _clamp(features.get("non_substitution", 0) or 0)
    return _clamp((il + va + nc + ns) / 4.0)


def compute_A4(features: Dict[str, Any]) -> float:
    wt = _clamp(features.get("window_of_tolerance", 0) or 0)
    ca = _clamp(features.get("coping_access", 0) or 0)
    mf = _clamp(features.get("meaning_frame", 0) or 0)
    vr_raw = _clamp(features.get("volatility_risk", 0) or 0)
    vr = 1.0 - vr_raw  # inverse
    return _clamp((wt + ca + mf + vr) / 4.0)


@dataclass
class AgencyVector:
    A1: float
    A2: float
    A3: float
    A4: float

    @property
    def aggregate(self) -> float:
        return 0.30 * self.A1 + 0.30 * self.A2 + 0.20 * self.A3 + 0.20 * self.A4


def compute_agency_vector(a1: Dict[str, Any], a2: Dict[str, Any], a3: Dict[str, Any], a4: Dict[str, Any]) -> AgencyVector:
    return AgencyVector(
        A1=compute_A1(a1),
        A2=compute_A2(a2),
        A3=compute_A3(a3),
        A4=compute_A4(a4),
    )
