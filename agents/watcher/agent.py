"""
Watcher Agent - Dispute-Clarity Mirror
Reconstructs mission timelines from the ledger without interpretation.
Provides a neutral, chronologically ordered narrative for dispute resolution.

The Watcher does NOT judge or decide. It reflects the system's own records
back to humans so they can argue about values and decisions, not facts.
"""

import os
import asyncio
import threading
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any

import httpx
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel

app = FastAPI(
    title="Watcher Agent",
    version="1.0.0",
    description="Dispute-clarity mirror - reconstructs mission timelines from immutable ledger"
)

# Configuration
AGENT_NAME = os.environ.get("AGENT_NAME", "watcher")
LEDGER_URL = os.environ.get("LEDGER_URL", "http://ledger_service:8082")
EVIDENCE_URL = os.environ.get("EVIDENCE_URL", "http://evidence_writer:8080")
ALERT_INTERVAL_SEC = int(os.environ.get("WATCHER_ALERT_INTERVAL_SEC", "300"))  # 5 minutes
HIGH_THRESHOLD = int(os.environ.get("WATCHER_HIGH_THRESHOLD", "3"))  # 3 HIGH in window

# Guardian Configuration - Self-Protecting Reflex
CONTROL_KILL_URL = os.environ.get("CONTROL_KILL_URL", "http://control_killswitch:8000/kill/label")
GUARDIAN_ENABLED = os.environ.get("GUARDIAN_ENABLED", "true").lower() == "true"
GUARDIAN_LABEL = os.environ.get("GUARDIAN_LABEL", "mission.killable=true")

# In-memory state for pattern analysis
last_analysis_time: Optional[datetime] = None
agent_scores: Dict[str, int] = {}
agent_awards: Dict[str, str] = {}
agent_flags: List[str] = []
guardian_activations: List[Dict[str, Any]] = []


class TimelineEvent(BaseModel):
    """A single event in the reconstructed timeline."""
    sequence: int
    timestamp: str
    event_type: str
    agent: Optional[str]
    action: Optional[str]
    target: Optional[str]
    outcome: Optional[str]
    details: Dict[str, Any]


class MissionTimeline(BaseModel):
    """Complete reconstructed timeline for a mission."""
    mission_id: str
    reconstructed_at: str
    event_count: int
    timeline: List[TimelineEvent]
    integrity_verified: bool
    narrative: str


class DisputeReport(BaseModel):
    """Neutral factual report for dispute resolution."""
    report_id: str
    generated_at: str
    mission_id: str
    scope: str
    timeline: MissionTimeline
    key_facts: List[str]
    disclaimer: str


# Ledger Integration
async def fetch_all_entries() -> List[dict]:
    """Fetch all ledger entries."""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{LEDGER_URL}/entries?limit=10000")
            if response.status_code == 200:
                data = response.json()
                return data.get("entries", [])
    except Exception as e:
        print(f"[{AGENT_NAME}] Failed to fetch ledger: {e}")
    return []


async def verify_ledger_integrity() -> bool:
    """Verify the ledger hash chain is intact."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{LEDGER_URL}/verify")
            if response.status_code == 200:
                return response.json().get("valid", False)
    except Exception as e:
        print(f"[{AGENT_NAME}] Ledger verification failed: {e}")
    return False


def filter_entries_by_mission(entries: List[dict], mission_id: str) -> List[dict]:
    """Filter ledger entries related to a specific mission."""
    related = []
    for entry in entries:
        # Check target field
        if entry.get("target") == mission_id:
            related.append(entry)
            continue
        # Check metadata
        metadata = entry.get("metadata", {})
        if metadata.get("mission_id") == mission_id:
            related.append(entry)
            continue
        # Check if task belongs to mission (via task_id pattern or metadata)
        if "task" in entry.get("event_type", "").lower():
            if metadata.get("mission_id") == mission_id:
                related.append(entry)
    return related


def build_timeline(entries: List[dict]) -> List[TimelineEvent]:
    """Build a chronological timeline from ledger entries."""
    # Sort by timestamp
    sorted_entries = sorted(entries, key=lambda e: e.get("timestamp", ""))

    timeline = []
    for i, entry in enumerate(sorted_entries):
        event = TimelineEvent(
            sequence=i + 1,
            timestamp=entry.get("timestamp", "unknown"),
            event_type=entry.get("event_type", "unknown"),
            agent=entry.get("agent"),
            action=entry.get("action"),
            target=entry.get("target"),
            outcome=entry.get("outcome"),
            details=entry.get("metadata", {})
        )
        timeline.append(event)

    return timeline


def generate_narrative(timeline: List[TimelineEvent], mission_id: str) -> str:
    """Generate a neutral, factual narrative from timeline events."""
    if not timeline:
        return f"No recorded events found for mission {mission_id}."

    lines = [
        f"## Mission Timeline: {mission_id}",
        f"**Total Events:** {len(timeline)}",
        f"**Time Span:** {timeline[0].timestamp} to {timeline[-1].timestamp}",
        "",
        "### Chronological Event Record",
        ""
    ]

    for event in timeline:
        # Format each event neutrally
        agent_str = f"[{event.agent}]" if event.agent else "[system]"
        action_str = event.action or event.event_type
        target_str = f"→ {event.target}" if event.target else ""
        outcome_str = f"({event.outcome})" if event.outcome else ""

        line = f"{event.sequence}. **{event.timestamp}** {agent_str} {action_str} {target_str} {outcome_str}"
        lines.append(line)

        # Add relevant details if present
        if event.details:
            if "risk_level" in str(event.details):
                assessment = event.details.get("assessment", {})
                if assessment:
                    lines.append(f"   - Risk Level: {assessment.get('risk_level', 'N/A')}")
                    lines.append(f"   - Rationale: {assessment.get('rationale', 'N/A')}")
            if "objective" in event.details:
                obj = event.details.get("objective", "")
                if obj:
                    lines.append(f"   - Objective: {obj[:100]}{'...' if len(obj) > 100 else ''}")
            if "task_count" in event.details:
                lines.append(f"   - Tasks Generated: {event.details.get('task_count')}")

    lines.extend([
        "",
        "---",
        "*This narrative is mechanically reconstructed from the immutable ledger.*",
        "*The Watcher does not interpret or judge; it only reflects recorded facts.*"
    ])

    return "\n".join(lines)


def extract_key_facts(timeline: List[TimelineEvent]) -> List[str]:
    """Extract key factual statements from the timeline."""
    facts = []

    for event in timeline:
        if event.event_type == "plan_created":
            facts.append(f"Plan created at {event.timestamp} by {event.agent or 'planner'}")
            if event.details.get("task_count"):
                facts.append(f"Plan contained {event.details['task_count']} tasks")

        elif event.event_type == "risk_assessment":
            assessment = event.details.get("assessment", {})
            level = assessment.get("risk_level", "UNKNOWN")
            facts.append(f"Risk assessed as {level} by {event.agent or 'confessor'} at {event.timestamp}")

        elif event.event_type == "plan_rejected":
            facts.append(f"Plan was REJECTED at {event.timestamp}")
            if event.details.get("reason"):
                facts.append(f"Rejection reason: {event.details['reason']}")

        elif event.event_type == "kill_switch":
            facts.append(f"Kill switch activated at {event.timestamp} by {event.agent or 'operator'}")

        elif event.event_type == "plan_execution_finished":
            status = event.details.get("status", "unknown")
            facts.append(f"Plan execution finished with status: {status}")

    return facts


# API Endpoints
@app.get("/health")
async def health():
    return {"status": "healthy", "service": "watcher", "role": "dispute-clarity-mirror"}


@app.get("/mission/{mission_id}/timeline", response_model=MissionTimeline)
async def get_mission_timeline(mission_id: str):
    """
    Reconstruct the complete timeline for a specific mission.
    Returns a chronological, neutral account of all recorded events.
    """
    # Verify ledger integrity first
    integrity_ok = await verify_ledger_integrity()

    # Fetch all entries
    all_entries = await fetch_all_entries()
    if not all_entries:
        raise HTTPException(status_code=404, detail="No ledger entries found")

    # Filter to mission
    mission_entries = filter_entries_by_mission(all_entries, mission_id)
    if not mission_entries:
        raise HTTPException(status_code=404, detail=f"No events found for mission {mission_id}")

    # Build timeline
    timeline = build_timeline(mission_entries)
    narrative = generate_narrative(timeline, mission_id)

    return MissionTimeline(
        mission_id=mission_id,
        reconstructed_at=datetime.utcnow().isoformat(),
        event_count=len(timeline),
        timeline=timeline,
        integrity_verified=integrity_ok,
        narrative=narrative
    )


@app.get("/mission/{mission_id}/report", response_model=DisputeReport)
async def generate_dispute_report(
    mission_id: str,
    scope: str = Query(default="full", description="Scope: full, planning, execution, risk")
):
    """
    Generate a formal dispute resolution report for a mission.
    This is a neutral factual document suitable for legal/regulatory review.
    """
    # Get timeline
    timeline_data = await get_mission_timeline(mission_id)

    # Filter by scope if needed
    timeline_events = timeline_data.timeline
    if scope == "planning":
        timeline_events = [e for e in timeline_events if "plan" in e.event_type.lower()]
    elif scope == "execution":
        timeline_events = [e for e in timeline_events if "task" in e.event_type.lower()]
    elif scope == "risk":
        timeline_events = [e for e in timeline_events if "risk" in e.event_type.lower() or "reject" in e.event_type.lower()]

    # Extract key facts
    key_facts = extract_key_facts(timeline_events)

    report_id = f"DR-{mission_id}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"

    return DisputeReport(
        report_id=report_id,
        generated_at=datetime.utcnow().isoformat(),
        mission_id=mission_id,
        scope=scope,
        timeline=timeline_data,
        key_facts=key_facts,
        disclaimer=(
            "DISCLAIMER: This report is mechanically generated from the immutable ledger. "
            "The Watcher agent does not interpret, judge, or render opinions. "
            "This document reflects only what was recorded by the system. "
            "Any disputes about the meaning or appropriateness of these events "
            "must be resolved by human judgment, not by this agent."
        )
    )


@app.get("/ledger/summary")
async def ledger_summary():
    """Get a high-level summary of the ledger state."""
    integrity_ok = await verify_ledger_integrity()
    all_entries = await fetch_all_entries()

    # Count by event type
    event_counts: Dict[str, int] = {}
    missions_seen = set()

    for entry in all_entries:
        event_type = entry.get("event_type", "unknown")
        event_counts[event_type] = event_counts.get(event_type, 0) + 1

        # Track missions
        target = entry.get("target", "")
        if target.startswith("M-"):
            missions_seen.add(target)
        metadata = entry.get("metadata", {})
        if metadata.get("mission_id", "").startswith("M-"):
            missions_seen.add(metadata["mission_id"])

    return {
        "total_entries": len(all_entries),
        "integrity_verified": integrity_ok,
        "event_type_counts": event_counts,
        "missions_tracked": len(missions_seen),
        "mission_ids": sorted(missions_seen)
    }


@app.get("/compare/{mission_id_1}/{mission_id_2}")
async def compare_missions(mission_id_1: str, mission_id_2: str):
    """
    Compare two missions side-by-side.
    Useful for understanding why similar objectives had different outcomes.
    """
    timeline_1 = await get_mission_timeline(mission_id_1)
    timeline_2 = await get_mission_timeline(mission_id_2)

    facts_1 = extract_key_facts(timeline_1.timeline)
    facts_2 = extract_key_facts(timeline_2.timeline)

    return {
        "comparison_generated_at": datetime.utcnow().isoformat(),
        "mission_1": {
            "mission_id": mission_id_1,
            "event_count": timeline_1.event_count,
            "key_facts": facts_1
        },
        "mission_2": {
            "mission_id": mission_id_2,
            "event_count": timeline_2.event_count,
            "key_facts": facts_2
        },
        "disclaimer": "This comparison is factual only. Interpretation is left to human judgment."
    }


# ============================================================================
# PATTERN ANALYSIS & ALERTING
# ============================================================================

async def emit_alert(event: dict) -> None:
    """Send an alert event to evidence writer."""
    event["event_type"] = event.get("event_type", "watcher_alert")
    event["agent"] = AGENT_NAME
    event["timestamp"] = datetime.utcnow().isoformat()
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            await client.post(f"{EVIDENCE_URL}/log", json=event)
            print(f"[{AGENT_NAME}] Alert emitted: {event.get('pattern', 'unknown')}")
    except Exception as e:
        print(f"[{AGENT_NAME}] Failed to emit alert: {e}")


async def guardian_autopause(reason: str, domain: str, count: int) -> Dict[str, Any]:
    """
    Guardian Self-Protecting Reflex
    ================================
    Automatically pause agents when repeated HIGH risk patterns are detected.

    This makes the system self-protecting while remaining:
    - Auditable (all actions logged)
    - Reversible (humans can restart agents)
    - Sovereign (humans can disable Guardian)

    Guardian can ONLY affect containers with the killable label.
    It cannot touch: ledger, watcher, planner core, kill-switch itself.
    """
    global guardian_activations

    if not GUARDIAN_ENABLED:
        print(f"[guardian] Auto-pause disabled. Would have paused for: {reason}")
        return {"status": "disabled", "reason": reason}

    payload = {
        "label": GUARDIAN_LABEL,
        "reason": reason,
        "domain": domain,
        "count": count,
        "triggered_by": AGENT_NAME,
        "timestamp": datetime.utcnow().isoformat()
    }

    result = {"status": "unknown", "killed": [], "error": None}

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(CONTROL_KILL_URL, json=payload)

            if response.status_code == 200:
                data = response.json()
                result["status"] = "paused"
                result["killed"] = data.get("killed", [])

                # Log guardian activation
                activation = {
                    "timestamp": datetime.utcnow().isoformat(),
                    "reason": reason,
                    "domain": domain,
                    "count": count,
                    "killed": result["killed"]
                }
                guardian_activations.append(activation)

                # Emit guardian event to evidence
                await emit_alert({
                    "event_type": "guardian_autopause",
                    "severity": "CRITICAL",
                    "pattern": "autopause_triggered",
                    "label": GUARDIAN_LABEL,
                    "domain": domain,
                    "count": count,
                    "reason": reason,
                    "containers_paused": len(result["killed"]),
                    "message": f"Guardian auto-paused {len(result['killed'])} agents due to {reason}"
                })

                print(f"[guardian] Auto-paused {len(result['killed'])} agents with label {GUARDIAN_LABEL}")
            else:
                result["error"] = f"Kill-switch returned {response.status_code}"
                print(f"[guardian] Failed to auto-pause: {result['error']}")

    except Exception as e:
        result["error"] = str(e)
        print(f"[guardian] FAILED to auto-pause agents: {e}")

        # Still log the attempt
        await emit_alert({
            "event_type": "guardian_autopause_failed",
            "severity": "ERROR",
            "pattern": "autopause_failed",
            "reason": reason,
            "error": str(e)
        })

    return result


async def analyze_patterns(entries: List[dict]) -> Dict[str, Any]:
    """
    Analyze ledger patterns and compute agent scores/flags.

    Detects:
    - Repeated HIGH risk in a domain
    - Frequent overrides by agent
    - Approval/rejection ratios
    """
    global agent_scores, agent_awards, agent_flags

    high_by_domain: Dict[str, int] = {}
    overrides_by_agent: Dict[str, int] = {}
    approved_by_agent: Dict[str, int] = {}
    rejected_by_agent: Dict[str, int] = {}

    for entry in entries:
        event_type = entry.get("event_type", "")
        agent = entry.get("agent", "unknown")
        metadata = entry.get("metadata", {})

        # Track risk assessments
        if event_type == "risk_assessment":
            assessment = metadata.get("assessment", {})
            risk_level = assessment.get("risk_level") or entry.get("outcome")
            domain = metadata.get("domain", "general")

            if risk_level == "HIGH":
                high_by_domain[domain] = high_by_domain.get(domain, 0) + 1

        # Track approvals/rejections
        if event_type == "plan_approved":
            approved_by_agent[agent] = approved_by_agent.get(agent, 0) + 1
            agent_scores[agent] = agent_scores.get(agent, 0) + 1

        if event_type == "plan_rejected":
            rejected_by_agent[agent] = rejected_by_agent.get(agent, 0) + 1

        # Track human overrides
        if event_type == "human_authorization":
            authorizer = metadata.get("authorizer", "unknown")
            if metadata.get("authorized"):
                overrides_by_agent[authorizer] = overrides_by_agent.get(authorizer, 0) + 1

    # Award logic
    awards: Dict[str, str] = {}
    for agent, count in approved_by_agent.items():
        if count >= 10:
            awards[agent] = "RELIABILITY_BADGE"
    agent_awards.update(awards)

    # Flag logic
    flags: List[str] = []
    for agent, count in overrides_by_agent.items():
        if count >= 3:
            flags.append(agent)
    agent_flags = flags

    # Emit alerts for domains with repeated HIGH and trigger Guardian
    alerts_emitted = 0
    guardian_triggered = 0
    for domain, count in high_by_domain.items():
        if count >= HIGH_THRESHOLD:
            await emit_alert({
                "event_type": "watcher_alert",
                "severity": "HIGH",
                "pattern": "repeated_high_risk",
                "domain": domain,
                "count": count,
                "message": f"{count} HIGH risk assessments in domain '{domain}' within window",
            })
            alerts_emitted += 1

            # Guardian Self-Protecting Reflex - auto-pause agents
            guardian_result = await guardian_autopause(
                reason="repeated_high_risk",
                domain=domain,
                count=count
            )
            if guardian_result.get("status") == "paused":
                guardian_triggered += 1

    # Emit summary
    await emit_alert({
        "event_type": "watcher_summary",
        "severity": "INFO",
        "pattern": "periodic_summary",
        "scores": agent_scores,
        "awards": awards,
        "flags": flags,
        "high_by_domain": high_by_domain,
        "total_approved": sum(approved_by_agent.values()),
        "total_rejected": sum(rejected_by_agent.values()),
    })

    return {
        "alerts_emitted": alerts_emitted,
        "guardian_triggered": guardian_triggered,
        "high_by_domain": high_by_domain,
        "scores": agent_scores,
        "awards": awards,
        "flags": flags,
    }


async def watcher_loop():
    """Background loop for periodic pattern analysis."""
    global last_analysis_time

    while True:
        try:
            entries = await fetch_all_entries()
            if entries:
                result = await analyze_patterns(entries)
                last_analysis_time = datetime.utcnow()
                print(f"[{AGENT_NAME}] Pattern analysis complete: {result['alerts_emitted']} alerts")
        except Exception as e:
            print(f"[{AGENT_NAME}] Error in watcher loop: {e}")

        await asyncio.sleep(ALERT_INTERVAL_SEC)


def start_background_watcher():
    """Start the watcher loop in background."""
    loop = asyncio.new_event_loop()

    def run_loop():
        asyncio.set_event_loop(loop)
        loop.run_until_complete(watcher_loop())

    thread = threading.Thread(target=run_loop, daemon=True)
    thread.start()
    print(f"[{AGENT_NAME}] Background pattern watcher started (interval: {ALERT_INTERVAL_SEC}s)")


# API Endpoint for manual pattern analysis
@app.post("/analyze")
async def trigger_analysis():
    """Manually trigger pattern analysis."""
    entries = await fetch_all_entries()
    if not entries:
        return {"status": "no_entries", "analysis": None}

    result = await analyze_patterns(entries)
    return {
        "status": "analyzed",
        "entry_count": len(entries),
        "analysis": result,
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/scores")
async def get_agent_scores():
    """Get current agent scores and awards."""
    return {
        "scores": agent_scores,
        "awards": agent_awards,
        "flags": agent_flags,
        "last_analysis": last_analysis_time.isoformat() if last_analysis_time else None
    }


@app.get("/guardian")
async def get_guardian_status():
    """Get Guardian self-protection status and activation history."""
    return {
        "enabled": GUARDIAN_ENABLED,
        "label": GUARDIAN_LABEL,
        "threshold": HIGH_THRESHOLD,
        "activations": guardian_activations[-10:],  # Last 10 activations
        "total_activations": len(guardian_activations),
        "control_url": CONTROL_KILL_URL
    }


@app.post("/guardian/test")
async def test_guardian():
    """
    Manually trigger Guardian auto-pause for testing.
    Use with caution - this WILL pause agents.
    """
    result = await guardian_autopause(
        reason="manual_test",
        domain="test",
        count=999
    )
    return {
        "status": result.get("status"),
        "killed": result.get("killed", []),
        "error": result.get("error"),
        "timestamp": datetime.utcnow().isoformat()
    }


@app.on_event("startup")
async def startup_event():
    """Log agent startup and start background watcher."""
    print(f"[{AGENT_NAME}] Starting up...")
    print(f"[{AGENT_NAME}] Watcher ready. Role: Dispute-Clarity Mirror")
    print(f"[{AGENT_NAME}] I do not judge. I only reflect what was recorded.")

    # Start background pattern watcher
    start_background_watcher()
