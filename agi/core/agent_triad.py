import os
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

try:
    import yaml  # type: ignore
except ImportError:  # minimal fallback
    yaml = None

try:
    import requests  # type: ignore
except ImportError:
    requests = None

DEFAULT_MODEL = os.getenv("TRIAD_MODEL_NAME", "llama3.2:3b")
DEFAULT_ENDPOINT = os.getenv("TRIAD_ENDPOINT", "http://localhost:11434")

RISK_YAML_PATH = Path(__file__).parent / "prompts_agent_triad.yaml"

EXPECTED_SEVERITIES = ["INFO","LOW","MEDIUM","HIGH","CRITICAL"]
EXPECTED_CATEGORIES = ["GOVERNANCE","SECURITY","RELIABILITY","DATA","OTHER"]

def _load_risk_yaml() -> Dict[str, Any]:
    if not RISK_YAML_PATH.exists():
        return {}
    raw = RISK_YAML_PATH.read_text(encoding="utf-8")
    if yaml:
        return yaml.safe_load(raw) or {}
    # fallback naive parser (only top-level triad: and risk_buckets: not strictly required)
    data: Dict[str, Any] = {}
    current_key = None
    for line in raw.splitlines():
        if line.startswith("triad:"):
            current_key = "triad"
            data[current_key] = {}
        elif line.startswith("risk_buckets:"):
            current_key = "risk_buckets"
            data[current_key] = {}
        elif current_key and line.strip().endswith(":") and not line.startswith(" "):
            # new severity bucket
            bucket = line.strip().rstrip(":")
            if current_key == "risk_buckets":
                data[current_key][bucket] = []
        elif current_key == "risk_buckets" and line.strip().startswith("-"):
            item = line.strip().lstrip("- ")
            # last inserted bucket
            if data[current_key]:
                last_bucket = list(data[current_key].keys())[-1]
                data[current_key][last_bucket].append(item)
    return data

_RISK_DATA = _load_risk_yaml()
_RISK_BUCKETS: Dict[str, List[str]] = _RISK_DATA.get("risk_buckets", {})

SIGNAL_TO_SEVERITY: Dict[str, str] = {}
for sev, signals in _RISK_BUCKETS.items():
    for s in signals:
        SIGNAL_TO_SEVERITY[s] = sev

PATTERN_MAP: Dict[str, str] = {
    # regex fragment -> signal id
    r"missing parent seal": "missing_parent_seal",
    r"missing_parent_seal": "missing_parent_seal",
    r"unauthorised.+manifest": "unauthorised_manifest_change",
    r"failed.+audit.+chain": "failed_audit_chain",
    r"degraded node": "degraded_node",
    r"stale policies?": "stale_policies",
    r"validation failure": "repeated_validation_failures",
    r"quorum": "inconsistent_quorum_results",
}

import re
_COMPILED_PATTERNS = [(re.compile(p, re.IGNORECASE), sig) for p, sig in PATTERN_MAP.items()]

def call_model(prompt: str, model: Optional[str] = None, endpoint: Optional[str] = None, timeout: int = 60) -> str:
    model = model or DEFAULT_MODEL
    endpoint = endpoint or DEFAULT_ENDPOINT
    if requests is None:
        # Fallback deterministic stub
        return "[]"
    try:
        resp = requests.post(f"{endpoint}/api/generate", json={"model": model, "prompt": prompt, "stream": False}, timeout=timeout)
        resp.raise_for_status()
        data = resp.json()
        return data.get("response", "")
    except Exception as e:
        return json.dumps({"error": f"model_call_failed: {e}"})

def classify_log_lines(lines: List[str]) -> List[Dict[str, Any]]:
    issues: List[Dict[str, Any]] = []
    for line in lines:
        matched_signals = []
        for rx, sig in _COMPILED_PATTERNS:
            if rx.search(line):
                matched_signals.append(sig)
        for sig in set(matched_signals):
            sev = SIGNAL_TO_SEVERITY.get(sig, "INFO")
            cat = _infer_category(sig)
            issues.append({
                "severity": sev if sev in EXPECTED_SEVERITIES else "INFO",
                "category": cat,
                "signal": sig,
                "summary": f"Detected {sig} in log line",
                "recommended_action": _default_action(sig),
                "source_line": line.strip()[:400]
            })
    return issues

def _infer_category(signal: str) -> str:
    if "manifest" in signal or "policy" in signal:
        return "GOVERNANCE"
    if "seal" in signal or "unauthorised" in signal or "validation" in signal:
        return "SECURITY"
    if "degraded" in signal or "quorum" in signal:
        return "RELIABILITY"
    if "audit" in signal or "chain" in signal:
        return "DATA"
    return "OTHER"

def _default_action(signal: str) -> str:
    mapping = {
        "missing_parent_seal": "Regenerate parent seal or rollback to last sealed manifest; re-run verification harness.",
        "unauthorised_manifest_change": "Investigate commit diff; re-sign manifest if legitimate.",
        "failed_audit_chain": "Recompute chain; verify stored roots; trigger regression event handler.",
        "repeated_validation_failures": "Inspect validator policy logs; escalate if >3 in window.",
        "inconsistent_quorum_results": "Trigger consensus re-evaluation; compare node receipts.",
        "degraded_node": "Check health telemetry; confirm non-critical classification.",
        "stale_policies": "Initiate policy refresh workflow; confirm signature freshness.",
    }
    return mapping.get(signal, "Log for review; no automatic remediation defined.")

def run_triad_on_log(log_path: str, model: Optional[str] = None) -> Dict[str, Any]:
    p = Path(log_path)
    if not p.exists():
        raise FileNotFoundError(f"Log file not found: {log_path}")
    lines = p.read_text(encoding="utf-8", errors="ignore").splitlines()
    signals = classify_log_lines(lines)
    # Optionally call model with summarization prompt if signals present
    model_summary = None
    if signals:
        prompt = _build_summary_prompt(signals)
        model_summary = call_model(prompt, model=model)
    return {
        "input_log": str(p.resolve()),
        "generated_at_utc": datetime.utcnow().isoformat() + "Z",
        "signals": signals,
        "model_summary_raw": model_summary
    }

def _build_summary_prompt(signals: List[Dict[str, Any]]) -> str:
    # Build compact schema prompt for model summarization (not classification)
    lines = [f"{s['signal']}|{s['severity']}|{s['category']}" for s in signals]
    joined = "\n".join(lines[:50])  # cap
    return (
        "You are the Agent Triad. Provide a concise JSON summary with fields: total, critical, high, recommend_focus.\n" \
        + "Signals (signal|severity|category):\n" + joined
    )

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, help="Path to log file")
    ap.add_argument("--model", help="Override TRIAD_MODEL_NAME")
    ap.add_argument("--json", action="store_true", help="Print full JSON output")
    args = ap.parse_args()
    result = run_triad_on_log(args.input, model=args.model)
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"Signals: {len(result['signals'])}")
        for s in result['signals']:
            print(f" - [{s['severity']}] {s['signal']} :: {s['summary']}")
