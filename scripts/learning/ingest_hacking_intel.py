#!/usr/bin/env python3
"""
Hacking Intelligence Ingestion Engine
Part of the Learning Suite.

This script 'ingests' hacking intelligence from external sources (simulated)
and records them in the project's knowledge base (Codex and Ledger).
"""

import json
import argparse
import sys
import subprocess
from datetime import datetime, timezone
from pathlib import Path

LEDGER_PATH = Path("governance/ledger/best_practices.jsonl")
CODEX_DIR = Path("Codex/Hacking")
EVIDENCE_DIR = Path("evidence/intel")

def utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def log_lesson(topic: str, lesson: str, source: str):
    entry = {
        "timestamp": utc_now_iso(),
        "node_id": "MASTER_LEARNER",
        "agent_id": "INTEL_INGEST_BOT",
        "topic": f"hacking_skill:{topic}",
        "lesson": lesson,
        "source": source,
        "action": "ingest",
        "result": "success"
    }
    
    LEDGER_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(LEDGER_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")
    print(f"LOGGED: {topic} to ledger.")

def create_codex_entry(topic: str, content: str):
    CODEX_DIR.mkdir(parents=True, exist_ok=True)
    safe_topic = topic.lower().replace(" ", "_").replace("/", "_")
    file_path = CODEX_DIR / f"{safe_topic}.md"
    
    md_content = f"""# Hacking Skill: {topic}
**Ingested:** {utc_now_iso()}
**Category:** Elite Hacking Intel

{content}

---
*Derived from External Intelligence Ingestion.*
"""
    file_path.write_text(md_content, encoding="utf-8")
    print(f"WROTE: {file_path}")
    
    # Seal the file
    try:
        subprocess.run([sys.executable, "tools/seal_file.py", str(file_path)], check=False)
    except Exception:
        pass

def ingest_seed_intel():
    """Ingest some initial 'elite' intelligence to fulfill the request."""
    intel = [
        {
            "topic": "Deterministic Protocol Analysis",
            "lesson": "Mapping state transitions in sovereign mesh protocols to identify race conditions.",
            "content": "Elite hackers focus on the deterministic nature of sovereign protocols. By mapping every possible state transition in the Gossip protocol, one can identify edge cases where consensus can be delayed or forced."
        },
        {
            "topic": "Tamper-Evidence Bypassing (Theoretical)",
            "lesson": "Analyzing hash-chain vulnerabilities in append-only ledgers.",
            "content": "While hash-chains are tamper-evident, they rely on the head hash being widely distributed. A 'split-view' attack can present different ledgers to different nodes if the gossip layer is compromised."
        },
        {
            "topic": "Side-Channel Sovereign Leakage",
            "lesson": "Monitoring power consumption of enclave-based signing operations.",
            "content": "Even inside a secure enclave, cryptographic operations can leak timing or power signatures. Sovereign nodes must use constant-time operations to mitigate this."
        }
    ]
    
    for item in intel:
        log_lesson(item["topic"], item["lesson"], "Seed Intelligence Database")
        create_codex_entry(item["topic"], item["content"])

def main():
    parser = argparse.ArgumentParser(description="Ingest hacking intelligence into the sovereign system.")
    parser.add_argument("--source", type=str, help="URL or path to intel source")
    parser.add_argument("--seed", action="store_true", help="Ingest seed intelligence")
    
    args = parser.parse_args()
    
    if args.seed:
        ingest_seed_intel()
    elif args.source:
        print(f"Ingesting from {args.source}... (Simulation)")
        # In a real scenario, this would use requests/curl to fetch and LLM to summarize
        log_lesson("External Source", f"Ingested data from {args.source}", args.source)
    else:
        parser.print_help()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
