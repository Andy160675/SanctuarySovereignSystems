# Boardroom System Topology

This document defines the services, their relationships, and the primary data flows that constitute the Boardroom's operational logic.

---

## Service Architecture

```
                                    CLIENTS
                    +------------------------------------------+
                    |  dashboard_web  |  client_desktop  |  VR |
                    +------------------------------------------+
                                      |
                                      | WebSocket + REST
                                      v
                    +------------------------------------------+
                    |         boardroom_coordinator            |
                    |  (Control plane: state, turns, votes)    |
                    +------------------------------------------+
                            |                       |
            +---------------+                       +---------------+
            |                                                       |
            v                                                       v
+------------------------+                           +------------------------+
|   AVATAR AGENTS        |                           |   CORE SERVICES        |
|  (Logical processes)   |                           |                        |
|                        |                           |  - ledger_service      |
|  01 Chair              |<------------------------->|  - policy_gate         |
|  02 Auditor            |                           |  - synthesis_agent     |
|  03 Strategist         |                           |  - simulation_engine   |
|  04 Synthesist         |                           |  - semantic_search     |
|  05 Archivist          |                           |  - accounting          |
|  06 Ethicist           |                           |                        |
|  07 Legalist           |                           +------------------------+
|  08 Guardian           |                                       |
|  09 Quartermaster      |                                       |
|  10 Scribe             |                                       v
|  11 Herald             |                           +------------------------+
|  12 Weaver             |                           |   ACTUATORS            |
|  13 Sentinel           |                           |                        |
|                        |<------------------------->|  - legal_compliance    |
+------------------------+                           |  - cyber_threat_hunter |
                                                     |  - dynamic_scaling     |
                                                     |  - evidence_writer     |
                                                     +------------------------+
                                                                 |
                                                                 v
                                                     +------------------------+
                                                     |   EXTERNAL SYSTEMS     |
                                                     |  (via Herald/Gateway)  |
                                                     +------------------------+
```

---

## Service Definitions

### Core Governance Plane
- **boardroom_coordinator** (Port 8200): The central nervous system of the Boardroom. Manages avatar state, turn-taking, mission lifecycle, and voting. Broadcasts all events via WebSocket.

### Internal Services
| Service | Port | Purpose |
|---------|------|---------|
| `ledger_service` | 8082 | Immutable append-only event log |
| `policy_gate` | 8181 | Policy enforcement (OPA) |
| `synthesis_agent` | 5800 | Cross-domain risk synthesis |
| `semantic_search` | TBD | Vector search over history |
| `simulation_engine` | TBD | Policy evolution simulations |
| `accounting` | TBD | Cost tracking and attribution |

### Actuators
| Actuator | Port | Domain |
|----------|------|--------|
| `legal_compliance` | 5011 | Contract/regulatory analysis |
| `cyber_threat_hunting` | TBD | Security threat detection |
| `dynamic_scaling` | TBD | Infrastructure scaling |
| `evidence_writer` | 8083 | Artifact persistence |

### Clients
- **dashboard_web**: React-based 2D Boardroom interface
- **client_desktop**: Native desktop application (future)
- **client_vr**: 3D/VR immersive interface (future)

---

## Primary Data Flows

### Flow 1: High-Risk Mission Approval

```
[External Request]
       |
       v
  +--------+     1. Ingest mission
  | Herald |------------------------->  [boardroom_coordinator]
  +--------+                                      |
                                                  | 2. Start session
                                                  v
                        +--------------------------------------------+
                        |              BOARDROOM SESSION              |
                        |                                            |
                        |  3. Route to avatars for analysis:         |
                        |     - Synthesist: holistic assessment      |
                        |     - Legalist: compliance check           |
                        |     - Guardian: security review            |
                        |     - Ethicist: ethical evaluation         |
                        |                                            |
                        |  4. Chair grants floor to each presenter   |
                        |                                            |
                        |  5. Chair calls vote                       |
                        |     - All 13 avatars cast votes            |
                        |     - Majority wins, Chair breaks ties     |
                        |                                            |
                        |  6. Chair finalizes decision               |
                        +--------------------------------------------+
                                          |
                                          v
                        +--------------------------------------------+
                        |  7. Auditor logs to ledger_service         |
                        |  8. Herald executes approved action        |
                        +--------------------------------------------+
```

### Flow 2: Incident Response

```
[Security Event Detected]
       |
       v
  +----------+     1. Detect & classify threat
  | Guardian |----------------------------------+
  +----------+                                  |
       |                                        |
       | 2. Raise security_alert                |
       v                                        |
  [boardroom_coordinator]                       |
       |                                        |
       | 3. Auto-elevate to HIGH priority       |
       |    session, notify all avatars         |
       v                                        |
  +--------------------------------------------+
  |              EMERGENCY SESSION              |
  |                                            |
  |  4. Guardian & Sentinel present threat     |
  |  5. Quartermaster reports capacity         |
  |  6. Chair calls immediate vote on          |
  |     containment plan                       |
  |                                            |
  +--------------------------------------------+
       |
       | 7. Decision: CONTAIN / ESCALATE
       v
  +----------+     8. Execute containment
  |  Herald  |---> [External systems]
  +----------+
       |
  +--------------+ 9. Scale defenses
  | Quartermaster|---> [dynamic_scaling]
  +--------------+
```

### Flow 3: Policy Evolution

```
[Ledger Analysis Complete]
       |
       v
  +------------+     1. Analyze patterns
  | Strategist |--------------------------------+
  +------------+                                |
       |                                        |
       | 2. Generate policy_suggestion          |
       v                                        |
  +-----------+     3. Ethical review           |
  | Ethicist  |<--------------------------------+
  +-----------+
       |
       | 4. Route to boardroom_coordinator
       v
  +--------------------------------------------+
  |           POLICY CHANGE SESSION            |
  |                                            |
  |  5. Strategist presents simulation data    |
  |  6. Synthesist provides impact analysis    |
  |  7. Ethicist renders ethical opinion       |
  |  8. Chair calls vote                       |
  |                                            |
  +--------------------------------------------+
       |
       | 9. If approved:
       v
  +-------------+    10. Update policy rules
  | policy_gate |<---------------------------+
  +-------------+                            |
       |                                     |
  +----------+     11. Propagate changes     |
  |  Weaver  |-------------------------------+
  +----------+
```

### Flow 4: Deconfliction

```
[Multiple missions in queue]
       |
       v
  +----------+     1. Detect resource conflict
  |  Weaver  |--------------------------------+
  +----------+                                |
       |                                      |
       | 2. Flag conflict to Chair            |
       v                                      |
  [boardroom_coordinator]                     |
       |                                      |
       | 3. Pause conflicting missions        |
       v                                      |
  +--------------------------------------------+
  |          DECONFLICTION SESSION             |
  |                                            |
  |  4. Quartermaster: resource inventory      |
  |  5. Synthesist: priority assessment        |
  |  6. Chair: arbitration decision            |
  |                                            |
  +--------------------------------------------+
       |
       | 7. Prioritized execution order
       v
  [Mission Queue Updated]
```

### Flow 5: Scaling Decision

```
[System Load Threshold Exceeded]
       |
       v
  +--------------+     1. Monitor metrics
  | Quartermaster|--------------------------------+
  +--------------+                                |
       |                                          |
       | 2. Generate scaling_recommendation       |
       v                                          |
  +--------------------------------------------+
  |              SCALING SESSION                |
  |  (Auto-approved for < CRITICAL risk)        |
  |                                            |
  |  3. Quartermaster presents data            |
  |  4. Auditor confirms cost impact           |
  |  5. Chair approves (if CRITICAL, vote)     |
  |                                            |
  +--------------------------------------------+
       |
       | 6. Execute scaling action
       v
  +----------------+
  | dynamic_scaling|---> [Infrastructure]
  +----------------+
```

---

## Event Protocol Summary

### WebSocket Events (boardroom_coordinator /ws)

| Event Type | Direction | Description |
|------------|-----------|-------------|
| `init_state` | Server->Client | Full state on connect |
| `mission_started` | Server->Client | New mission opened |
| `mission_updated` | Server->Client | Mission data changed |
| `mission_closed` | Server->Client | Mission decided |
| `turn_requested` | Client->Server | Avatar requests floor |
| `turn_granted` | Server->Client | Floor granted |
| `turn_released` | Server->Client | Floor released |
| `vote_started` | Server->Client | Voting window open |
| `vote_cast` | Server->Client | Individual vote recorded |
| `vote_closed` | Server->Client | Voting complete |
| `alert_raised` | Server->Client | Critical alert from avatar |

---

## Port Allocation

| Port | Service | Protocol |
|------|---------|----------|
| 8000 | control_killswitch | HTTP |
| 8080 | filesystem_proxy | HTTP |
| 8082 | ledger_service | HTTP |
| 8083 | evidence_writer | HTTP |
| 8084 | api_gateway_proxy | HTTP |
| 8085 | db_proxy | HTTP |
| 8090 | planner_agent | HTTP |
| 8091 | advocate_agent | HTTP |
| 8092 | confessor_agent | HTTP |
| 8093 | watcher_agent | HTTP |
| 8095 | amendment_service | HTTP |
| 8096 | runtime_interface | HTTP |
| 8097 | phase_status | HTTP |
| 8100 | command_center | HTTP |
| 8181 | policy_gate | HTTP |
| 8200 | boardroom_coordinator | HTTP+WS |
| 5011 | legal_compliance | HTTP |
| 5100 | actuator_registry | HTTP |
| 5800 | synthesis_agent | HTTP |

---

**Document Control:**
- Created: 2025-12-02
- Version: 1.0.0
- Author: Sovereign System Architecture
