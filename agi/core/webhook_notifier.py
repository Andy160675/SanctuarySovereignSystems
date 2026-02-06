from __future__ import annotations
"""Webhook notifier for HIGH/CRITICAL events (Phase 5 governance gap #3)."""
import os, json, urllib.request

WEBHOOK_URL = os.environ.get("SOVEREIGN_ALERT_WEBHOOK")  # e.g. Slack/Teams/Telegram

def send_alert(level: str, title: str, details: dict):
    if not WEBHOOK_URL:
        return False
    payload = {
        "level": level,
        "title": title,
        "details": details,
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(WEBHOOK_URL, data=data, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            return resp.status == 200
    except Exception:
        return False

__all__ = ["send_alert"]
