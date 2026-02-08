from typing import List

# Deterministic guardrails (fail-closed signals)
BLOCK_PATTERNS = [
    "modify kernel",
    "change constitution",
    "bypass invariants",
    "disable audit",
    "disable halt doctrine",
    "force push to main",
    "skip tests",
]

def scan_decision_for_kernel_risk(decision: str) -> List[str]:
    text = (decision or "").lower()
    hits = [p for p in BLOCK_PATTERNS if p in text]
    return [f"Kernel guard trigger: '{h}'" for h in hits]
