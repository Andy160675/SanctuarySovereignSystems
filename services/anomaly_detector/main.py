"""
Anomaly Detector Service - Proactive Pattern Recognition
=========================================================

Subscribes to the ledger's WebSocket event stream and identifies
anomalous patterns that may indicate systemic stress or threats.

Acts as the organism's "immune system" - detecting subtle issues
that may not trigger hard-coded Guardian rules.

v1.0.0 - Initial release
"""

import asyncio
import json
import os
import time
from collections import deque, defaultdict
from datetime import datetime, timezone
from typing import Dict, Any, List, Deque

import httpx
import websockets


# =============================================================================
# Configuration
# =============================================================================

LEDGER_WS_URL = os.getenv("LEDGER_WS_URL", "ws://ledger_service:8082/ws/events")
LEDGER_REST_URL = os.getenv("LEDGER_URL", "http://ledger_service:8082")

# Alert thresholds
ALERT_THRESHOLD_GUARDIAN = int(os.getenv("ALERT_THRESHOLD_GUARDIAN", "3"))
ALERT_THRESHOLD_FAILURES = int(os.getenv("ALERT_THRESHOLD_FAILURES", "5"))
ALERT_THRESHOLD_HIGH_RISK = int(os.getenv("ALERT_THRESHOLD_HIGH_RISK", "3"))
EVENT_WINDOW_SECONDS = int(os.getenv("EVENT_WINDOW_SECONDS", "300"))  # 5 minutes

# Reconnection settings
RECONNECT_DELAY_SECONDS = 5
MAX_RECONNECT_ATTEMPTS = 10


# =============================================================================
# State
# =============================================================================

event_window: Deque[Dict[str, Any]] = deque(maxlen=1000)
alert_cooldowns: Dict[str, float] = {}  # alert_type -> last_alert_timestamp
COOLDOWN_SECONDS = 60  # Don't repeat same alert within this window


# =============================================================================
# Alerting
# =============================================================================

def can_send_alert(alert_type: str) -> bool:
    """Check if we're past the cooldown period for this alert type."""
    last_alert = alert_cooldowns.get(alert_type, 0)
    return time.time() - last_alert > COOLDOWN_SECONDS


def log_alert_to_ledger(alert_type: str, details: Dict[str, Any]) -> None:
    """Log a high-priority anomaly alert to the ledger."""
    if not can_send_alert(alert_type):
        print(f"[Anomaly] Skipping duplicate alert: {alert_type} (cooldown)")
        return

    alert_cooldowns[alert_type] = time.time()

    print(f"[ALERT] {alert_type}: {json.dumps(details, default=str)}")

    ledger_event = {
        "event_type": "anomaly_detector_alert",
        "agent": "anomaly_detector",
        "action": "alert",
        "target": alert_type,
        "outcome": "ALERT",
        "metadata": {
            "alert_type": alert_type,
            "severity": "HIGH",
            "details": details,
            "detected_at": datetime.now(timezone.utc).isoformat()
        }
    }

    try:
        # Synchronous call - we're in an async context but this is fire-and-forget
        import urllib.request
        req = urllib.request.Request(
            f"{LEDGER_REST_URL}/append",
            data=json.dumps(ledger_event).encode('utf-8'),
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        with urllib.request.urlopen(req, timeout=5) as response:
            pass
    except Exception as e:
        print(f"[Anomaly] CRITICAL: Could not log alert to ledger: {e}")


# =============================================================================
# Pattern Analysis
# =============================================================================

def analyze_events() -> None:
    """Analyze the current event window for known anomalous patterns."""
    now = time.time()
    cutoff = now - EVENT_WINDOW_SECONDS

    # Filter to recent events
    recent_events = [e for e in event_window if e.get('_received_at', 0) > cutoff]

    if not recent_events:
        return

    # Pattern 1: High frequency of Guardian interventions
    guardian_events = [
        e for e in recent_events
        if e.get('event_type') in ['guardian_intervention', 'guardian_alert', 'agent_killed']
    ]
    if len(guardian_events) >= ALERT_THRESHOLD_GUARDIAN:
        log_alert_to_ledger("high_guardian_activity", {
            "count": len(guardian_events),
            "window_seconds": EVENT_WINDOW_SECONDS,
            "events": [
                {"event_type": e.get('event_type'), "target": e.get('target')}
                for e in guardian_events[-5:]  # Last 5
            ]
        })

    # Pattern 2: High frequency of mission failures
    failure_events = [
        e for e in recent_events
        if e.get('event_type') in ['mission_aborted', 'execution_failed', 'task_failed']
        or e.get('outcome') == 'FAILED'
    ]
    if len(failure_events) >= ALERT_THRESHOLD_FAILURES:
        log_alert_to_ledger("high_failure_rate", {
            "count": len(failure_events),
            "window_seconds": EVENT_WINDOW_SECONDS,
            "failure_types": list(set(e.get('event_type') for e in failure_events))
        })

    # Pattern 3: Multiple HIGH risk assessments
    high_risk_events = [
        e for e in recent_events
        if e.get('outcome') == 'HIGH'
        or e.get('event_type') == 'plan_rejected'
        or (e.get('metadata', {}).get('risk_level') == 'HIGH')
    ]
    if len(high_risk_events) >= ALERT_THRESHOLD_HIGH_RISK:
        log_alert_to_ledger("repeated_high_risk_attempts", {
            "count": len(high_risk_events),
            "window_seconds": EVENT_WINDOW_SECONDS,
            "targets": list(set(e.get('target') for e in high_risk_events if e.get('target')))
        })

    # Pattern 4: Unusual event chatter (>100 events in window)
    if len(recent_events) > 100:
        event_types = defaultdict(int)
        for e in recent_events:
            event_types[e.get('event_type', 'unknown')] += 1

        log_alert_to_ledger("high_event_chatter", {
            "total_events": len(recent_events),
            "window_seconds": EVENT_WINDOW_SECONDS,
            "breakdown": dict(event_types)
        })

    # Pattern 5: Amendment storm (multiple amendment proposals)
    amendment_events = [
        e for e in recent_events
        if e.get('event_type') in ['amendment_proposed', 'amendment_voting_started']
    ]
    if len(amendment_events) >= 3:
        log_alert_to_ledger("amendment_storm", {
            "count": len(amendment_events),
            "window_seconds": EVENT_WINDOW_SECONDS,
            "message": "Multiple amendment proposals in short window - possible manipulation attempt"
        })


# =============================================================================
# WebSocket Handler
# =============================================================================

async def process_event(event: Dict[str, Any]) -> None:
    """Process an incoming event from the ledger stream."""
    # Add receive timestamp
    event['_received_at'] = time.time()

    # Store in window
    event_window.append(event)

    # Run analysis
    analyze_events()


async def websocket_handler() -> None:
    """Connect to the ledger WebSocket and process events."""
    reconnect_attempts = 0

    while True:
        try:
            print(f"[Anomaly] Connecting to {LEDGER_WS_URL}...")

            async with websockets.connect(LEDGER_WS_URL) as ws:
                reconnect_attempts = 0
                print(f"[Anomaly] Connected to ledger event stream")

                while True:
                    try:
                        message = await ws.recv()
                        data = json.loads(message)

                        # Handle context message (initial batch)
                        if data.get('type') == 'context':
                            print(f"[Anomaly] Received context: {data.get('count', len(data.get('data', [])))} events")
                            for event in data.get('data', []):
                                await process_event(event)
                        elif data.get('type') == 'heartbeat':
                            # Ignore heartbeats
                            pass
                        else:
                            # Regular event
                            await process_event(data)

                    except websockets.exceptions.ConnectionClosed:
                        print("[Anomaly] WebSocket connection closed")
                        break

        except Exception as e:
            reconnect_attempts += 1
            wait_time = min(RECONNECT_DELAY_SECONDS * reconnect_attempts, 60)

            if reconnect_attempts <= MAX_RECONNECT_ATTEMPTS:
                print(f"[Anomaly] Connection failed ({e}). Reconnecting in {wait_time}s... (attempt {reconnect_attempts})")
                await asyncio.sleep(wait_time)
            else:
                print(f"[Anomaly] Max reconnection attempts reached. Waiting 60s before retry...")
                await asyncio.sleep(60)
                reconnect_attempts = 0


# =============================================================================
# Main
# =============================================================================

def main() -> None:
    """Entry point for the anomaly detector."""
    print("=" * 60)
    print("SOVEREIGN SYSTEM - ANOMALY DETECTOR")
    print("=" * 60)
    print(f"Ledger WebSocket: {LEDGER_WS_URL}")
    print(f"Event Window: {EVENT_WINDOW_SECONDS}s")
    print(f"Guardian Threshold: {ALERT_THRESHOLD_GUARDIAN}")
    print(f"Failure Threshold: {ALERT_THRESHOLD_FAILURES}")
    print(f"High Risk Threshold: {ALERT_THRESHOLD_HIGH_RISK}")
    print("=" * 60)

    asyncio.run(websocket_handler())


if __name__ == "__main__":
    main()
