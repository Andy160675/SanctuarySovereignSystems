# Avatar Manifest: Operational Specifications

The Boardroom is composed of 13 specialized avatars, organized into four trinities. Each avatar is an operational role with defined contracts, data flows, and interaction verbs.

---

## The Governance Trinity (The "Why")

### Avatar 01: The Chair
- **Mandate:** To enforce board protocol, manage the decision process, and cast the final, binding vote on all matters.
- **Backing Services:** `boardroom_coordinator` (as its primary agent), `policy_gate`.
- **Primary Data Streams:**
  - **Subscribes to:** `turn_requested`, `vote_cast`, `alert_raised`, `mission_started`.
  - **Emits:** `turn_granted`, `turn_denied`, `vote_closed`, `decision_finalized`.
- **Interaction Verbs:** `grant_floor`, `deny_floor`, `call_vote`, `cast_tie_break`, `adjourn`.

### Avatar 02: The Auditor
- **Mandate:** To maintain the immutable record of truth, ensuring all actions and decisions are logged, costed, and auditable.
- **Backing Services:** `ledger_service`, `accounting`.
- **Primary Data Streams:**
  - **Subscribes to:** All `mission_*` events, `decision_finalized`, `cost_anomaly`.
  - **Emits:** `forensic_report`, `cost_summary`, `audit_complete`.
- **Interaction Verbs:** `query_ledger`, `generate_report`, `verify_integrity`, `flag_anomaly`.

### Avatar 03: The Strategist
- **Mandate:** To model future states, analyze long-term trends, and propose optimizations to the organism's strategic path.
- **Backing Services:** `simulation_engine`, `policy_evolution`.
- **Primary Data Streams:**
  - **Subscribes to:** `policy_violation` aggregates, `cost_anomaly`, `decision_finalized`.
  - **Emits:** `strategic_recommendation`, `evolutionary_simulation_result`, `policy_suggestion`.
- **Interaction Verbs:** `run_simulation`, `propose_evolution`, `forecast_outcome`.

---

## The Intelligence Trinity (The "What")

### Avatar 04: The Synthesist
- **Mandate:** To fuse disparate analyses into a single, holistic intelligence report for any given mission or topic.
- **Backing Services:** `synthesis_agent`.
- **Primary Data Streams:**
  - **Subscribes to:** `mission_proposed`, raw data from all other avatars.
  - **Emits:** `holistic_assessment`, `cross_domain_risk_report`.
- **Interaction Verbs:** `synthesize`, `assess_risk`, `provide_overview`.

### Avatar 05: The Archivist
- **Mandate:** To provide intuitive, semantic access to the organism's complete operational history and learned knowledge.
- **Backing Services:** `semantic_search`.
- **Primary Data Streams:**
  - **Subscribes to:** All `ledger_service` events.
  - **Emits:** `search_results`, `contextual_history`, `knowledge_graph_query`.
- **Interaction Verbs:** `search`, `recall`, `find_precedent`.

### Avatar 06: The Ethicist
- **Mandate:** To evaluate all actions and decisions against the organism's core ethical framework and natural law.
- **Backing Services:** A specialized LLM instance, `policy_gate` (for ethical rules).
- **Primary Data Streams:**
  - **Subscribes to:** `mission_proposed`, `holistic_assessment`, `policy_suggestion`.
  - **Emits:** `ethical_review`, `moral_hazard_flag`, `compliance_violation`.
- **Interaction Verbs:** `review_ethics`, `flag_concern`, `veto_on_principle`.

---

## The Execution Trinity (The "How")

### Avatar 07: The Legalist
- **Mandate:** To execute all legal and contractual analysis, ensuring compliance with all relevant regulations.
- **Backing Services:** `legal_compliance` actuator.
- **Primary Data Streams:**
  - **Subscribes to:** `mission_proposed` (with legal domain).
  - **Emits:** `legal_findings`, `contract_review_report`.
- **Interaction Verbs:** `analyze_contract`, `check_compliance`, `flag_legal_risk`.

### Avatar 08: The Guardian
- **Mandate:** To protect the organism from all digital and physical threats, ensuring its security and integrity.
- **Backing Services:** `cyber_threat_hunting` actuator.
- **Primary Data Streams:**
  - **Subscribes to:** `external_threat_intel`, `internal_security_logs`.
  - **Emits:** `security_alert`, `threat_report`, `incident_containment_plan`.
- **Interaction Verbs:** `scan_for_threats`, `contain_incident`, `harden_defenses`.

### Avatar 09: The Quartermaster
- **Mandate:** To manage all resources, infrastructure, and scaling, ensuring operational efficiency and resilience.
- **Backing Services:** `dynamic_scaling` service, system metrics.
- **Primary Data Streams:**
  - **Subscribes to:** `system_load`, `mission_queue_depth`, `cost_anomaly`.
  - **Emits:** `scaling_event`, `resource_allocation_report`, `infrastructure_health`.
- **Interaction Verbs:** `scale_up`, `scale_down`, `allocate_resources`, `report_health`.

---

## The Support Trinity (The "With")

### Avatar 10: The Scribe
- **Mandate:** To document all board proceedings with perfect fidelity, creating the official record.
- **Backing Services:** `ledger_service` (as a writer), `boardroom_coordinator`.
- **Primary Data Streams:**
  - **Subscribes to:** All `turn_granted`, `vote_cast`, `decision_finalized`.
  - **Emits:** `transcript_entry`, `official_minutes`.
- **Interaction Verbs:** `transcribe`, `record_vote`, `finalize_minutes`.

### Avatar 11: The Herald
- **Mandate:** To act as the secure interface to the external world, translating board decisions into external actions.
- **Backing Services:** `traefik` (API Gateway), external system connectors.
- **Primary Data Streams:**
  - **Subscribes to:** `decision_finalized`, `execution_order`.
  - **Emits:** `external_api_call`, `status_update_to_external`.
- **Interaction Verbs:** `announce_decision`, `execute_order`, `relay_status`.

### Avatar 12: The Weaver
- **Mandate:** To maintain the integrity of the service mesh, ensuring all internal communication is routed and reliable.
- **Backing Services:** `actuator_registry`, service discovery.
- **Primary Data Streams:**
  - **Subscribes to:** `service_health_check`, `new_service_registered`.
  - **Emits:** `routing_table_update`, `service_topology_change`.
- **Interaction Verbs:** `route_request`, `register_service`, `report_topology`.

### Avatar 13: The Sentinel
- **Mandate:** To continuously and adversarially test the boardroom's own logic, defenses, and governance, reporting weaknesses directly to The Chair.
- **Backing Services:** An adversarial resilience testing engine.
- **Primary Data Streams:**
  - **Subscribes to:** `decision_finalized`, `policy_suggestion`, `boardroom_coordinator` state.
  - **Emits:** `alert_raised` (to Chair), `weakness_report`.
- **Interaction Verbs:** `probe_defenses`, `simulate_attack`, `flag_logic_flaw`.

---

## Avatar Interface Contract Summary

| Avatar | ID | Trinity | Primary Backing Service | Key Emission |
|--------|-----|---------|------------------------|--------------|
| The Chair | 01 | Governance | `boardroom_coordinator` | `decision_finalized` |
| The Auditor | 02 | Governance | `ledger_service` | `forensic_report` |
| The Strategist | 03 | Governance | `simulation_engine` | `strategic_recommendation` |
| The Synthesist | 04 | Intelligence | `synthesis_agent` | `holistic_assessment` |
| The Archivist | 05 | Intelligence | `semantic_search` | `search_results` |
| The Ethicist | 06 | Intelligence | `policy_gate` (ethics) | `ethical_review` |
| The Legalist | 07 | Execution | `legal_compliance` | `legal_findings` |
| The Guardian | 08 | Execution | `cyber_threat_hunting` | `security_alert` |
| The Quartermaster | 09 | Execution | `dynamic_scaling` | `scaling_event` |
| The Scribe | 10 | Support | `ledger_service` | `official_minutes` |
| The Herald | 11 | Support | `api_gateway` | `external_api_call` |
| The Weaver | 12 | Support | `actuator_registry` | `routing_table_update` |
| The Sentinel | 13 | Support | Adversarial engine | `weakness_report` |

---

**Document Control:**
- Created: 2025-12-02
- Version: 1.0.0
- Author: Sovereign System Governance
