# agi/core/model_runner.py
"""Unified model runner with receipt enrichment (v0.1c).
Provides forensic metadata (latency, token estimates, cost) for every model invocation.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Literal, Tuple, Optional
import requests, yaml, time, os
from dataclasses import dataclass, asdict

# Optional Anthrop ic import (remote provider)
try:
    import anthropic  # type: ignore
except Exception:  # pragma: no cover
    anthropic = None  # fallback

ROOT_DIR = Path(__file__).resolve().parent
STACK_PATH = ROOT_DIR / "model_stack.yaml"
_StackCache: Dict[str, Any] | None = None

Sensitivity = Literal["normal", "high"]
Provider = Literal["ollama", "cloud-llm", "anthropic"]

@dataclass
class ModelReceipt:
    timestamp: float
    model_id: str
    provider: str
    input_tokens: int
    output_tokens: int
    latency_ms: int
    cost_usd: float
    status: str  # success|error
    raw_output: str
    error_msg: Optional[str] = None

PRICING_PER_MILLION = {
    # Example pricing (update as needed)
    "claude-3-5-sonnet-20241022": {"input": 3.00, "output": 15.00},
    "claude-3-haiku-20240307": {"input": 0.25, "output": 1.25},
    # Local models cost considered 0 for accounting (adjust if internal amortisation used)
}

class ModelRunnerError(Exception):
    pass

def load_model_stack() -> Dict[str, Any]:
    global _StackCache
    if _StackCache is None:
        if not STACK_PATH.exists():
            raise ModelRunnerError(f"model_stack.yaml not found at {STACK_PATH}")
        with STACK_PATH.open("r", encoding="utf-8") as f:
            _StackCache = yaml.safe_load(f) or {}
    return _StackCache

def resolve_model_key(task_type: str, sensitivity: Sensitivity) -> Tuple[str, Dict[str, Any]]:
    stack = load_model_stack()
    routing = stack.get("routing_rules", {})
    default_key = routing.get("default", "local_small")
    key = routing.get("by_task_type", {}).get(task_type, default_key)
    if sensitivity == "high":
        ov = routing.get("overrides", {}).get("high_sensitivity", {})
        if not ov.get("allow_remote", True) and key == "remote_tier":
            key = ov.get("fallback", default_key)
    models = stack.get("models", {})
    cfg = models.get(key)
    if not cfg:
        raise ModelRunnerError(f"Model key '{key}' not defined for task '{task_type}'")
    return key, cfg

def _estimate_tokens(text: str) -> int:
    # Rough heuristic: 1 token ? 4 chars or split by spaces; choose smaller for safety
    if not text:
        return 0
    return min(len(text) // 4, len(text.split()))

def _calc_cost(model_id: str, input_toks: int, output_toks: int) -> float:
    pricing = PRICING_PER_MILLION.get(model_id)
    if not pricing:
        return 0.0
    cost = (input_toks / 1_000_000 * pricing["input"]) + (output_toks / 1_000_000 * pricing["output"])
    return round(cost, 6)

def call_ollama(model_id: str, prompt: str, **kwargs: Any) -> str:
    url = "http://localhost:11434/api/generate"
    payload = {"model": model_id, "prompt": prompt, "stream": False}
    payload.update(kwargs)
    resp = requests.post(url, json=payload, timeout=120)
    if resp.status_code != 200:
        raise ModelRunnerError(f"Ollama HTTP {resp.status_code}: {resp.text}")
    data = resp.json()
    return (data.get("response") or data.get("output") or "").strip()

def call_anthropic(model_id: str, prompt: str, system: str, max_tokens: int = 1024, temperature: float = 0.0) -> Dict[str, Any]:
    if anthropic is None:
        raise ModelRunnerError("Anthropic library not available")
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ModelRunnerError("ANTHROPIC_API_KEY missing from environment")
    client = anthropic.Anthropic(api_key=api_key)
    resp = client.messages.create(
        model=model_id,
        max_tokens=max_tokens,
        temperature=temperature,
        system=system,
        messages=[{"role": "user", "content": prompt}],
    )
    return {
        "text": resp.content[0].text if resp.content else "",
        "input_tokens": getattr(resp.usage, "input_tokens", 0),
        "output_tokens": getattr(resp.usage, "output_tokens", 0),
    }

def generate(
    task_type: str,
    prompt: str,
    sensitivity: Sensitivity = "normal",
    system_prompt: Optional[str] = None,
    max_tokens: int = 1024,
    temperature: float = 0.0,
) -> ModelReceipt:
    start = time.time()
    key, cfg = resolve_model_key(task_type, sensitivity)
    provider: Provider = cfg.get("provider", "ollama")  # type: ignore
    model_id = cfg.get("id")
    try:
        if provider == "ollama":
            output = call_ollama(model_id=model_id, prompt=prompt)
            in_toks = _estimate_tokens(prompt)
            out_toks = _estimate_tokens(output)
        elif provider == "cloud-llm":
            # Placeholder remote stub
            output = f"[REMOTE_STUB:{model_id}] {prompt[:180]}"
            in_toks = _estimate_tokens(prompt)
            out_toks = _estimate_tokens(output)
        elif provider == "anthropic":
            system = system_prompt or "You are a helpful assistant."  # required for anthropic
            data = call_anthropic(model_id=model_id, prompt=prompt, system=system, max_tokens=max_tokens, temperature=temperature)
            output = data["text"]
            in_toks = data["input_tokens"]
            out_toks = data["output_tokens"]
        else:
            raise ModelRunnerError(f"Unsupported provider '{provider}'")
        latency_ms = int((time.time() - start) * 1000)
        cost = _calc_cost(model_id, in_toks, out_toks)
        return ModelReceipt(
            timestamp=time.time(),
            model_id=model_id,
            provider=provider,
            input_tokens=in_toks,
            output_tokens=out_toks,
            latency_ms=latency_ms,
            cost_usd=cost,
            status="success",
            raw_output=output,
        )
    except Exception as e:  # Capture failure receipt
        latency_ms = int((time.time() - start) * 1000)
        return ModelReceipt(
            timestamp=time.time(),
            model_id=model_id,
            provider=provider,
            input_tokens=0,
            output_tokens=0,
            latency_ms=latency_ms,
            cost_usd=0.0,
            status="error",
            raw_output="",
            error_msg=str(e),
        )

def generate_dict(*args: Any, **kwargs: Any) -> Dict[str, Any]:
    """Helper returning receipt as dict plus convenience 'text'."""
    receipt = generate(*args, **kwargs)
    data = asdict(receipt)
    data["text"] = receipt.raw_output
    return data

# Backwards compatibility function used by specialist
def run_model_for_task(task_type: str, prompt: str, sensitivity: Sensitivity = "normal") -> Dict[str, Any]:
    rec = generate(task_type=task_type, prompt=prompt, sensitivity=sensitivity)
    return {"model_key": task_type, "model_id": rec.model_id, "provider": rec.provider, "text": rec.raw_output, "receipt": asdict(rec), "sensitivity": sensitivity}

if __name__ == "__main__":  # quick manual test
    r = generate("governance", "List three principles of sovereign property analysis.")
    print(asdict(r))
