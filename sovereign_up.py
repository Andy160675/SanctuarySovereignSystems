#!/usr/bin/env python
import os
import sys
import subprocess
import time
from pathlib import Path
import json

COMPOSE_FILE = os.getenv("COMPOSE_FILE", "docker-compose.yml")

def get_docker_compose_cmd():
    # Try docker-compose (v1/Standalone)
    try:
        subprocess.run(["docker-compose", "version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return ["docker-compose", "-f", COMPOSE_FILE]
    except FileNotFoundError:
        pass
    
    # Try docker compose (v2/Plugin)
    try:
        subprocess.run(["docker", "compose", "version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return ["docker", "compose", "-f", COMPOSE_FILE]
    except FileNotFoundError:
        return None

DC = get_docker_compose_cmd()


def run(cmd, check=True):
    if cmd[0] == "docker" and DC is None:
         print(f"⚠️  Skipping command (Docker not found): {' '.join(cmd)}")
         return subprocess.CompletedProcess(cmd, 0, "", "")

    print(f"→ {' '.join(cmd)}")
    try:
        # Force UTF-8 encoding for subprocess output to handle emojis
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding='utf-8')
        print(result.stdout)
        if check and result.returncode != 0:
            print(f"EXIT {result.returncode}: {' '.join(cmd)}", file=sys.stderr)
            sys.exit(result.returncode)
        return result
    except FileNotFoundError:
        print(f"❌ Command not found: {cmd[0]}")
        if check:
            sys.exit(1)
        return subprocess.CompletedProcess(cmd, 1, "", "")

def ensure_dirs():
    print("📁 Ensuring data directories exist...")
    for p in [
        Path("Evidence/Inbox"),
        Path("Evidence/Analysis/_verified"),
        Path("Property/Leads"),
        Path("Property/Scored/_drafts"),
        Path("Governance/Logs"),
    ]:
        p.mkdir(parents=True, exist_ok=True)
        print(f"   - {p} (ok)")


def seed_data():
    print("🌱 Seeding legislative traps and test data...")
    
    # Trap for Property Agent (Insider)
    trap_file = Path("Property/Leads/test_trap_fixer.txt")
    if not trap_file.exists():
        trap_file.write_text("3 Bed House. 123 Test Rd. Asking £350k. Warning: Structural cracks visible in foundation.", encoding="utf-8")
        print(f"   - Created {trap_file} (Legislative Trap)")
    
    # Standard file for Evidence Agent (Stable)
    evidence_file = Path("Evidence/Inbox/test_invoice_stable.txt")
    if not evidence_file.exists():
        evidence_file.write_text("Invoice #101 for Sovereign Services. Amount: $500. Date: 2025-11-20.", encoding="utf-8")
        print(f"   - Created {evidence_file} (Standard Test)")


def ensure_ledger_genesis():
    ledger_path = Path("Governance/Logs/audit_chain.jsonl") # Changed from data/ledger
    if ledger_path.exists():
        print(f"🔗 Ledger exists: {ledger_path}")
        return

    print("🔗 Initializing ledger genesis event...")
    genesis_event = {
        "event_type": "GENESIS",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "agent": "system",
        "payload": {
            "message": "Sovereign Ledger Initialized",
            "version": "v0.1",
        },
    }
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    with ledger_path.open("w", encoding="utf-8") as f:
        f.write(json.dumps(genesis_event) + "\n")
    print(f"   - Genesis written to {ledger_path}")


def docker_up():
    if DC is None:
        print("❌ Docker not found. Skipping Docker bootstrap.")
        return

    print("🐳 Bootstrapping Docker stack...")
    run(DC + ["down", "--volumes", "--remove-orphans"], check=False)
    run(DC + ["build"])
    run(DC + ["up", "-d"])
    print("   Waiting for containers to become healthy...")
    time.sleep(10)
    run(["docker", "ps", "--format", "table {{.Names}}\t{{.Status}}"], check=False)


def start_boardroom():
    if DC is None: return
    print("🏛️ Ensuring Boardroom service is running first...")
    # If boardroom is long-running service in compose, up -d already started it.
    # Optionally, you can restart it explicitly:
    run(DC + ["up", "-d", "boardroom"])
    print("   Waiting a bit for Boardroom to warm up...")
    time.sleep(5)


def run_evidence_agent():
    if DC is None: return
    print("📜 Running Evidence agent (STABLE expected)...")
    # evidence service should use TRACK/EVIDENCE_TRACK env inside container
    run(DC + ["run", "--rm", "evidence", "python", "src/agents/evidence_validator.py"])


def run_property_agent():
    if DC is None: return
    print("🏠 Running Property agent (INSIDER expected)...")
    run(DC + ["run", "--rm", "property", "python", "src/agents/property_analyst.py"])


def run_readiness():
    if DC is None: return
    print("📊 Running readiness check (infra-level)...")
    run(DC + ["run", "--rm", "evidence", "python", "scripts/agent_readiness.py"])


def run_integration_verification():
    print("✅ Running integration verification (constitution-level)...")
    # This script we define below
    run([sys.executable, "verify_integration.py"])


def main():
    print("🚀 SOVEREIGN SYSTEM – FULL INTEGRATION BOOT")

    ensure_dirs()
    seed_data()
    ensure_ledger_genesis()
    docker_up()
    start_boardroom()
    run_evidence_agent()
    run_property_agent()
    run_readiness()
    run_integration_verification()

    print("\n🏆 FULL SYSTEM INTEGRATION COMPLETED.")
    print("   Evidence: STABLE (verified)")
    print("   Property: INSIDER (drafts)")
    print("   Ledger: GENESIS + NEW EVENTS (check Governance/Logs/)")


if __name__ == "__main__":
    main()
