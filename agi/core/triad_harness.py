# agi/core/triad_harness.py
from __future__ import annotations
from pathlib import Path
from typing import Dict, Any, Literal, Optional
import time, json, hashlib, uuid

from .roles import validator, arbiter, specialist, interpreter
from .assistant_channel import get_assistant_system_prompt
from .receipt import SovereignReceipt, write_receipt_json, store_answer_and_receipt, init_db
try:
    from .drift_detector import detect_drift
except ImportError:
    def detect_drift(root: Path):
        return []

ResponseMode = Literal["raw", "explained", "discussion"]
ROOT_DIR = Path(__file__).resolve().parent
DEFAULT_POLICY_VERSION = "v0.1c"
DEFAULT_MODEL_ID = "stack-routed"

def _hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def run_triad(question: str, mode: ResponseMode = "raw", parent_receipt_id: Optional[str] = None, sensitivity: str = "normal") -> Dict[str, Any]:
    context: Dict[str, Any] = {
        "policy_version": DEFAULT_POLICY_VERSION,
        "model_id": DEFAULT_MODEL_ID,
        "question": question,
    }
    drifts = detect_drift(ROOT_DIR)
    drift_flag = len(drifts) > 0

    # Specialist invocation (now returns receipt metadata inside result['receipt'])
    spec_out = specialist.run_specialist(question, context)
    val_out = validator.run_validator(spec_out, context)
    arb_out = arbiter.run_arbiter(spec_out, val_out, context)

    raw_answer_obj = arb_out.get("final_answer", "")
    raw_answer = raw_answer_obj if isinstance(raw_answer_obj, str) else str(raw_answer_obj)

    explained_answer: Optional[str] = None
    interpreter_prompt_hash: Optional[str] = None
    if mode == "explained":
        interp_out = interpreter.run_interpreter(question, raw_answer, context)
        exp_obj = interp_out.get("explained_answer", raw_answer)
        explained_answer = exp_obj if isinstance(exp_obj, str) else str(exp_obj)
        interpreter_prompt_hash = _hash_text(interp_out.get("prompt", ""))
    elif mode == "discussion":
        explained_answer = f"[DISCUSSION]\n{raw_answer}"

    assistant_system_prompt = get_assistant_system_prompt()
    assistant_system_prompt_hash = _hash_text(assistant_system_prompt)

    answer_id = str(uuid.uuid4())
    receipt_id = str(uuid.uuid4())
    prompt_hash = _hash_text(question)
    answer_hash = _hash_text(raw_answer)
    ts = int(time.time())
    agent_path = ["specialist", "validator", "arbiter"] + (["interpreter"] if mode == "explained" else [])

    receipt = SovereignReceipt(
        receipt_id=receipt_id,
        answer_id=answer_id,
        model_id=context["model_id"],
        policy_version=context["policy_version"],
        mode=mode if mode != "explained" else "explained",
        agent_path=agent_path,
        prompt_hash=prompt_hash,
        answer_hash=answer_hash,
        interpreter_prompt_hash=interpreter_prompt_hash,
        assistant_system_prompt_hash=assistant_system_prompt_hash,
        parent_receipt_id=parent_receipt_id,
        drift_detected=drift_flag,
        drift_details=drifts,
        timestamp=ts,
    )

    receipt_path = write_receipt_json(receipt)

    visible_answer = explained_answer if (mode in ("explained", "discussion") and explained_answer) else raw_answer

    # Enrich receipt JSON with validator + arbiter + model forensic metadata
    enriched = json.loads(Path(receipt_path).read_text(encoding="utf-8"))
    enriched["validator"] = {"policy_ok": val_out.get("policy_ok", True), "violations": val_out.get("violations", [])}
    enriched["arbiter_status"] = arb_out.get("status", "OK")
    enriched["calls"] = {"specialist": spec_out.get("meta", {}), "specialist_receipt": spec_out.get("receipt")}
    Path(receipt_path).write_text(json.dumps(enriched, indent=2), encoding="utf-8")

    # Persist answer with full audit receipt
    store_answer_and_receipt(
        receipt,
        question,
        raw_answer,
        explained_answer if mode == "explained" else None,
        audit_receipt=enriched,
    )

    return {
        "answer": visible_answer,
        "mode": mode,
        "answer_id": answer_id,
        "receipt_id": receipt_id,
        "violations": val_out.get("violations", []),
        "policy_ok": val_out.get("policy_ok", True),
        "receipt_path": str(receipt_path),
        "receipt": enriched,
    }

if __name__ == "__main__":
    init_db()
    print(json.dumps(run_triad("Explain lawful property acquisition strategies", mode="explained"), indent=2))
