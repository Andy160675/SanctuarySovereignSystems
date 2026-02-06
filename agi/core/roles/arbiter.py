# agi/core/roles/arbiter.py
from __future__ import annotations
from typing import Dict, Any, List

_REFUSAL_HEADER = (
    "I cannot fulfil this request as stated because it conflicts with safety and policy constraints. "
    "Triggered violations:"
)


def _summarise_violations(violations: List[Dict[str, str]]) -> str:
    if not violations:
        return "- [POLICY] A rule was triggered but no details recorded."
    lines = []
    for v in violations:
        code = v.get("code", "POLICY")
        msg = v.get("message", "Rule triggered.")
        lines.append(f"- [{code}] {msg}")
    return "\n".join(lines)


def _build_refusal(validator_output: Dict[str, Any]) -> str:
    violations = validator_output.get("violations") or []
    body = _summarise_violations(violations)
    tail = (
        "\nI can help by:\n"
        "- Rephrasing the request safely\n"
        "- Providing high-level, non-actionable context instead."
    )
    return f"{_REFUSAL_HEADER}\n{body}\n{tail}"


def run_arbiter(specialist_output: Dict[str, Any], validator_output: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    policy_ok = bool(validator_output.get("policy_ok", True))
    if policy_ok:
        final_answer = specialist_output.get("answer", "")
        status = "OK"
    else:
        final_answer = _build_refusal(validator_output)
        status = "REFUSED"
    return {
        "role": "arbiter",
        "status": status,
        "final_answer": final_answer,
        "validator_view": validator_output,
    }
