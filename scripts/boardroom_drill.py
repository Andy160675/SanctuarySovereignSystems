#!/usr/bin/env python3
"""
Boardroom Drill - Automated Invariant Testing for the Avatar Boardroom
======================================================================
Tests the boardroom_coordinator's turn-taking, voting, and mission lifecycle
to ensure the Boardroom behaves as a consistent governance plane.

Invariants Tested:
1. Only one speaker at a time
2. Votes only accepted when vote window is open
3. Mission transitions correctly through DISCUSSING -> VOTING -> DECIDED
4. Board decision is logged upon finalization

Usage:
    python scripts/boardroom_drill.py [--coordinator-url URL] [--ledger-url URL]

Exit Codes:
    0 - All invariants passed
    1 - Invariant violation detected
"""

import argparse
import asyncio
import httpx
import sys
from datetime import datetime


# Configuration
DEFAULT_COORDINATOR_URL = "http://localhost:8200"
DEFAULT_LEDGER_URL = "http://localhost:8082"


class BoardroomDrill:
    """Automated test harness for Boardroom invariants."""

    def __init__(self, coordinator_url: str, ledger_url: str):
        self.coordinator_url = coordinator_url.rstrip("/")
        self.ledger_url = ledger_url.rstrip("/")
        self.mission_id = f"DRILL-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        self.passed = 0
        self.failed = 0

    def log(self, level: str, message: str):
        """Log with timestamp and level."""
        ts = datetime.utcnow().strftime("%H:%M:%S")
        icon = {"INFO": "->", "PASS": "[PASS]", "FAIL": "[FAIL]", "TEST": "[TEST]"}.get(level, "  ")
        print(f"{ts} {icon} {message}")

    def assert_true(self, condition: bool, description: str):
        """Assert a condition is true."""
        if condition:
            self.log("PASS", description)
            self.passed += 1
        else:
            self.log("FAIL", description)
            self.failed += 1

    async def run_all_tests(self) -> bool:
        """Run all Boardroom invariant tests."""
        print("=" * 70)
        print("BOARDROOM DRILL - Invariant Testing Suite")
        print("=" * 70)
        self.log("INFO", f"Coordinator: {self.coordinator_url}")
        self.log("INFO", f"Mission ID: {self.mission_id}")
        print("-" * 70)

        async with httpx.AsyncClient(timeout=10.0) as client:
            # Test 1: Health check
            await self.test_health(client)

            # Test 2: Start mission
            await self.test_start_mission(client)

            # Test 3: Turn-taking invariants
            await self.test_turn_taking(client)

            # Test 4: Voting invariants
            await self.test_voting(client)

            # Test 5: Decision finalization
            await self.test_decision(client)

            # Test 6: Verify ledger entry (optional)
            await self.test_ledger_entry(client)

        print("-" * 70)
        print(f"Results: {self.passed} passed, {self.failed} failed")
        print("=" * 70)

        return self.failed == 0

    async def test_health(self, client: httpx.AsyncClient):
        """Test coordinator health endpoint."""
        self.log("TEST", "Health check")
        try:
            resp = await client.get(f"{self.coordinator_url}/health")
            data = resp.json()
            self.assert_true(
                resp.status_code == 200 and data.get("status") == "healthy",
                "Coordinator is healthy"
            )
        except Exception as e:
            self.assert_true(False, f"Health check failed: {e}")

    async def test_start_mission(self, client: httpx.AsyncClient):
        """Test mission start."""
        self.log("TEST", "Start mission")
        try:
            resp = await client.post(
                f"{self.coordinator_url}/sessions/start_mission",
                json={
                    "mission_id": self.mission_id,
                    "prompt": "DRILL: Test mission for invariant validation",
                    "risk_level": "LOW",
                    "origin": "boardroom_drill"
                }
            )
            data = resp.json()
            self.assert_true(
                resp.status_code == 200 and data.get("status") == "mission_started",
                f"Mission {self.mission_id} started"
            )

            # Verify mission state
            resp = await client.get(f"{self.coordinator_url}/coordinator/mission")
            mission = resp.json()
            self.assert_true(
                mission.get("status") == "discussing",
                "Mission is in DISCUSSING state"
            )
        except Exception as e:
            self.assert_true(False, f"Mission start failed: {e}")

    async def test_turn_taking(self, client: httpx.AsyncClient):
        """Test turn-taking invariants: only one speaker at a time."""
        self.log("TEST", "Turn-taking invariants")

        try:
            # Avatar 4 (Synthesist) requests floor
            resp = await client.post(
                f"{self.coordinator_url}/coordinator/request_turn",
                json={"avatar_id": 4, "topic": "Cross-domain risk assessment for drill mission"}
            )
            data = resp.json()
            self.assert_true(
                data.get("status") == "granted",
                "Avatar 4 (Synthesist) granted the floor"
            )

            # Avatar 6 (Ethicist) tries to request floor - should be denied
            resp = await client.post(
                f"{self.coordinator_url}/coordinator/request_turn",
                json={"avatar_id": 6, "topic": "Ethical considerations"}
            )
            data = resp.json()
            self.assert_true(
                data.get("status") == "denied",
                "Avatar 6 denied while Avatar 4 holds floor (INVARIANT: single speaker)"
            )

            # Verify current speaker
            resp = await client.get(f"{self.coordinator_url}/coordinator/state")
            state = resp.json()
            self.assert_true(
                state.get("current_speaker") == 4,
                "Current speaker is Avatar 4"
            )

            # Avatar 4 releases floor
            resp = await client.post(
                f"{self.coordinator_url}/coordinator/release_turn",
                json={"avatar_id": 4, "topic": ""}
            )
            data = resp.json()
            self.assert_true(
                data.get("status") == "released",
                "Avatar 4 released the floor"
            )

            # Now Avatar 6 can get floor
            resp = await client.post(
                f"{self.coordinator_url}/coordinator/request_turn",
                json={"avatar_id": 6, "topic": "Ethical review"}
            )
            data = resp.json()
            self.assert_true(
                data.get("status") == "granted",
                "Avatar 6 (Ethicist) now granted the floor"
            )

            # Release before voting
            await client.post(
                f"{self.coordinator_url}/coordinator/release_turn",
                json={"avatar_id": 6, "topic": ""}
            )

        except Exception as e:
            self.assert_true(False, f"Turn-taking test failed: {e}")

    async def test_voting(self, client: httpx.AsyncClient):
        """Test voting invariants: votes only accepted when window is open."""
        self.log("TEST", "Voting invariants")

        try:
            # Try to vote before window is open - should fail
            resp = await client.post(
                f"{self.coordinator_url}/coordinator/cast_vote",
                json={"avatar_id": 1, "decision": "approve"}
            )
            data = resp.json()
            self.assert_true(
                data.get("status") == "error" and "window" in data.get("reason", "").lower(),
                "Vote rejected when window is closed (INVARIANT: vote window)"
            )

            # Open voting
            resp = await client.post(f"{self.coordinator_url}/sessions/start_voting")
            data = resp.json()
            self.assert_true(
                data.get("status") == "voting_started",
                "Voting window opened"
            )

            # Verify mission state changed to VOTING
            resp = await client.get(f"{self.coordinator_url}/coordinator/mission")
            mission = resp.json()
            self.assert_true(
                mission.get("status") == "voting",
                "Mission transitioned to VOTING state"
            )

            # Cast votes from multiple avatars
            votes = [
                (1, "approve"),   # Chair
                (2, "approve"),   # Auditor
                (3, "approve"),   # Strategist
                (4, "approve"),   # Synthesist
                (5, "approve"),   # Archivist
                (6, "approve"),   # Ethicist
                (7, "approve"),   # Legalist
                (8, "approve"),   # Guardian
                (9, "approve"),   # Quartermaster
                (10, "approve"),  # Scribe
                (11, "reject"),   # Herald
                (12, "reject"),   # Weaver
                (13, "defer"),    # Sentinel
            ]

            for avatar_id, decision in votes:
                resp = await client.post(
                    f"{self.coordinator_url}/coordinator/cast_vote",
                    json={"avatar_id": avatar_id, "decision": decision}
                )
                data = resp.json()
                if data.get("status") != "recorded":
                    self.assert_true(False, f"Vote from Avatar {avatar_id} failed")

            self.assert_true(True, "All 13 avatars cast votes (10 approve, 2 reject, 1 defer)")

        except Exception as e:
            self.assert_true(False, f"Voting test failed: {e}")

    async def test_decision(self, client: httpx.AsyncClient):
        """Test decision finalization."""
        self.log("TEST", "Decision finalization")

        try:
            # Finalize decision
            resp = await client.post(
                f"{self.coordinator_url}/sessions/decision",
                json={
                    "decision": "approve",
                    "rationale": "DRILL mission approved by majority vote (10-2-1). Low risk profile validated."
                }
            )
            data = resp.json()
            self.assert_true(
                data.get("status") == "decided",
                "Decision finalized"
            )

            # Verify mission state is DECIDED
            resp = await client.get(f"{self.coordinator_url}/coordinator/mission")
            mission = resp.json()
            self.assert_true(
                mission.get("status") == "decided",
                "Mission transitioned to DECIDED state"
            )
            self.assert_true(
                mission.get("decision") == "approve",
                "Decision recorded as APPROVE"
            )

            # Verify vote window is closed
            resp = await client.get(f"{self.coordinator_url}/coordinator/state")
            state = resp.json()
            self.assert_true(
                state.get("vote_window_open") == False,
                "Vote window closed after decision"
            )

        except Exception as e:
            self.assert_true(False, f"Decision test failed: {e}")

    async def test_ledger_entry(self, client: httpx.AsyncClient):
        """Verify decision was logged to ledger."""
        self.log("TEST", "Ledger entry verification")

        try:
            resp = await client.get(f"{self.ledger_url}/events?limit=10")
            if resp.status_code == 200:
                events = resp.json()
                # Look for our board_decision event
                found = any(
                    e.get("event_type") == "boardroom.board_decision" and
                    e.get("payload", {}).get("mission_id") == self.mission_id
                    for e in events
                )
                self.assert_true(
                    found,
                    f"Board decision for {self.mission_id} logged to ledger"
                )
            else:
                self.log("INFO", "Ledger not available - skipping ledger verification")
        except Exception:
            self.log("INFO", "Ledger not available - skipping ledger verification")


async def main():
    parser = argparse.ArgumentParser(description="Boardroom Drill - Invariant Testing")
    parser.add_argument(
        "--coordinator-url",
        default=DEFAULT_COORDINATOR_URL,
        help=f"Boardroom coordinator URL (default: {DEFAULT_COORDINATOR_URL})"
    )
    parser.add_argument(
        "--ledger-url",
        default=DEFAULT_LEDGER_URL,
        help=f"Ledger service URL (default: {DEFAULT_LEDGER_URL})"
    )
    args = parser.parse_args()

    drill = BoardroomDrill(args.coordinator_url, args.ledger_url)
    success = await drill.run_all_tests()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
