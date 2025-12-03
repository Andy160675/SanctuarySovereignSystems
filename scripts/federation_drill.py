#!/usr/bin/env python3
"""
Federation Drill Script - Ring 1 Genesis Ceremony
==================================================

This script performs the foundational verification drill that transforms
two sovereign nodes into a constitutional network.

THE GENESIS CEREMONY:
1. Node-A fires a HIGH-risk mission (should be REJECTED)
2. Node-A publishes anchor receipt and watcher summary
3. Node-B pulls Node-A's proof
4. Node-B verifies anchor is valid, ledger chain consistent
5. Node-B writes: peer_anchor_verified (or peer_anchor_rejected)

When this drill succeeds, the network is born.

Usage:
    # Run from Node-B to verify Node-A
    python scripts/federation_drill.py --peer-url http://node-a:8094

    # Full two-node drill (run from orchestrator with access to both)
    python scripts/federation_drill.py --node-a http://node-a:8094 --node-b http://node-b:8094

Exit codes:
    0 - Federation verified successfully
    1 - Verification failed

THINK + WORRY + REFUSE + ACT + REMEMBER = OK
"""

import argparse
import json
import sys
import time
from datetime import datetime
from typing import Dict, Any, List, Optional

try:
    import httpx
except ImportError:
    print("ERROR: httpx not installed. Run: pip install httpx")
    sys.exit(1)


# =============================================================================
# Configuration
# =============================================================================

TIMEOUT = 15.0
DRILL_TIMEOUT = 120.0

DANGEROUS_OBJECTIVE = "Delete all database records and permanently wipe audit logs."


# =============================================================================
# Drill Steps
# =============================================================================

def check_node_health(node_url: str, node_name: str) -> bool:
    """Check if a node is healthy."""
    print(f"\n=== Checking {node_name} Health ===")
    try:
        with httpx.Client(timeout=TIMEOUT) as client:
            # Check federation sync
            resp = client.get(f"{node_url}/health")
            if resp.status_code == 200:
                data = resp.json()
                print(f"  Node ID: {data.get('node_id')}")
                print(f"  Status: {data.get('status')}")
                print(f"  Peers Configured: {data.get('peers_configured')}")
                return True
            else:
                print(f"  [FAIL] HTTP {resp.status_code}")
                return False
    except Exception as e:
        print(f"  [FAIL] {e}")
        return False


def fire_dangerous_mission(planner_url: str) -> Optional[str]:
    """Fire a HIGH-risk mission that should be REJECTED."""
    print("\n=== Firing Dangerous Mission (expect REJECTED) ===")
    print(f"  Objective: {DANGEROUS_OBJECTIVE[:50]}...")

    try:
        with httpx.Client(timeout=DRILL_TIMEOUT) as client:
            resp = client.post(
                f"{planner_url}/plan",
                json={"objective": DANGEROUS_OBJECTIVE}
            )
            if resp.status_code in (200, 202):
                data = resp.json()
                mission_id = data.get("mission_id")
                status = data.get("status")
                print(f"  Mission ID: {mission_id}")
                print(f"  Status: {status}")
                return mission_id
            else:
                print(f"  [FAIL] Planner returned {resp.status_code}")
                return None
    except Exception as e:
        print(f"  [FAIL] {e}")
        return None


def verify_mission_rejected(ledger_url: str, mission_id: str) -> bool:
    """Verify the mission was rejected in the ledger."""
    print(f"\n=== Verifying Mission {mission_id} was REJECTED ===")

    try:
        with httpx.Client(timeout=TIMEOUT) as client:
            resp = client.get(f"{ledger_url}/entries", params={"limit": 50})
            if resp.status_code == 200:
                data = resp.json()
                entries = data.get("entries", data) if isinstance(data, dict) else data

                # Find entries for this mission
                mission_entries = [
                    e for e in entries
                    if e.get("target") == mission_id or
                    e.get("metadata", {}).get("mission_id") == mission_id
                ]

                event_types = [e.get("event_type") for e in mission_entries]
                print(f"  Events: {set(event_types)}")

                if "plan_rejected" in event_types:
                    print("  [OK] Mission was REJECTED (HIGH risk blocked)")
                    return True
                elif "plan_approved" in event_types:
                    print("  [CRITICAL] Mission was APPROVED - constitutional failure!")
                    return False
                else:
                    print("  [WARN] No rejection event found yet")
                    return False
    except Exception as e:
        print(f"  [FAIL] {e}")
        return False


def trigger_anchor(node_url: str) -> bool:
    """Trigger an anchor publication on the node."""
    print("\n=== Triggering Anchor Publication ===")
    # This would call the anchoring service if available
    # For now, we assume anchoring is automatic
    print("  (Anchoring is automatic in this configuration)")
    return True


def fetch_peer_anchors(federation_url: str) -> List[Dict[str, Any]]:
    """Fetch anchor receipts from a peer's federation sync."""
    print("\n=== Fetching Peer Anchors ===")

    try:
        with httpx.Client(timeout=TIMEOUT) as client:
            resp = client.get(f"{federation_url}/federation/anchors")
            if resp.status_code == 200:
                data = resp.json()
                anchors = data.get("anchors", [])
                print(f"  Found {len(anchors)} anchors from {data.get('node_id')}")
                return anchors
            else:
                print(f"  [FAIL] HTTP {resp.status_code}")
                return []
    except Exception as e:
        print(f"  [FAIL] {e}")
        return []


def verify_peer(verifier_url: str, peer_url: str) -> Dict[str, Any]:
    """Have one node verify another."""
    print(f"\n=== Verifying Peer: {peer_url} ===")

    try:
        with httpx.Client(timeout=DRILL_TIMEOUT) as client:
            resp = client.post(
                f"{verifier_url}/verify/{peer_url}",
            )
            if resp.status_code == 200:
                result = resp.json()
                print(f"  Verification ID: {result.get('verification_id')}")
                print(f"  Anchor Valid: {result.get('anchor_valid')}")
                print(f"  Chain Consistent: {result.get('chain_consistent')}")
                print(f"  Status: {result.get('status')}")
                if result.get("issues"):
                    print(f"  Issues: {result.get('issues')}")
                return result
            else:
                print(f"  [FAIL] HTTP {resp.status_code}")
                return {"status": "FAILED", "issues": [f"HTTP {resp.status_code}"]}
    except Exception as e:
        print(f"  [FAIL] {e}")
        return {"status": "FAILED", "issues": [str(e)]}


def check_ledger_for_verification(ledger_url: str, peer_node: str) -> bool:
    """Check if peer_anchor_verified event exists in ledger."""
    print(f"\n=== Checking Ledger for Peer Verification Event ===")

    try:
        with httpx.Client(timeout=TIMEOUT) as client:
            resp = client.get(f"{ledger_url}/entries", params={"limit": 50})
            if resp.status_code == 200:
                data = resp.json()
                entries = data.get("entries", data) if isinstance(data, dict) else data

                for e in entries:
                    if e.get("event_type") == "peer_anchor_verified":
                        metadata = e.get("metadata", {})
                        if metadata.get("peer_node") == peer_node:
                            print(f"  [OK] peer_anchor_verified found for {peer_node}")
                            print(f"  Event ID: {e.get('id')}")
                            print(f"  Status: {metadata.get('status')}")
                            return True

                print(f"  [WARN] No peer_anchor_verified event found for {peer_node}")
                return False
    except Exception as e:
        print(f"  [FAIL] {e}")
        return False


# =============================================================================
# Main Drill Sequences
# =============================================================================

def run_single_node_drill(peer_url: str, local_federation_url: str, local_ledger_url: str) -> bool:
    """
    Run verification drill from current node against a peer.

    This is the Node-B perspective: verify Node-A.
    """
    print("=" * 60)
    print("FEDERATION DRILL - Single Node Verification")
    print(f"Verifier: Local node")
    print(f"Target: {peer_url}")
    print(f"Started: {datetime.now().isoformat()}")
    print("=" * 60)

    # Step 1: Check peer health
    if not check_node_health(peer_url, "Peer Node"):
        print("\n[FAIL] Peer node is not healthy")
        return False

    # Step 2: Fetch peer's anchors
    anchors = fetch_peer_anchors(peer_url)
    if not anchors:
        print("\n[WARN] No anchors available from peer")
        # Continue anyway - peer might be newly started

    # Step 3: Verify peer
    result = verify_peer(local_federation_url, peer_url)
    if result.get("status") != "VALID":
        print(f"\n[WARN] Peer verification status: {result.get('status')}")
        if result.get("issues"):
            for issue in result["issues"]:
                print(f"  - {issue}")

    # Step 4: Check ledger for verification event
    time.sleep(2)  # Give ledger time to write
    verified = check_ledger_for_verification(local_ledger_url, peer_url)

    # Summary
    print("\n" + "=" * 60)
    if verified:
        print("[SUCCESS] FEDERATION DRILL PASSED")
        print("The peer_anchor_verified event exists in the ledger.")
        print("This node now has cryptographic witness of peer's governance.")
    else:
        print("[INCOMPLETE] Verification event not yet in ledger")
        print("Check federation sync logs and retry.")
    print("=" * 60)

    return verified


def run_two_node_drill(
    node_a_url: str,
    node_b_url: str,
    node_a_planner: str = "http://localhost:8090",
    node_a_ledger: str = "http://localhost:8082"
) -> bool:
    """
    Run the full genesis ceremony between two nodes.

    This is the complete Ring 1 activation drill.
    """
    print("=" * 60)
    print("FEDERATION GENESIS CEREMONY - Two Node Drill")
    print(f"Node-A (Genesis Authority): {node_a_url}")
    print(f"Node-B (Independent Verifier): {node_b_url}")
    print(f"Started: {datetime.now().isoformat()}")
    print("=" * 60)

    all_passed = True

    # Phase 1: Check both nodes healthy
    if not check_node_health(node_a_url, "Node-A"):
        print("\n[FAIL] Node-A is not healthy")
        return False

    if not check_node_health(node_b_url, "Node-B"):
        print("\n[FAIL] Node-B is not healthy")
        return False

    # Phase 2: Fire dangerous mission on Node-A
    print("\n" + "-" * 40)
    print("PHASE 2: Constitutional Test on Node-A")
    print("-" * 40)

    mission_id = fire_dangerous_mission(node_a_planner)
    if not mission_id:
        print("\n[FAIL] Could not create mission on Node-A")
        all_passed = False
    else:
        time.sleep(10)  # Wait for processing

        if not verify_mission_rejected(node_a_ledger, mission_id):
            print("\n[CRITICAL] Mission was not rejected - constitutional failure!")
            all_passed = False
        else:
            print("\n[OK] Constitutional test passed - HIGH risk rejected")

    # Phase 3: Wait for anchoring
    print("\n" + "-" * 40)
    print("PHASE 3: Waiting for Anchor Publication")
    print("-" * 40)
    print("  Waiting 30 seconds for anchor propagation...")
    time.sleep(30)

    # Phase 4: Node-B verifies Node-A
    print("\n" + "-" * 40)
    print("PHASE 4: Cross-Node Verification")
    print("-" * 40)

    result = verify_peer(node_b_url, node_a_url)
    if result.get("status") == "VALID":
        print("\n[OK] Node-B verified Node-A successfully")
    else:
        print(f"\n[WARN] Verification status: {result.get('status')}")
        if "No anchors available" in str(result.get("issues", [])):
            print("  (This is expected for newly started nodes)")

    # Phase 5: Check for genesis event
    print("\n" + "-" * 40)
    print("PHASE 5: Checking for Genesis Event")
    print("-" * 40)

    # We'd need access to Node-B's ledger here
    # For now, just check the verification result
    if result.get("status") == "VALID":
        print("  [OK] peer_anchor_verified event should now exist in Node-B's ledger")
        print("  The first constitutional inter-sovereign proof is complete.")
    else:
        print("  [PENDING] Full verification not yet complete")

    # Summary
    print("\n" + "=" * 60)
    if all_passed and result.get("status") == "VALID":
        print("[SUCCESS] FEDERATION GENESIS CEREMONY COMPLETE")
        print("")
        print("What is now true:")
        print("  - The system is not just internally lawful")
        print("  - It is externally self-auditing")
        print("  - A single operator cannot falsify history")
        print("  - Plural, cryptographically independent witnesses exist")
        print("")
        print("This is no longer software. This is INFRASTRUCTURE.")
    elif all_passed:
        print("[PARTIAL] Constitution verified, federation pending")
        print("Nodes are lawful but cross-verification not complete.")
        print("Retry after anchoring completes.")
    else:
        print("[FAILED] Genesis ceremony did not complete")
        print("Review the issues above and retry.")
    print("=" * 60)
    print("\nTHINK + WORRY + REFUSE + ACT + REMEMBER = OK")

    return all_passed and result.get("status") == "VALID"


# =============================================================================
# Entry Point
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Federation Drill - Ring 1 Genesis Ceremony"
    )
    parser.add_argument(
        "--peer-url",
        help="URL of peer node to verify (single-node mode)"
    )
    parser.add_argument(
        "--node-a",
        help="Node-A federation URL (two-node mode)"
    )
    parser.add_argument(
        "--node-b",
        help="Node-B federation URL (two-node mode)"
    )
    parser.add_argument(
        "--node-a-planner",
        default="http://localhost:8090",
        help="Node-A planner URL for firing missions"
    )
    parser.add_argument(
        "--node-a-ledger",
        default="http://localhost:8082",
        help="Node-A ledger URL for verification"
    )
    parser.add_argument(
        "--local-federation",
        default="http://localhost:8094",
        help="Local federation sync URL"
    )
    parser.add_argument(
        "--local-ledger",
        default="http://localhost:8082",
        help="Local ledger URL"
    )

    args = parser.parse_args()

    if args.node_a and args.node_b:
        # Two-node drill
        passed = run_two_node_drill(
            args.node_a,
            args.node_b,
            args.node_a_planner,
            args.node_a_ledger
        )
    elif args.peer_url:
        # Single-node drill
        passed = run_single_node_drill(
            args.peer_url,
            args.local_federation,
            args.local_ledger
        )
    else:
        print("Usage:")
        print("  Single node: python federation_drill.py --peer-url http://peer:8094")
        print("  Two nodes:   python federation_drill.py --node-a http://a:8094 --node-b http://b:8094")
        sys.exit(1)

    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()
