# CSS-OPS-DOC-004 — PIOPL Agent Deployment Engine

**CONTROLLED DOCUMENT — DO NOT PRINT**

| Field | Value |
|---|---|
| Document Reference | CSS-OPS-DOC-004 |
| Version | 1.0 DRAFT — FOR LT REVIEW |
| Classification | INTERNAL — LT DISTRIBUTION ONLY |
| Author | Andy Jones, Steward |
| Date | 16 February 2026 |
| Derives From | CSS-OPS-DOC-003 (Post-SIP Execution Engine), CSS-STRAT-DOC-001 (Creator777 Strategy) |
| Constitutional Weight | **BINDING — Post LT Buy-Off** |
| Distribution | Andy (FULL), Steven (FULL), Chris Bevan (GOV/OPS), Tom Maher (ROLLOUT) |

---

## 1. What This Document Does

Defines how to deploy, govern, and scale a fleet of PIOPL agents (Personal Intelligence Operating Partner Links) as digital employees of Codex Sovereign Systems. Each agent has its own identity, capabilities, governance constraints, and earning streams. Target: 25,000 agents.

This document extends CSS-OPS-DOC-003. Every agent deployment is a SIP. Every agent action is an atomic task. Every agent is subject to Watchtower/Sentinel enforcement.

> **INVARIANT:** A PIOPL agent is a governed digital employee, not an unmonitored script. It has identity, boundaries, audit trails, and a kill switch. If any of these are missing, the agent cannot be deployed.

## 2. What a PIOPL Agent Is (And Is Not)

| A PIOPL Agent IS | A PIOPL Agent IS NOT |
|---|---|
| A digital employee with unique identity and profile | A cron job or unmonitored script |
| Governed by constitutional invariants with evidence-grade audit | A black box that runs without oversight |
| Assigned specific capabilities via signed tokens (revocable) | Granted blanket access to all systems |
| Revenue-generating with tracked earnings per agent | A cost centre or internal tool only |
| Deployed via SIP (frozen plan, gate review, evidence) | Spun up ad hoc without governance |
| Capable of halting itself if output quality is below threshold | Allowed to produce garbage to meet a quota |

## 3. Agent Profile Schema

Every agent has four blocks. No agent deploys without all four complete and validated.

### 3.1 Identity Block

| Field | Type / Format | Example |
|---|---|---|
| agent_id | String. Auto-generated. Immutable. | piopl_00001 |
| name | Human-readable label. | ContentCrafter_Alpha |
| role | Enum from role registry. | digital_product_generator |
| tier | 0 / 1 / 2 (see Section 4). | 0 |
| version | SemVer. Increments on profile change. | 1.0.0 |
| created | ISO 8601 timestamp. | 2026-02-16T15:00:00Z |
| status | pending / active / paused / terminated | active |
| owner | Human or org entity responsible. | andy.jones@css |

### 3.2 Capability Block

| Field | Type / Format | Example |
|---|---|---|
| capabilities | Array of capability token IDs. | [trend_scan, template_gen, gumroad_publish] |
| can_send_to | Allowlist of external endpoints. | [gumroad_api, linkedin_api] |
| never_sends | Hard blocklist. Constitutional. | [customer_pii, financial_credentials, unauthorised_prompts] |
| max_spend_per_day | Currency amount. Hard cap. | £0.00 (Tier 0 agents cannot spend) |
| output_confidence_floor | Float 0–1. Below this, agent halts. | 0.85 |

### 3.3 Governance Block

| Field | Type / Format | Enforcement |
|---|---|---|
| constitution_hash | SHA-256 of governing constitution. | Agent refuses to start if hash mismatch. |
| invariants_enforced | Array of invariant IDs. | Watchtower checks compliance per action. |
| kill_switch | Boolean. Always TRUE. | Steward can terminate instantly. Non-negotiable. |
| audit_chain | Hash-linked action log. | Every action hashed + timestamped. Immutable. |
| behaviour_score | Float 0–100. Continuous. | Below 60: auto-throttle. Below 40: auto-pause. |

### 3.4 Revenue Block

| Field | Type / Format | Example |
|---|---|---|
| earning_model | revenue_share / fixed_stipend / hybrid | revenue_share |
| revenue_share_pct | Percentage retained by CSS. | 80% to CSS, 20% to subscriber |
| settlement_account | Stripe Connect ID or internal ledger ref. | acct_css_revenue_001 |
| lifetime_revenue | Cumulative. Auto-tracked. | £0.00 (new agent) |
| cost_to_date | Cumulative operational cost. | £0.00 (new agent) |

## 4. Agent Runtime Tiers

| Tier | Purpose | Runtime | Control Level | Scale Target |
|---|---|---|---|---|
| 0 | Deterministic generation (templates, music, assets) | Stateless container on Node-0 or serverless | Fully automated. No human in loop. | 20,000+ |
| 1 | Marketplace interaction (listing, promotion, social) | API-governed microservice. Rate-limited. | Behaviour monitored. Auto-throttle on drift. | 4,000+ |
| 2 | Revenue + customer interaction (payments, support, spend) | Controlled runtime with approval gates. | Human oversight on irreversible actions. | 1,000+ |

> **DESIGN RULE:** Start with Tier 0 only. Prove unit economics before unlocking Tier 1. Prove governance enforcement before unlocking Tier 2.

## 5. Capability Tokens

Capabilities are signed, time-bounded, revocable tokens — not static profile entries.

```
cap_token = sign(agent_id, capability_scope, issued_at, expires_at, risk_level)
```

| Field | Purpose | Example |
|---|---|---|
| agent_id | Which agent holds this capability. | piopl_00001 |
| capability_scope | What the agent can do. | gumroad_publish |
| issued_at | When token was granted. | 2026-02-16T15:00:00Z |
| expires_at | When token becomes invalid. | 2026-03-16T15:00:00Z (30-day default) |
| risk_level | low / medium / high / critical | low (Tier 0) / high (Tier 2 spend) |

> **INVARIANT:** Capability is not permission. Without a valid capability token, the call is blocked and logged as a policy violation.

## 6. Deployment Pipeline

Follows the SIP lifecycle from CSS-OPS-DOC-003. Agent-specific implementation:

### Phase 1 — SIP Formation (Human)

Pre-conditions before freeze: Role template exists, infrastructure ready, API credentials available and tested, revenue ledger configured, LT vote 3/3.

### Phase 2 — Decomposition (Machine)

8 atomic tasks per agent: Generate ID → Populate profile → Issue tokens → Compliance gate → Provision runtime → Inject credentials → Run activation test → Set ACTIVE.

### Phase 3 — Execution (Machine)

Active agents execute: scan → generate → publish → promote → earn. Each cycle produces evidence. Watchtower monitors. Sentinel enforces.

### Phase 4 — Gate Review (Human)

Weekly LT gate reviews: active count, revenue per agent, cost per agent, behaviour scores, drift incidents, HALT events.

## 7. Unit Economics

| Metric | Conservative | Expected | Mature |
|---|---|---|---|
| Monthly revenue per agent | £8 | £22 | £60 |
| API + runtime cost per agent | £0.70 | £1.20 | £2.00 |
| Platform fees (10–20%) | £1.60 | £4.40 | £12.00 |
| **Net contribution per agent** | **£5.70** | **£16.40** | **£46.00** |

### Break-Even and Scale Projections

Fixed operating cost: £5,000/month.

| Milestone | Agents | Monthly Net | After Fixed Costs | Status |
|---|---|---|---|---|
| Break-even (conservative) | 877 | £5,000 | £0 | BREAK-EVEN |
| Break-even (expected) | 305 | £5,000 | £0 | BREAK-EVEN |
| Phase 3 target | 1,000 | £16,400 | +£11,400 | PROFITABLE |
| Full scale | 25,000 | £410,000 | +£405,000 | SCALE |

> **INVARIANT:** Do not scale before economic validation. First 10 agents must prove net positive unit economics over 30 days before batch deployment.

## 8. Behavioural Governance

### Behaviour Score Components

| Component | Weight | Measures |
|---|---|---|
| Compliance consistency | 30% | Actions within boundaries / total actions |
| Output quality | 25% | Confidence scores, rejection rates |
| Revenue efficiency | 25% | Revenue per API call, cost ratio |
| Anomaly frequency | 20% | Unexpected behaviours, drift events |

### Score Thresholds

| Score | Status | System Response |
|---|---|---|
| 80–100 | HEALTHY | Normal operation |
| 60–79 | DEGRADED | Auto-throttle. Flagged for review. |
| 40–59 | PAUSED | Agent auto-paused. Capabilities frozen. |
| 0–39 | TERMINATED | Agent terminated. All tokens revoked. Audit sealed. |

## 9. Three Ledgers — Revenue Assurance

| Ledger | What It Records | Reconciliation Rule |
|---|---|---|
| Activity Ledger | What each agent did | Must correlate 1:1 with Revenue Ledger entries. |
| Revenue Ledger | What platforms report | Must match Settlement Ledger within 1.5% per cycle. |
| Settlement Ledger | What was actually paid | Source of truth for P&L. Audited weekly. |

> **INVARIANT:** Revenue variance above 1.5% per cycle triggers automatic audit review at next LT gate.

## 10. Scaling Pathway — Four Phases

| Phase | Timeline | Deliverables | Success Criterion |
|---|---|---|---|
| 1. FOUNDATION | 0–6 weeks | Agent registry, token service, evidence pipeline, single-agent runtime, revenue ledger | First agent produces revenue AND complete audit trail. |
| 2. CONTROLLED | 6–12 weeks | Batch provisioning, tiered runtime, behaviour scoring, marketplace integration | Net positive unit economics sustained 4 weeks across 100–250 agents. |
| 3. INDUSTRIALISE | 3–6 months | Kubernetes, multi-account API, automated niche allocation, self-healing runtime | Human load does not scale with agent count. 1,000+ agents. |
| 4. AUTONOMOUS | 6–12 months | Strategic allocation, agent retirement, capital reinvestment, predictive modelling | System is an economic organism. 5,000–25,000 agents. |

## 11. Infrastructure Mapping

| Component | Current (Node-0) | Target (25,000 Agents) |
|---|---|---|
| Agent registry | Does not exist yet. | PostgreSQL on NAS → Cloud RDS (Phase 3+). |
| Runtime | UGREEN DXP4800 Plus. Docker capable. | Node-0 Docker → Kubernetes cluster (Phase 3+). |
| Networking | Tailscale mesh (Node-0 ↔ Node-1). | Tailscale + cloud VPC. |
| Secure storage | Tresorit Business (Swiss, E2E encrypted). | Tresorit for docs + S3/Backblaze for audit logs. |
| Monitoring | Watchtower DDT (26 detectors). | Extended with behaviour scoring engine. |
| Revenue tracking | No payment rails live. | Stripe Connect + three-ledger reconciliation. |

## 12. Risk Register

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Agent misbehaviour | Medium | Medium | Behaviour scoring + auto-throttle + kill switch |
| API rate limits | High | Medium | Multi-account distribution + request queuing |
| Revenue leakage | Medium | High | Three-ledger reconciliation, 1.5% threshold |
| Infra cost > revenue | Medium | High | Phase gates: no scale before economic validation |
| Constitutional violation | Low | Critical | Hard-coded invariants + Sentinel HALT |
| Platform terms change | Medium | Medium | Multi-platform, no single dependency |
| Scaling too fast | High | High | Phase gates are non-negotiable |

## 13. Constitutional Binding

- **Steward:** Deploy agents only via frozen SIPs. Enforce phase gates. Review behaviour scores weekly. Terminate agents violating invariants.
- **LT:** Vote on deployment SIPs with economic evidence. Review fleet metrics weekly. Refuse scale requests that skip phases.
- **Machine:** Enforce capability tokens. Score behaviour continuously. Halt agents below threshold. Reconcile revenue across three ledgers. Produce evidence for every action.

---

| STEWARD SIGN-OFF | LT MEMBER 2 | LT MEMBER 3 |
|---|---|---|
| Andy Jones | Steven Jones | Chris Bevan |
| Date: ___________ | Date: ___________ | Date: ___________ |
| Vote: YES / NO | Vote: YES / NO | Vote: YES / NO |
