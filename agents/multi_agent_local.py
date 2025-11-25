#!/usr/bin/env python3
"""
Sovereign System - Multi-Agent Local PoC
=========================================
Pure local multi-agent system using queue.Queue for inter-agent communication.
No HTTP, no Flask, no backend - just agents in a single Python process.

Agents:
  - SeedAgent:    Seeds evidence with expected hash
  - VerifyAgent:  Recomputes hash, emits verify_result
  - EnforceAgent: Reacts to mismatches (tamper detection)

Run:
  python multi_agent_local.py

This demonstrates the agent communication pattern without any network overhead.
"""

import hashlib
import json
import queue
import threading
import time
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional

# =============================================================================
# MESSAGE TYPES
# =============================================================================

@dataclass
class Message:
    """Inter-agent message."""
    type: str
    sender: str
    data: Dict[str, Any]
    timestamp: str

    def to_dict(self) -> dict:
        return asdict(self)


# =============================================================================
# EVIDENCE STORE
# =============================================================================

ROOT = Path(__file__).parent.parent.resolve()
EVIDENCE_ROOT = ROOT / "evidence_store"
CASE_ID = "CASE-TEST-001"
CASE_DIR = EVIDENCE_ROOT / CASE_ID


def hash_file(filepath: Path) -> str:
    """Compute SHA-256 hash of a file."""
    h = hashlib.sha256()
    with filepath.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def ensure_evidence() -> tuple[Path, str]:
    """Ensure evidence file exists and return (path, hash)."""
    CASE_DIR.mkdir(parents=True, exist_ok=True)

    mock_file = CASE_DIR / "mock-event-1.jsonl"

    if not mock_file.exists():
        event = {
            "id": "mock-event-1",
            "case_id": CASE_ID,
            "ts": datetime.now(timezone.utc).isoformat(),
            "type": "evidence",
            "payload": {
                "text": "This is a tamper-test artifact. Change this file to see mismatch behavior."
            }
        }
        with mock_file.open("w", encoding="utf-8") as f:
            f.write(json.dumps(event, sort_keys=True) + "\n")

    return mock_file, hash_file(mock_file)


# =============================================================================
# BASE AGENT
# =============================================================================

class BaseAgent:
    """Base class for all agents."""

    def __init__(self, name: str, inbox: queue.Queue, outbox: queue.Queue):
        self.name = name
        self.inbox = inbox
        self.outbox = outbox
        self.running = False
        self._thread: Optional[threading.Thread] = None

    def start(self):
        """Start agent in background thread."""
        self.running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        print(f"  [{self.name}] Started")

    def stop(self):
        """Stop agent."""
        self.running = False
        if self._thread:
            self._thread.join(timeout=1.0)
        print(f"  [{self.name}] Stopped")

    def _run_loop(self):
        """Main agent loop - process messages from inbox."""
        while self.running:
            try:
                msg = self.inbox.get(timeout=0.5)
                self.handle_message(msg)
            except queue.Empty:
                continue
            except Exception as e:
                print(f"  [{self.name}] Error: {e}")

    def handle_message(self, msg: Message):
        """Override in subclass to handle messages."""
        raise NotImplementedError

    def send(self, msg_type: str, data: Dict[str, Any]):
        """Send message to outbox."""
        msg = Message(
            type=msg_type,
            sender=self.name,
            data=data,
            timestamp=datetime.now(timezone.utc).isoformat()
        )
        self.outbox.put(msg)
        print(f"  [{self.name}] Sent: {msg_type}")


# =============================================================================
# SEED AGENT
# =============================================================================

class SeedAgent(BaseAgent):
    """
    Seeds evidence with expected hash.
    Listens for: seed_request
    Emits: evidence_seeded
    """

    def __init__(self, inbox: queue.Queue, outbox: queue.Queue):
        super().__init__("SeedAgent", inbox, outbox)

    def handle_message(self, msg: Message):
        if msg.type == "seed_request":
            case_id = msg.data.get("case_id", CASE_ID)

            # Ensure evidence exists and get hash
            evidence_path, evidence_hash = ensure_evidence()

            self.send("evidence_seeded", {
                "case_id": case_id,
                "evidence_path": str(evidence_path),
                "expected_hash": evidence_hash
            })


# =============================================================================
# VERIFY AGENT
# =============================================================================

class VerifyAgent(BaseAgent):
    """
    Recomputes hash and verifies against expected.
    Listens for: evidence_seeded
    Emits: verify_result
    """

    def __init__(self, inbox: queue.Queue, outbox: queue.Queue):
        super().__init__("VerifyAgent", inbox, outbox)

    def handle_message(self, msg: Message):
        if msg.type == "evidence_seeded":
            evidence_path = Path(msg.data["evidence_path"])
            expected_hash = msg.data["expected_hash"]
            case_id = msg.data["case_id"]

            if not evidence_path.exists():
                self.send("verify_result", {
                    "case_id": case_id,
                    "status": "error",
                    "error": "File not found",
                    "path": str(evidence_path)
                })
                return

            # Recompute hash
            actual_hash = hash_file(evidence_path)
            match = (actual_hash == expected_hash)

            self.send("verify_result", {
                "case_id": case_id,
                "match": match,
                "status": "verified" if match else "TAMPERED",
                "actual_hash": actual_hash,
                "expected_hash": expected_hash,
                "path": str(evidence_path)
            })


# =============================================================================
# ENFORCE AGENT
# =============================================================================

class EnforceAgent(BaseAgent):
    """
    Reacts to verification results.
    Listens for: verify_result
    Emits: enforcement_action
    """

    def __init__(self, inbox: queue.Queue, outbox: queue.Queue):
        super().__init__("EnforceAgent", inbox, outbox)

    def handle_message(self, msg: Message):
        if msg.type == "verify_result":
            case_id = msg.data["case_id"]
            status = msg.data.get("status", "unknown")
            match = msg.data.get("match", False)

            if status == "TAMPERED":
                action = "quarantine"
                severity = "critical"
                message = f"TAMPER DETECTED: Hash mismatch for {msg.data.get('path')}"
            elif status == "verified":
                action = "log"
                severity = "info"
                message = "Evidence integrity verified"
            else:
                action = "flag"
                severity = "warning"
                message = f"Verification status unclear: {status}"

            self.send("enforcement_action", {
                "case_id": case_id,
                "action": action,
                "severity": severity,
                "message": message,
                "verification_status": status
            })

            # Print result prominently
            if status == "TAMPERED":
                print(f"\n  [!] ALERT: {message}\n")
            else:
                print(f"\n  [OK] {message}\n")


# =============================================================================
# ORCHESTRATOR
# =============================================================================

class LocalOrchestrator:
    """
    Orchestrates the three agents using message queues.
    Routes messages between agents based on type.
    """

    def __init__(self):
        # Create queues for each agent
        self.seed_inbox = queue.Queue()
        self.verify_inbox = queue.Queue()
        self.enforce_inbox = queue.Queue()
        self.results = queue.Queue()

        # Create agents with appropriate routing
        self.seed_agent = SeedAgent(self.seed_inbox, self.verify_inbox)
        self.verify_agent = VerifyAgent(self.verify_inbox, self.enforce_inbox)
        self.enforce_agent = EnforceAgent(self.enforce_inbox, self.results)

        self.agents = [self.seed_agent, self.verify_agent, self.enforce_agent]

    def start(self):
        """Start all agents."""
        print("\nStarting agents...")
        for agent in self.agents:
            agent.start()
        time.sleep(0.2)  # Let threads initialize

    def stop(self):
        """Stop all agents."""
        print("\nStopping agents...")
        for agent in self.agents:
            agent.stop()

    def run_case(self, case_id: str) -> Dict[str, Any]:
        """Run a full verification case."""
        print(f"\n{'='*60}")
        print(f"  Running case: {case_id}")
        print(f"{'='*60}")

        # Trigger the pipeline
        seed_msg = Message(
            type="seed_request",
            sender="Orchestrator",
            data={"case_id": case_id},
            timestamp=datetime.now(timezone.utc).isoformat()
        )
        self.seed_inbox.put(seed_msg)

        # Wait for result
        try:
            result = self.results.get(timeout=5.0)
            return result.to_dict()
        except queue.Empty:
            return {"error": "Timeout waiting for result"}


# =============================================================================
# MAIN
# =============================================================================

def main():
    print("=" * 60)
    print("  SOVEREIGN MULTI-AGENT LOCAL PoC")
    print("  Pure Python Queue-Based Communication")
    print("=" * 60)
    print()
    print("Agents:")
    print("  - SeedAgent:    Seeds evidence with expected hash")
    print("  - VerifyAgent:  Recomputes hash, emits verify_result")
    print("  - EnforceAgent: Reacts to mismatches")
    print()
    print(f"Evidence store: {EVIDENCE_ROOT}")
    print()

    orchestrator = LocalOrchestrator()

    try:
        orchestrator.start()

        # Run test case
        result = orchestrator.run_case(CASE_ID)

        print("\nFinal Result:")
        print(json.dumps(result, indent=2))

        # Demo: tamper detection
        print("\n" + "=" * 60)
        print("  TAMPER TEST")
        print("=" * 60)
        print(f"\nTo test tamper detection:")
        print(f"  1. Edit: {CASE_DIR / 'mock-event-1.jsonl'}")
        print(f"  2. Run this script again")
        print(f"  3. You'll see: TAMPER DETECTED")

    finally:
        orchestrator.stop()

    print("\nDone.")


if __name__ == "__main__":
    main()
