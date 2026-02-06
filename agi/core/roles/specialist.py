# agi/core/roles/specialist.py
from __future__ import annotations
from typing import Dict, Any
from ..model_runner import run_model_for_task

def build_specialist_prompt(question: str, context: Dict[str, Any]) -> str:
    return (
        "You are the Sovereign specialist agent.\n"
        "- Answer truthfully and precisely.\n"
        "- Prefer evidence and clarity over style.\n"
        "- Do not fabricate sources or facts.\n\n"
        f"Question:\n{question}\n"
    )

def run_specialist(question: str, context: Dict[str, Any]) -> Dict[str, Any]:
    prompt = build_specialist_prompt(question, context)
    result = run_model_for_task(task_type="governance", prompt=prompt)
    answer_text = result.get("text", "")
    return {
        "role": "specialist",
        "answer": answer_text,
        "meta": {"prompt": prompt, "model_key": result.get("model_key"), "provider": result.get("provider")},
    }
