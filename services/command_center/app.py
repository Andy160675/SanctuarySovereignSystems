"""
Command Center Dashboard - Real-Time Event Stream UI
====================================================

Provides a web-based dashboard for real-time monitoring of the
Sovereign System's ledger events via WebSocket streaming.

v2.0.0 - Added system health aggregation and NL proposal interface
"""

import os
from pathlib import Path

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

app = FastAPI(title="Command Center", version="2.0.0")

# Runtime interface for system health and NL proposals
RUNTIME_INTERFACE_URL = os.getenv("RUNTIME_INTERFACE_URL", "http://runtime-interface:8096")

LEDGER_WS_HOST = os.getenv("LEDGER_WS_HOST", "localhost")
LEDGER_WS_PORT = os.getenv("LEDGER_WS_PORT", "8082")


# =============================================================================
# API Proxy Routes - Forward to Runtime Interface
# =============================================================================

class NLProposalRequest(BaseModel):
    proposal: str


@app.get("/api/system/health")
async def proxy_system_health():
    """Proxy system health request to runtime-interface."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{RUNTIME_INTERFACE_URL}/system/health")
            return response.json()
    except Exception as e:
        return {"overall": "unhealthy", "services": [], "error": str(e)}


@app.post("/api/propose_nl")
async def proxy_propose_nl(request: NLProposalRequest):
    """Proxy NL proposal to runtime-interface."""
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{RUNTIME_INTERFACE_URL}/propose_nl",
                json={"proposal": request.proposal}
            )
            if response.status_code == 200:
                return response.json()
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=response.text
                )
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Request timed out")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "command_center"}


@app.get("/config")
async def get_config():
    """Return configuration for the frontend."""
    return {
        "ledger_ws_url": f"ws://{LEDGER_WS_HOST}:{LEDGER_WS_PORT}/ws/events",
        "runtime_interface_url": RUNTIME_INTERFACE_URL
    }


@app.get("/", response_class=HTMLResponse)
async def dashboard():
    """Serve the main dashboard HTML."""
    return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sovereign System - Command Center</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Courier New', monospace;
            background: #0a0a0f;
            color: #00ff00;
            min-height: 100vh;
        }
        .header {
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            padding: 20px;
            border-bottom: 2px solid #00ff00;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .header h1 { font-size: 1.5em; text-shadow: 0 0 10px #00ff00; }
        .status-bar { display: flex; gap: 20px; align-items: center; }
        .status-indicator { display: flex; align-items: center; gap: 8px; }
        .status-dot {
            width: 12px; height: 12px; border-radius: 50%;
            animation: pulse 2s infinite;
        }
        .status-dot.connected { background: #00ff00; box-shadow: 0 0 10px #00ff00; }
        .status-dot.disconnected { background: #ff4444; box-shadow: 0 0 10px #ff4444; }
        .status-dot.unknown { background: #ffaa00; box-shadow: 0 0 10px #ffaa00; }
        @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }
        .container {
            display: grid;
            grid-template-columns: 300px 1fr;
            height: calc(100vh - 80px);
        }
        .sidebar {
            background: #111;
            border-right: 1px solid #333;
            padding: 15px;
            overflow-y: auto;
        }
        .sidebar h2 { font-size: 1em; margin-bottom: 15px; color: #00aaff; }
        .overall-status {
            padding: 10px;
            margin-bottom: 15px;
            border-radius: 4px;
            font-weight: bold;
            text-align: center;
        }
        .overall-status.healthy { background: #0a3010; color: #00ff00; }
        .overall-status.degraded { background: #3a3000; color: #ffaa00; }
        .overall-status.unhealthy { background: #3a0a0a; color: #ff4444; }
        .service-list { list-style: none; }
        .service-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 10px;
            margin-bottom: 5px;
            background: #1a1a1a;
            border-radius: 4px;
            border-left: 3px solid #333;
            cursor: pointer;
        }
        .service-item:hover { background: #252525; }
        .service-item.healthy { border-left-color: #00ff00; }
        .service-item.unhealthy { border-left-color: #ff4444; }
        .service-item.unknown { border-left-color: #ffaa00; }
        .main-panel { padding: 20px; overflow-y: auto; }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 15px;
            margin-bottom: 20px;
        }
        .stat-card {
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            padding: 15px;
            border-radius: 8px;
            border: 1px solid #333;
        }
        .stat-card h3 { font-size: 0.8em; color: #888; margin-bottom: 5px; }
        .stat-card .value { font-size: 1.8em; color: #00ff00; }
        .proposal-panel {
            background: #111;
            border: 1px solid #333;
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 20px;
        }
        .proposal-panel h3 { color: #00aaff; margin-bottom: 10px; }
        .proposal-input {
            width: 100%;
            padding: 12px;
            background: #1a1a1a;
            border: 1px solid #333;
            border-radius: 4px;
            color: #00ff00;
            font-family: inherit;
            font-size: 0.9em;
            resize: vertical;
        }
        .proposal-input:focus { outline: none; border-color: #00aaff; }
        .btn {
            padding: 10px 20px;
            background: #00aaff;
            color: #000;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-family: inherit;
            font-weight: bold;
            margin-top: 10px;
        }
        .btn:hover { background: #0088cc; }
        .btn:disabled { background: #333; color: #666; cursor: not-allowed; }
        .proposal-status {
            margin-top: 10px;
            padding: 10px;
            border-radius: 4px;
            display: none;
        }
        .proposal-status.success { display: block; background: #0a3010; color: #00ff00; }
        .proposal-status.error { display: block; background: #3a0a0a; color: #ff4444; }
        .event-stream {
            background: #111;
            border: 1px solid #333;
            border-radius: 8px;
            overflow: hidden;
        }
        .event-stream-header {
            background: #1a1a2e;
            padding: 10px 15px;
            border-bottom: 1px solid #333;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .event-list { max-height: 400px; overflow-y: auto; padding: 10px; }
        .event-item {
            background: #1a1a1a;
            margin-bottom: 8px;
            padding: 12px;
            border-radius: 4px;
            border-left: 3px solid #00aaff;
            font-size: 0.85em;
        }
        .event-item.alert { border-left-color: #ff4444; background: #2a1a1a; }
        .event-item.approved { border-left-color: #00ff00; }
        .event-item.rejected { border-left-color: #ff4444; }
        .event-item.risk_high { border-left-color: #ff0000; }
        .event-header { display: flex; justify-content: space-between; margin-bottom: 8px; }
        .event-type { color: #00aaff; font-weight: bold; }
        .event-time { color: #666; font-size: 0.9em; }
        .event-details {
            background: #0a0a0f;
            padding: 8px;
            border-radius: 4px;
            font-size: 0.85em;
            white-space: pre-wrap;
            overflow-x: auto;
            color: #aaa;
        }
        .alert-banner {
            display: none;
            background: linear-gradient(90deg, #ff4444, #cc0000);
            color: white;
            padding: 15px 20px;
            text-align: center;
            font-weight: bold;
            animation: flash 1s infinite;
        }
        @keyframes flash { 0%, 100% { opacity: 1; } 50% { opacity: 0.7; } }
        .alert-banner.active { display: block; }
    </style>
</head>
<body>
    <div id="alert-banner" class="alert-banner">ANOMALY DETECTED - CHECK EVENT STREAM</div>

    <div class="header">
        <h1>[SOVEREIGN SYSTEM] COMMAND CENTER v2.0</h1>
        <div class="status-bar">
            <div class="status-indicator">
                <span id="ws-status" class="status-dot disconnected"></span>
                <span id="ws-status-text">Disconnected</span>
            </div>
        </div>
    </div>

    <div class="container">
        <div class="sidebar">
            <h2>SYSTEM HEALTH</h2>
            <div id="overall-status" class="overall-status unknown">Loading...</div>
            <ul id="service-list" class="service-list"></ul>
        </div>

        <div class="main-panel">
            <div class="stats-grid">
                <div class="stat-card">
                    <h3>TOTAL EVENTS</h3>
                    <div id="stat-total" class="value">0</div>
                </div>
                <div class="stat-card">
                    <h3>APPROVED</h3>
                    <div id="stat-approved" class="value">0</div>
                </div>
                <div class="stat-card">
                    <h3>REJECTED</h3>
                    <div id="stat-rejected" class="value">0</div>
                </div>
                <div class="stat-card">
                    <h3>ALERTS</h3>
                    <div id="stat-alerts" class="value">0</div>
                </div>
            </div>

            <div class="proposal-panel">
                <h3>SUBMIT PROPOSAL (Natural Language)</h3>
                <textarea id="nl-proposal" class="proposal-input" rows="3"
                    placeholder="Enter your mission in plain English, e.g., 'Review the lease agreement for compliance issues'"></textarea>
                <button id="submit-btn" class="btn">Submit Proposal</button>
                <div id="proposal-status" class="proposal-status"></div>
            </div>

            <div class="event-stream">
                <div class="event-stream-header">
                    <span>LIVE EVENT STREAM</span>
                    <button onclick="clearEvents()" class="btn" style="padding:5px 10px;">Clear</button>
                </div>
                <div id="event-list" class="event-list">
                    <div class="event-item">
                        <div class="event-header">
                            <span class="event-type">Waiting for connection...</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        let ws;
        let stats = { total: 0, approved: 0, rejected: 0, alerts: 0 };
        const eventList = document.getElementById('event-list');
        const wsStatus = document.getElementById('ws-status');
        const wsStatusText = document.getElementById('ws-status-text');
        const alertBanner = document.getElementById('alert-banner');
        const overallStatus = document.getElementById('overall-status');
        const serviceList = document.getElementById('service-list');
        const nlProposal = document.getElementById('nl-proposal');
        const submitBtn = document.getElementById('submit-btn');
        const proposalStatus = document.getElementById('proposal-status');

        // System Health Polling (via runtime_interface)
        async function pollSystemHealth() {
            try {
                const resp = await fetch('/api/system/health');
                if (!resp.ok) throw new Error('Health check failed');
                const data = await resp.json();

                // Update overall status
                overallStatus.textContent = 'SYSTEM: ' + data.overall.toUpperCase();
                overallStatus.className = 'overall-status ' + data.overall;

                // Update service tiles
                serviceList.innerHTML = (data.services || []).map(svc => {
                    const name = svc.name.replace(/_/g, ' ').toUpperCase();
                    return '<li class="service-item ' + svc.status + '" title="' + (svc.detail || '') + '">' +
                        '<span>' + name + '</span>' +
                        '<span class="status-dot ' + svc.status + '"></span>' +
                        '</li>';
                }).join('');
            } catch (err) {
                console.error('Health poll error:', err);
                overallStatus.textContent = 'SYSTEM: UNREACHABLE';
                overallStatus.className = 'overall-status unhealthy';
            }
        }

        // NL Proposal Submission
        submitBtn.addEventListener('click', async () => {
            const text = nlProposal.value.trim();
            if (!text) {
                showProposalStatus('Please enter a proposal', 'error');
                return;
            }

            submitBtn.disabled = true;
            showProposalStatus('Submitting...', '');

            try {
                const resp = await fetch('/api/propose_nl', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ proposal: text })
                });
                const data = await resp.json();

                if (resp.ok && data.status === 'submitted') {
                    showProposalStatus('Mission submitted! ID: ' + data.mission_id, 'success');
                    nlProposal.value = '';
                } else {
                    throw new Error(data.detail || data.message || 'Submission failed');
                }
            } catch (err) {
                showProposalStatus('Error: ' + err.message, 'error');
            } finally {
                submitBtn.disabled = false;
            }
        });

        function showProposalStatus(msg, type) {
            proposalStatus.textContent = msg;
            proposalStatus.className = 'proposal-status ' + type;
        }

        // WebSocket Connection
        function connectWebSocket() {
            const wsUrl = 'ws://' + window.location.hostname + ':8082/ws/events';
            ws = new WebSocket(wsUrl);

            ws.onopen = () => {
                wsStatus.className = 'status-dot connected';
                wsStatusText.textContent = 'Connected';
            };

            ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                if (data.type === 'context') {
                    eventList.innerHTML = '';
                    data.data.reverse().forEach(e => prependEvent(e));
                    stats.total = data.count || data.data.length;
                    updateStats();
                } else if (data.type !== 'heartbeat' && data.type !== 'pong') {
                    prependEvent(data);
                    updateStatsForEvent(data);
                }
            };

            ws.onclose = () => {
                wsStatus.className = 'status-dot disconnected';
                wsStatusText.textContent = 'Reconnecting...';
                setTimeout(connectWebSocket, 5000);
            };

            ws.onerror = () => wsStatus.className = 'status-dot disconnected';
        }

        function prependEvent(event) {
            const item = document.createElement('div');
            let cls = 'event-item';

            if (event.event_type === 'anomaly_detector_alert') {
                cls += ' alert';
                alertBanner.classList.add('active');
                setTimeout(() => alertBanner.classList.remove('active'), 10000);
            } else if (event.event_type === 'plan_approved') cls += ' approved';
            else if (event.event_type === 'plan_rejected') cls += ' rejected';
            else if (event.outcome === 'HIGH') cls += ' risk_high';

            item.className = cls;
            const ts = event.timestamp || new Date().toISOString();
            const details = event.metadata || event.details || {};

            item.innerHTML = '<div class="event-header">' +
                '<span class="event-type">' + (event.event_type || 'unknown') + '</span>' +
                '<span class="event-time">' + ts + '</span></div>' +
                '<div class="event-details">' + JSON.stringify(details, null, 2) + '</div>';

            eventList.prepend(item);
            while (eventList.children.length > 100) eventList.removeChild(eventList.lastChild);
        }

        function updateStatsForEvent(event) {
            stats.total++;
            if (event.event_type === 'plan_approved') stats.approved++;
            if (event.event_type === 'plan_rejected') stats.rejected++;
            if (event.event_type === 'anomaly_detector_alert') stats.alerts++;
            updateStats();
        }

        function updateStats() {
            document.getElementById('stat-total').textContent = stats.total;
            document.getElementById('stat-approved').textContent = stats.approved;
            document.getElementById('stat-rejected').textContent = stats.rejected;
            document.getElementById('stat-alerts').textContent = stats.alerts;
        }

        function clearEvents() {
            eventList.innerHTML = '';
            stats = { total: 0, approved: 0, rejected: 0, alerts: 0 };
            updateStats();
        }

        // Initialize
        pollSystemHealth();
        connectWebSocket();
        setInterval(pollSystemHealth, 10000);
    </script>
</body>
</html>"""