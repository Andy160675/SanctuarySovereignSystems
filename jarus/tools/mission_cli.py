#!/usr/bin/env python3
"""
Mission Control CLI - Operator Interface
=========================================

Single command-line interface for operating the Sovereign AI System.
Provides mission management, monitoring, and control capabilities.

Usage:
    python mission_cli.py missions             # List all missions
    python mission_cli.py status <mission_id>  # Get mission status
    python mission_cli.py replay <mission_id>  # Replay mission timeline
    python mission_cli.py kill <mission_id>    # Kill mission agents
    python mission_cli.py pending              # List pending authorizations
    python mission_cli.py authorize <mission_id> <yes|no> --operator <name>
    python mission_cli.py fire <objective>     # Fire new mission
    python mission_cli.py health               # System health check
    python mission_cli.py scores               # Agent scores and awards
    python mission_cli.py alerts               # Recent alerts
"""

import argparse
import json
import os
import sys
from datetime import datetime
from typing import Optional

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False
    print("Warning: httpx not installed. Install with: pip install httpx")

# Service URLs (configurable via environment)
PLANNER_URL = os.environ.get("PLANNER_URL", "http://localhost:8090")
WATCHER_URL = os.environ.get("WATCHER_URL", "http://localhost:8093")
LEDGER_URL = os.environ.get("LEDGER_URL", "http://localhost:8082")
KILLSWITCH_URL = os.environ.get("KILLSWITCH_URL", "http://localhost:8000")

TIMEOUT = 30.0


def print_header(title: str):
    """Print a section header."""
    width = 60
    print("\n" + "=" * width)
    print(f" {title}")
    print("=" * width)


def print_table(headers: list, rows: list):
    """Print a simple table."""
    if not rows:
        print("  (no data)")
        return

    # Calculate column widths
    widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(str(cell)))

    # Print header
    header_line = " | ".join(h.ljust(widths[i]) for i, h in enumerate(headers))
    print(f"  {header_line}")
    print("  " + "-+-".join("-" * w for w in widths))

    # Print rows
    for row in rows:
        row_line = " | ".join(str(cell).ljust(widths[i]) for i, cell in enumerate(row))
        print(f"  {row_line}")


def api_get(url: str) -> Optional[dict]:
    """Make GET request to API."""
    if not HTTPX_AVAILABLE:
        print("Error: httpx required")
        return None
    try:
        with httpx.Client(timeout=TIMEOUT) as client:
            response = client.get(url)
            if response.status_code == 200:
                return response.json()
            print(f"Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Error: {e}")
    return None


def api_post(url: str, data: dict) -> Optional[dict]:
    """Make POST request to API."""
    if not HTTPX_AVAILABLE:
        print("Error: httpx required")
        return None
    try:
        with httpx.Client(timeout=TIMEOUT) as client:
            response = client.post(url, json=data)
            if response.status_code in (200, 201, 202):
                return response.json()
            print(f"Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Error: {e}")
    return None


# ============================================================================
# COMMANDS
# ============================================================================

def cmd_health():
    """Check system health."""
    print_header("SYSTEM HEALTH")

    services = [
        ("Planner", f"{PLANNER_URL}/health"),
        ("Watcher", f"{WATCHER_URL}/health"),
        ("Ledger", f"{LEDGER_URL}/health"),
        ("Kill-switch", f"{KILLSWITCH_URL}/health"),
    ]

    rows = []
    for name, url in services:
        try:
            result = api_get(url)
            if result:
                status = result.get("status", "unknown")
                rows.append([name, status, "OK"])
            else:
                rows.append([name, "unreachable", "FAIL"])
        except Exception:
            rows.append([name, "error", "FAIL"])

    print_table(["Service", "Status", "Health"], rows)


def cmd_missions():
    """List all missions."""
    print_header("MISSIONS")

    result = api_get(f"{PLANNER_URL}/plans")
    if not result:
        return

    plans = result.get("plans", [])
    if not plans:
        print("  No missions found")
        return

    rows = []
    for p in plans:
        rows.append([
            p.get("mission_id", "?"),
            p.get("status", "?"),
            p.get("tasks_completed", 0),
            p.get("tasks_total", 0),
            p.get("objective", "")[:40]
        ])

    print_table(["Mission ID", "Status", "Done", "Total", "Objective"], rows)


def cmd_status(mission_id: str):
    """Get mission status."""
    print_header(f"MISSION: {mission_id}")

    result = api_get(f"{PLANNER_URL}/plan/{mission_id}")
    if not result:
        print(f"  Mission {mission_id} not found")
        return

    print(f"  Objective: {result.get('objective', 'N/A')}")
    print(f"  Status:    {result.get('status', 'N/A')}")
    print(f"  Risk:      {result.get('risk_level', 'N/A')}")

    tasks = result.get("tasks", [])
    if tasks:
        print(f"\n  Tasks ({len(tasks)}):")
        for t in tasks:
            status_icon = {
                "completed": "[x]",
                "in_progress": "[>]",
                "pending": "[ ]",
                "failed": "[!]"
            }.get(t.get("status", ""), "[ ]")
            print(f"    {status_icon} {t.get('sequence', '?')}. {t.get('description', '')[:50]}")


def cmd_replay(mission_id: str):
    """Replay mission timeline from Watcher."""
    print_header(f"TIMELINE REPLAY: {mission_id}")

    result = api_get(f"{WATCHER_URL}/mission/{mission_id}/timeline")
    if not result:
        print(f"  No timeline found for {mission_id}")
        return

    print(f"  Integrity: {'VERIFIED' if result.get('integrity_verified') else 'NOT VERIFIED'}")
    print(f"  Events:    {result.get('event_count', 0)}")
    print(f"  Generated: {result.get('reconstructed_at', 'N/A')}")

    # Print narrative
    narrative = result.get("narrative", "")
    if narrative:
        print("\n" + "-" * 60)
        print(narrative)
        print("-" * 60)


def cmd_pending():
    """List missions pending human authorization."""
    print_header("PENDING AUTHORIZATIONS")

    result = api_get(f"{PLANNER_URL}/pending_auth")
    if not result:
        return

    pending = result.get("pending_authorizations", [])
    if not pending:
        print("  No missions pending authorization")
        return

    for p in pending:
        print(f"\n  Mission:   {p.get('mission_id')}")
        print(f"  Objective: {p.get('objective', 'N/A')[:60]}")
        print(f"  Tasks:     {p.get('task_count', 0)}")
        print(f"  Created:   {p.get('created_at', 'N/A')}")

        assessment = p.get("risk_assessment", {})
        if assessment:
            print(f"  Risk:      {assessment.get('risk_level', 'UNKNOWN')}")
            print(f"  Reason:    {assessment.get('reason', 'N/A')[:60]}")

    print(f"\n  Total pending: {result.get('count', 0)}")
    print("\n  To authorize: mission_cli.py authorize <mission_id> yes --operator <name>")
    print("  To deny:      mission_cli.py authorize <mission_id> no --operator <name>")


def cmd_authorize(mission_id: str, decision: str, operator: str, reason: str = None):
    """Authorize or deny a pending mission."""
    authorized = decision.lower() in ("yes", "y", "true", "1", "approve")

    print_header(f"{'AUTHORIZING' if authorized else 'DENYING'}: {mission_id}")

    data = {
        "mission_id": mission_id,
        "authorized": authorized,
        "authorizer": operator,
        "reason": reason or f"{'Approved' if authorized else 'Denied'} via CLI"
    }

    result = api_post(f"{PLANNER_URL}/human_auth", data)
    if result:
        print(f"  Status:     {result.get('status', 'unknown')}")
        print(f"  Authorizer: {result.get('authorizer', operator)}")
        print(f"  Message:    {result.get('message', 'N/A')}")
    else:
        print("  Authorization failed")


def cmd_fire(objective: str, jurisdiction: str = "UK"):
    """Fire a new mission."""
    print_header("FIRING NEW MISSION")

    data = {
        "objective": objective,
        "jurisdiction": jurisdiction
    }

    result = api_post(f"{PLANNER_URL}/plan", data)
    if result:
        print(f"  Mission ID: {result.get('mission_id', 'unknown')}")
        print(f"  Status:     {result.get('status', 'unknown')}")
        print(f"  Tasks:      {len(result.get('tasks', []))}")
        print(f"\n  Mission submitted. Check status with:")
        print(f"    mission_cli.py status {result.get('mission_id')}")
    else:
        print("  Failed to fire mission")


def cmd_kill(mission_id: str = None):
    """Kill agents via kill-switch."""
    print_header("KILL SWITCH")

    if mission_id:
        # Kill specific mission agents (by label)
        url = f"{KILLSWITCH_URL}/kill/mission/{mission_id}"
    else:
        # Kill all agents
        url = f"{KILLSWITCH_URL}/kill/agents"

    result = api_post(url, {})
    if result:
        print(f"  Status:  {result.get('status', 'unknown')}")
        print(f"  Stopped: {result.get('stopped_count', 0)} containers")
        if result.get("stopped"):
            for container in result.get("stopped", []):
                print(f"    - {container}")
    else:
        print("  Kill switch activation failed")


def cmd_scores():
    """Get agent scores and awards."""
    print_header("AGENT SCORES & AWARDS")

    result = api_get(f"{WATCHER_URL}/scores")
    if not result:
        return

    scores = result.get("scores", {})
    awards = result.get("awards", {})
    flags = result.get("flags", [])

    print("\n  Scores:")
    if scores:
        for agent, score in sorted(scores.items(), key=lambda x: -x[1]):
            print(f"    {agent}: {score}")
    else:
        print("    (no scores yet)")

    print("\n  Awards:")
    if awards:
        for agent, award in awards.items():
            print(f"    {agent}: {award}")
    else:
        print("    (no awards yet)")

    print("\n  Flags (needs review):")
    if flags:
        for agent in flags:
            print(f"    - {agent}")
    else:
        print("    (none)")

    last = result.get("last_analysis")
    if last:
        print(f"\n  Last analysis: {last}")


def cmd_alerts():
    """Trigger analysis and show recent alerts."""
    print_header("PATTERN ANALYSIS")

    result = api_post(f"{WATCHER_URL}/analyze", {})
    if not result:
        return

    analysis = result.get("analysis", {})

    print(f"  Entries analyzed: {result.get('entry_count', 0)}")
    print(f"  Alerts emitted:   {analysis.get('alerts_emitted', 0)}")

    high_domains = analysis.get("high_by_domain", {})
    if high_domains:
        print("\n  HIGH risk by domain:")
        for domain, count in high_domains.items():
            print(f"    {domain}: {count}")

    print(f"\n  Timestamp: {result.get('timestamp', 'N/A')}")


def cmd_summary():
    """Get ledger summary."""
    print_header("LEDGER SUMMARY")

    result = api_get(f"{WATCHER_URL}/ledger/summary")
    if not result:
        return

    print(f"  Total entries:    {result.get('total_entries', 0)}")
    print(f"  Integrity:        {'VERIFIED' if result.get('integrity_verified') else 'NOT VERIFIED'}")
    print(f"  Missions tracked: {result.get('missions_tracked', 0)}")

    event_counts = result.get("event_type_counts", {})
    if event_counts:
        print("\n  Event counts:")
        for event_type, count in sorted(event_counts.items()):
            print(f"    {event_type}: {count}")


# ============================================================================
# MAIN
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Mission Control CLI - Sovereign AI System Operator Interface",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Commands:
  health              Check system health
  missions            List all missions
  status <id>         Get mission status
  replay <id>         Replay mission timeline
  pending             List pending authorizations
  authorize <id>      Authorize/deny pending mission
  fire <objective>    Fire new mission
  kill [id]           Kill agents (all or by mission)
  scores              Agent scores and awards
  alerts              Trigger pattern analysis
  summary             Ledger summary

Examples:
  %(prog)s health
  %(prog)s fire "Review lease compliance for property"
  %(prog)s pending
  %(prog)s authorize M-20251202 yes --operator "John Smith"
  %(prog)s replay M-20251202
  %(prog)s kill
"""
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # health
    subparsers.add_parser("health", help="Check system health")

    # missions
    subparsers.add_parser("missions", help="List all missions")

    # status
    p = subparsers.add_parser("status", help="Get mission status")
    p.add_argument("mission_id", help="Mission ID")

    # replay
    p = subparsers.add_parser("replay", help="Replay mission timeline")
    p.add_argument("mission_id", help="Mission ID")

    # pending
    subparsers.add_parser("pending", help="List pending authorizations")

    # authorize
    p = subparsers.add_parser("authorize", help="Authorize/deny pending mission")
    p.add_argument("mission_id", help="Mission ID")
    p.add_argument("decision", choices=["yes", "no", "y", "n"], help="Authorization decision")
    p.add_argument("--operator", "-o", required=True, help="Operator name")
    p.add_argument("--reason", "-r", help="Reason for decision")

    # fire
    p = subparsers.add_parser("fire", help="Fire new mission")
    p.add_argument("objective", help="Mission objective")
    p.add_argument("--jurisdiction", "-j", default="UK", help="Jurisdiction")

    # kill
    p = subparsers.add_parser("kill", help="Kill agents")
    p.add_argument("mission_id", nargs="?", help="Mission ID (optional, kills all if omitted)")

    # scores
    subparsers.add_parser("scores", help="Agent scores and awards")

    # alerts
    subparsers.add_parser("alerts", help="Trigger pattern analysis")

    # summary
    subparsers.add_parser("summary", help="Ledger summary")

    args = parser.parse_args()

    if not HTTPX_AVAILABLE:
        print("Error: httpx library required. Install with: pip install httpx")
        sys.exit(1)

    if not args.command:
        parser.print_help()
        sys.exit(0)

    # Dispatch commands
    if args.command == "health":
        cmd_health()
    elif args.command == "missions":
        cmd_missions()
    elif args.command == "status":
        cmd_status(args.mission_id)
    elif args.command == "replay":
        cmd_replay(args.mission_id)
    elif args.command == "pending":
        cmd_pending()
    elif args.command == "authorize":
        cmd_authorize(args.mission_id, args.decision, args.operator, args.reason)
    elif args.command == "fire":
        cmd_fire(args.objective, args.jurisdiction)
    elif args.command == "kill":
        cmd_kill(args.mission_id)
    elif args.command == "scores":
        cmd_scores()
    elif args.command == "alerts":
        cmd_alerts()
    elif args.command == "summary":
        cmd_summary()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
