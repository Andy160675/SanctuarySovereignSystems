#!/usr/bin/env python3
"""
Keyword-Triggered Safety Engine
Part of the Sovereign Safety Suite.

Implements a 3-layer safety pipeline:
1. Measurement (Risk Classification)
2. Response (Redaction + Simulation)
3. Escalation (Audit + Logging)

Aligned with Child Safety Protocol.
"""

import json
import hashlib
import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

# Paths
LEDGER_PATH = Path("governance/ledger/best_practices.jsonl")
SAFETY_LOG_PATH = Path("logs/safety/critical_events.jsonl")
KEYWORDS_PATH = Path("CONFIG/safety/keywords.json")

def utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def log_to_ledger(category: str, detail: str, level: str):
    entry = {
        "timestamp": utc_now_iso(),
        "node_id": "MASTER_SAFETY",
        "agent_id": "SAFETY_ENGINE",
        "topic": f"safety_event:{category}",
        "lesson": detail,
        "level": level,
        "action": "log_event",
        "result": "recorded"
    }
    LEDGER_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(LEDGER_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")

def log_critical_event(redacted_text: str, category: str):
    SAFETY_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp": utc_now_iso(),
        "category": category,
        "event_data": redacted_text,
        "status": "ESCALATED"
    }
    with open(SAFETY_LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")

def classify_risk(text: str) -> str:
    """
    Simulated Risk Classification.
    In production, this would use an encrypted/access-controlled keyword list or ML classifier.
    """
    text_lower = text.lower()
    
    # Placeholder for critical patterns (abstracted)
    critical_triggers = ["[redacted_risk_pattern_a]", "[redacted_risk_pattern_b]"]
    ambiguous_triggers = ["[borderline_pattern_x]", "[borderline_pattern_y]"]
    
    # Simulation: if the user passes a specific flag for testing
    if "TRIGGER_CRITICAL" in text:
        return "critical"
    if "TRIGGER_HIGH" in text:
        return "ambiguous"
        
    return "normal"

def process_message(text: str):
    """3-Layer Safety Pipeline"""
    
    # 1. Measurement Layer
    risk = classify_risk(text)
    
    # 2. Response & 3. Escalation Layers
    if risk == "normal":
        log_to_ledger("clean", "Message processed normally.", "INFO")
        return {"status": "allowed", "response": text}

    if risk == "ambiguous":
        log_to_ledger("high_risk", "High risk deviation recorded.", "WARNING")
        return {
            "status": "mismatch", 
            "response": "This content cannot be reconstructed safely.",
            "level": "high"
        }

    if risk == "critical":
        # Redaction from user view happens by not returning the text
        redacted_summary = "[REDACTED CONTENT - CATEGORY: CHILD_SAFETY]"
        
        log_to_ledger("child_safety", "Critical safety mismatch recorded and escalated.", "CRITICAL")
        log_critical_event(redacted_summary, "child_safety")
        
        return {
            "status": "mismatch", 
            "response": "This request has been measured as a deviation for safety reasons.",
            "level": "critical"
        }

def main():
    parser = argparse.ArgumentParser(description="Process a message through the safety engine.")
    parser.add_argument("text", type=str, help="The input text to scan")
    args = parser.parse_args()
    
    result = process_message(args.text)
    print(json.dumps(result, indent=2))
    return 0

if __name__ == "__main__":
    sys.exit(main())
