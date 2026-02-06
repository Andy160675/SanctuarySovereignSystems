# agi/core/roles/validator.py
from __future__ import annotations
from typing import Dict, Any, List
import re

HARD_REFUSALS = [
    r"\bmake\s+a\s+bomb\b",
    r"\bcredit\s+card\s+fraud\b",
    r"\bhack\s+.*server\b",
    r"\bkill\b",
    r"\bmanufacture\s+drugs\b",
]
PROFESSIONAL_CLAIMS = [r"\bi am a (doctor|lawyer|attorney|certified|surgeon)\b"]
UNCERTAINTY_WORDS = ["maybe", "possibly", "unclear", "unknown"]

REFUSAL_TEMPLATE = (
    "I must decline providing that assistance under the Sovereign policy. "
    "This request triggers safety or legality constraints."
)


def scan_patterns(text: str, patterns: List[str]) -> List[str]:
    hits = []
    for pat in patterns:
        if re.search(pat, text, flags=re.IGNORECASE):
            hits.append(pat)
    return hits


def run_validator(specialist_out: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    raw = specialist_out.get("answer", "")
    answer = raw if isinstance(raw, str) else str(raw)
    violations: List[Dict[str, str]] = []
    hard_hits = scan_patterns(answer, HARD_REFUSALS)
    if hard_hits:
        violations.append({"code": "HARD_REFUSAL", "patterns": ",".join(hard_hits)})
    prof_hits = scan_patterns(answer, PROFESSIONAL_CLAIMS)
    if prof_hits:
        violations.append({"code": "PROFESSIONAL_MISREPRESENTATION", "patterns": ",".join(prof_hits)})

    # Overconfidence: if answer lacks uncertainty words AND is short disclaimers free when question seems broad
    # Heuristic minimal for v0.1b
    if not any(w in answer.lower() for w in UNCERTAINTY_WORDS) and len(answer.split()) > 120:
        # If no qualifiers for a long answer mark potential overconfidence
        violations.append({"code": "POTENTIAL_OVERCERTAINTY", "patterns": "none"})

    policy_ok = len([v for v in violations if v["code"] == "HARD_REFUSAL"]) == 0
    safe_answer = answer
    if not policy_ok:
        safe_answer = REFUSAL_TEMPLATE

    return {
        "role": "validator",
        "policy_ok": policy_ok,
        "violations": violations,
        "original": answer,
        "answer": safe_answer,
    }
