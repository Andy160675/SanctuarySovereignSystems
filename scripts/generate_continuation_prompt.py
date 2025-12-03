#!/usr/bin/env python3
"""
Conversation Continuation Prompt Generator
==========================================

Generates a structured prompt to continue halted AI conversations.
Captures system state, pending tasks, and context for seamless handoff.

Usage:
    python scripts/generate_continuation_prompt.py
    python scripts/generate_continuation_prompt.py --output continuation.md
    python scripts/generate_continuation_prompt.py --check-services
"""

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

# Try to import httpx for service checks
try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False


# =============================================================================
# Configuration
# =============================================================================

REPO_ROOT = Path(__file__).parent.parent
COMPOSE_FILE = REPO_ROOT / "compose" / "docker-compose.mission.yml"

# Service endpoints (when running)
SERVICES = {
    "ledger": "http://localhost:8082",
    "planner": "http://localhost:8090",
    "advocate": "http://localhost:8091",
    "confessor": "http://localhost:8092",
    "watcher": "http://localhost:8093",
    "policy_gate": "http://localhost:8181",
    "filesystem_proxy": "http://localhost:8080",
    "evidence_writer": "http://localhost:8083",
    "killswitch": "http://localhost:8000",
}

# Key files to summarize
KEY_FILES = [
    "compose/docker-compose.mission.yml",
    "agents/planner/agent.py",
    "agents/advocate/agent.py",
    "agents/confessor/agent.py",
    "agents/watcher/agent.py",
    "docs/governance/Mission_Execution_Charter.md",
    "docs/governance/Mission_Execution_Charter_Risk_Addendum.md",
    ".github/workflows/reasoning-drill.yml",
]


# =============================================================================
# Service Status Checks
# =============================================================================

def check_service_health(name: str, url: str) -> Dict[str, Any]:
    """Check if a service is healthy."""
    if not HTTPX_AVAILABLE:
        return {"name": name, "status": "unknown", "note": "httpx not installed"}

    try:
        with httpx.Client(timeout=3.0) as client:
            resp = client.get(f"{url}/health")
            if resp.status_code == 200:
                return {"name": name, "status": "healthy", "data": resp.json()}
            return {"name": name, "status": "unhealthy", "code": resp.status_code}
    except httpx.ConnectError:
        return {"name": name, "status": "offline"}
    except Exception as e:
        return {"name": name, "status": "error", "error": str(e)}


def get_all_service_status() -> List[Dict[str, Any]]:
    """Get status of all services."""
    return [check_service_health(name, url) for name, url in SERVICES.items()]


def get_ledger_summary() -> Optional[Dict[str, Any]]:
    """Get recent ledger entries for context."""
    if not HTTPX_AVAILABLE:
        return None

    try:
        with httpx.Client(timeout=5.0) as client:
            resp = client.get(f"{SERVICES['ledger']}/entries?limit=20")
            if resp.status_code == 200:
                data = resp.json()
                entries = data.get("entries", data) if isinstance(data, dict) else data

                # Summarize by event type
                by_type = {}
                for e in entries:
                    et = e.get("event_type", "unknown")
                    by_type[et] = by_type.get(et, 0) + 1

                return {
                    "total_recent": len(entries),
                    "by_event_type": by_type,
                    "latest": entries[0] if entries else None
                }
    except Exception:
        pass
    return None


def get_pending_missions() -> Optional[List[Dict[str, Any]]]:
    """Get missions awaiting human authorization."""
    if not HTTPX_AVAILABLE:
        return None

    try:
        with httpx.Client(timeout=5.0) as client:
            resp = client.get(f"{SERVICES['planner']}/pending_auth")
            if resp.status_code == 200:
                return resp.json().get("pending_missions", [])
    except Exception:
        pass
    return None


# =============================================================================
# File Analysis
# =============================================================================

def get_file_summary(filepath: str) -> Dict[str, Any]:
    """Get summary info about a key file."""
    full_path = REPO_ROOT / filepath
    if not full_path.exists():
        return {"path": filepath, "exists": False}

    stat = full_path.stat()
    lines = 0
    try:
        with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = sum(1 for _ in f)
    except Exception:
        pass

    return {
        "path": filepath,
        "exists": True,
        "size_bytes": stat.st_size,
        "lines": lines,
        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
    }


def get_git_status() -> Dict[str, Any]:
    """Get current git status."""
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True
        )
        modified = [l.strip() for l in result.stdout.strip().split('\n') if l.strip()]

        # Get current branch
        branch_result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True
        )
        branch = branch_result.stdout.strip()

        # Get last commit
        commit_result = subprocess.run(
            ["git", "log", "-1", "--format=%h %s"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True
        )
        last_commit = commit_result.stdout.strip()

        return {
            "branch": branch,
            "last_commit": last_commit,
            "modified_files": modified[:10],  # Limit to 10
            "modified_count": len(modified)
        }
    except Exception as e:
        return {"error": str(e)}


# =============================================================================
# Prompt Generation
# =============================================================================

def generate_continuation_prompt(include_services: bool = True) -> str:
    """Generate a structured continuation prompt."""

    timestamp = datetime.now().isoformat()

    # Gather context
    git_status = get_git_status()
    file_summaries = [get_file_summary(f) for f in KEY_FILES]

    service_status = []
    ledger_summary = None
    pending_missions = None

    if include_services:
        service_status = get_all_service_status()
        ledger_summary = get_ledger_summary()
        pending_missions = get_pending_missions()

    # Build prompt
    prompt = f"""# Conversation Continuation Prompt
Generated: {timestamp}

## System: Sovereign AI Governance Runtime

This is a continuation of work on the "Sovereign System" - an autonomous AI governance runtime with charter-aligned agents.

## Architecture Summary

### Core Agents (Trinity + Guardian)
- **Planner**: Mission decomposition, risk-gated execution, calls Confessor before any plan approval
- **Confessor**: Risk assessment (LOW/MEDIUM/HIGH/UNKNOWN), writes to ledger
- **Watcher**: Dispute-clarity mirror, pattern detection, timeline reconstruction
- **Advocate**: Task executor with real tool calls (filesystem, API, database proxies)
- **Guardian**: Self-protection reflex, kills agents on repeated HIGH risk patterns

### Risk Gating Rules
- HIGH → REJECTED (mandatory block, no execution)
- UNKNOWN → PENDING_HUMAN_AUTH (requires human approval)
- LOW/MEDIUM → APPROVED (proceed with execution)
- Timeout → PENDING_HUMAN_AUTH (fail-safe)

### Key Services
- policy_gate (OPA): Policy enforcement at :8181
- ledger_service: Immutable audit trail at :8082
- evidence_writer: Structured evidence collection at :8083
- control_killswitch: Emergency agent termination at :8000
- filesystem_proxy, api_gateway_proxy, db_proxy: Governed tool access

## Current State
"""

    # Git status
    prompt += f"""
### Git Status
- Branch: {git_status.get('branch', 'unknown')}
- Last commit: {git_status.get('last_commit', 'unknown')}
- Modified files: {git_status.get('modified_count', 0)}
"""
    if git_status.get('modified_files'):
        prompt += "- Changes:\n"
        for f in git_status.get('modified_files', []):
            prompt += f"  - {f}\n"

    # Service status
    if service_status:
        prompt += "\n### Service Status\n"
        online = [s for s in service_status if s.get('status') == 'healthy']
        offline = [s for s in service_status if s.get('status') != 'healthy']

        if online:
            prompt += f"- Online ({len(online)}): {', '.join(s['name'] for s in online)}\n"
        if offline:
            prompt += f"- Offline/Unknown ({len(offline)}): {', '.join(s['name'] for s in offline)}\n"

    # Ledger summary
    if ledger_summary:
        prompt += f"""
### Ledger Summary (last 20 entries)
- Total: {ledger_summary.get('total_recent', 0)}
- By type: {json.dumps(ledger_summary.get('by_event_type', {}), indent=2)}
"""

    # Pending missions
    if pending_missions:
        prompt += f"""
### Pending Human Authorization
{len(pending_missions)} mission(s) awaiting approval:
"""
        for m in pending_missions[:5]:
            prompt += f"- {m.get('mission_id', 'unknown')}: {m.get('objective', 'no objective')[:60]}...\n"

    # Key files
    prompt += "\n### Key Files\n"
    for fs in file_summaries:
        if fs.get('exists'):
            prompt += f"- {fs['path']}: {fs['lines']} lines, modified {fs['modified'][:10]}\n"
        else:
            prompt += f"- {fs['path']}: MISSING\n"

    # Implementation status
    prompt += """
## Implementation Status

### Completed
- [x] Risk gating in Planner (HIGH→block, UNKNOWN→human, LOW/MEDIUM→approve)
- [x] Confessor LLM-based risk assessment with ledger logging
- [x] Watcher with Guardian auto-pause on repeated HIGH patterns
- [x] Advocate tool execution (filesystem, API gateway, database proxies)
- [x] CI workflow for risk gating verification
- [x] Kill-switch with label-based container termination

### In Progress / Remaining
- [ ] Human authorization dashboard (approve/reject PENDING_HUMAN_AUTH missions)
- [ ] Byzantine attack defense (HMAC signature verification)
- [ ] Artifact storage service for mission outputs
- [ ] Full integration test with all proxies

## Continuation Instructions

To continue this work:

1. **If services are offline**: Start the mission stack
   ```bash
   cd /c/sovereign-system
   docker compose -f compose/docker-compose.mission.yml up -d --build
   ```

2. **To verify risk gating**: Run the drill
   ```bash
   pytest tests/planner/test_risk_gating.py -v
   ```

3. **To test a mission**: Send to planner
   ```bash
   curl -X POST http://localhost:8090/plan \\
     -H "Content-Type: application/json" \\
     -d '{"objective":"Review lease compliance for standard tenancy."}'
   ```

4. **To check ledger**: Query entries
   ```bash
   curl http://localhost:8082/entries?limit=10 | jq .
   ```

## Context for AI Assistant

You are continuing work on this Sovereign AI Governance system. The user's primary goals are:
1. Complete the "trinity" architecture (Planner/Confessor/Watcher) with Guardian self-protection
2. Ensure all risk gating rules are mechanically enforced
3. Move toward self-build capability (make mission-up, make mission-drill)
4. Maintain EU AI Act Article 14 compliance (human oversight for HIGH/UNKNOWN risk)

Key governance documents are in `docs/governance/`. All agent decisions must be logged to the ledger.

Please review the current state and continue with the next priority task.
"""

    return prompt


# =============================================================================
# Main
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description="Generate continuation prompt for halted conversations")
    parser.add_argument("--output", "-o", help="Output file path (default: stdout)")
    parser.add_argument("--check-services", action="store_true", help="Include live service status checks")
    parser.add_argument("--json", action="store_true", help="Output as JSON instead of markdown")
    args = parser.parse_args()

    prompt = generate_continuation_prompt(include_services=args.check_services)

    if args.json:
        output = json.dumps({
            "generated_at": datetime.now().isoformat(),
            "prompt": prompt,
            "git_status": get_git_status(),
            "services": get_all_service_status() if args.check_services else []
        }, indent=2)
    else:
        output = prompt

    if args.output:
        Path(args.output).write_text(output)
        print(f"Continuation prompt written to: {args.output}")
    else:
        print(output)


if __name__ == "__main__":
    main()
