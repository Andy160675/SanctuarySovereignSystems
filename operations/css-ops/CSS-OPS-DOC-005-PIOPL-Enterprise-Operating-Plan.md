# CSS-OPS-DOC-005 — PIOPL Enterprise Operating Plan

**CONTROLLED DOCUMENT — DO NOT PRINT**

| Field | Value |
|---|---|
| Document Reference | CSS-OPS-DOC-005 |
| Version | 1.0 DRAFT — FOR LT REVIEW |
| Classification | INTERNAL — LT DISTRIBUTION ONLY |
| Author | Andy Jones, Steward |
| Date | 17 February 2026 |
| Derives From | CSS-OPS-DOC-003 (SIP Engine), CSS-OPS-DOC-004 (Agent Deployment), CSS-STRAT-DOC-001 (Creator777) |
| Constitutional Weight | **BINDING — Post LT Buy-Off** |
| Distribution | Andy (FULL), Steven (FULL), Chris Bevan (GOV/OPS), Tom Maher (ROLLOUT) |

---

## 1. What This Document Does

Defines the complete PIOPL enterprise — an organisation where every business function is executed by governed AI agents. Seven divisions, each staffed by PIOPL agents, each generating revenue, each subject to constitutional governance.

Andy provides patterns and direction. The LT governs at weekly gates. PIOPL agents execute everything between gates. Revenue flows through three-ledger reconciliation. The machine runs. Humans review.

> **INVARIANT:** Every business function is assigned to a PIOPL agent division. If a function has no agent owner, it either doesn't exist yet (needs a SIP) or it is one of the four irreducible human touchpoints from CSS-OPS-DOC-003.

## 2. The Seven Divisions

| DIV | NAME | FUNCTION | AGENT COUNT (TARGET) | REVENUE TYPE |
|---|---|---|---|---|
| D1 | CREATOR ACQUISITION | Find, attract, and onboard creators onto the platform. | 50–200 | Subscription fees |
| D2 | PRODUCTION | Generate digital assets: templates, music, designs, courses. The factory floor. | 20,000+ | Product sales |
| D3 | DISTRIBUTION | List and distribute across marketplaces: Gumroad, DistroKid, Etsy, KDP, Redbubble. | 2,000–5,000 | Platform revenue |
| D4 | PROMOTION | Market via social media, email, SEO, paid ads. Drive traffic. | 500–2,000 | Traffic → sales |
| D5 | CUSTOMER OPS | Support, onboarding, billing queries, refunds, upsell. AI-first. | 100–500 | Retention → LTV |
| D6 | FINANCE & BILLING | Invoicing, payment processing, dunning, revenue recognition, three-ledger reconciliation. | 50–200 | Cash flow |
| D7 | GOVERNANCE & INTEL | Watchtower, Sentinel, behaviour scoring, SITREP, evidence chain management. | 100–500 | Risk reduction |

Total target: 23,000–28,500 agents. D2 is largest by design — that's the factory.

## 3. Division Detail — Agent Roles

### D1 — Creator Acquisition

| Agent Role | Function | Tier | Outputs |
|---|---|---|---|
| lead_scanner | Scan social platforms for emerging creators | Tier 0 — Read-only | Creator lead lists |
| outreach_agent | Send personalised outreach via email/DM | Tier 1 — Monitored | Sent messages, response rates |
| onboarding_agent | Guide creators through signup and first asset | Tier 1 — Monitored | Completed onboards |
| landing_page_agent | Generate and deploy landing pages, A/B test | Tier 0 — Automated | Live pages, conversion rates |

### D2 — Production (Factory Floor)

| Agent Role | Function | Tier | Outputs |
|---|---|---|---|
| trend_scanner | Identify trending niches and demand signals daily | Tier 0 — Read-only | Trend reports |
| template_generator | Create digital templates (Canva, Notion, planners) | Tier 0 — Automated | Template files + confidence scores |
| music_generator | Create music via Suno/Udio, package into albums | Tier 0 — Automated | Audio files, album metadata |
| design_generator | Create visual assets (graphics, POD, brand kits) | Tier 0 — Automated | Image files, mockups |
| course_builder | Structure educational content (outlines, scripts, quizzes) | Tier 0 — Automated | Course packages |
| quality_gate | Review all D2 output. Reject below confidence floor. | Tier 0 — Automated | Pass/fail per asset |

### D3 — Distribution

| Agent Role | Function | Tier | Outputs |
|---|---|---|---|
| gumroad_publisher | List products on Gumroad with optimised metadata | Tier 1 — Monitored | Live listing URLs |
| distrokid_publisher | Distribute music to streaming platforms | Tier 1 — Monitored | Distribution confirmations |
| marketplace_publisher | List on Etsy, Amazon KDP, Redbubble, Creative Market | Tier 1 — Monitored | Multi-platform reports |
| seo_optimiser | Optimise all listings for search | Tier 0 — Automated | SEO scores |

### D4 — Promotion

| Agent Role | Function | Tier | Outputs |
|---|---|---|---|
| social_poster | Create and schedule posts across platforms | Tier 1 — Monitored | Posts published, engagement |
| email_marketer | Build and send email campaigns | Tier 1 — Monitored | Open/click rates |
| youtube_producer | Generate faceless YouTube content packages | Tier 0 — Automated | Video packages |
| ad_manager | Manage low-budget paid ads | **Tier 2 — Controlled (spends money)** | ROAS reports |

### D5 — Customer Ops

| Agent Role | Function | Tier | Outputs |
|---|---|---|---|
| support_responder | Handle inbound support queries | Tier 1 — Monitored | Resolution rate, CSAT |
| upsell_agent | Identify upsell/cross-sell opportunities | Tier 1 — Monitored | Conversion rate |
| retention_agent | Monitor churn, send win-back sequences | Tier 1 — Monitored | Churn rate, LTV |

### D6 — Finance & Billing

| Agent Role | Function | Tier | Outputs |
|---|---|---|---|
| invoice_generator | Create and send invoices | Tier 1 — Monitored | Invoices sent |
| payment_monitor | Track payment status via Stripe webhooks | Tier 1 — Monitored | Payment status |
| dunning_agent | Automated payment reminders, service holds | **Tier 2 — Controlled** | Collection rate |
| reconciliation_agent | Cross-check three ledgers, flag variance >1.5% | Tier 0 — Automated | Reconciliation reports |

### D7 — Governance & Intelligence

| Agent Role | Function | Tier | Outputs |
|---|---|---|---|
| watchtower_agent | Run 26 DDT detectors across all divisions | Tier 0 — Automated | Drift reports |
| sentinel_agent | Enforce hard stops, issue HALT_ALL | Tier 0 — Automated | HALT events |
| sitrep_generator | Produce daily auto-SITREP and weekly gate packs | Tier 0 — Automated | SITREP documents |
| behaviour_scorer | Continuously score all agents | Tier 0 — Automated | Score reports |
| evidence_manager | Manage hash-linked evidence chains | Tier 0 — Automated | Integrity reports |

> **INVARIANT:** D7 agents govern all other divisions. They are the only agents that can pause, throttle, or terminate other agents. No D1–D6 agent can override a D7 action.

## 4. Revenue Flow

| Channel | Source | Divisions | Expected Monthly (at scale) |
|---|---|---|---|
| Digital Product Sales | Templates, designs, courses on Gumroad, Etsy, KDP | D2 → D3 → D4 | £200K–£800K |
| Music Streaming & Sales | AI music via DistroKid to Spotify, Apple, YouTube | D2 → D3 | £50K–£200K |
| Creator Subscriptions | Monthly fee for personal PIOPL agent access | D1 → D5 → D6 | £50K–£150K |
| Governance Licensing | SDK licensing of constitutional framework | D7 (exported) | £0 (Phase 4+) |

**Total revenue target at 25,000 agents: £300K–£1.15M per month.**

## 5. Deployment Sequence

| Phase | Timeline | Agents Deployed | Success Criterion |
|---|---|---|---|
| 1. FOUNDATION | Weeks 1–6 | 14 agents: 10 template_generator, 1 gumroad_publisher, 1 quality_gate, 1 watchtower, 1 reconciliation | First £ earned. Complete audit trail. Unit economics positive over 30 days. |
| 2. CONTROLLED | Weeks 6–12 | +100 production, +10 distribution, +5 social, +3 support, +landing_page | Net positive across 100+ agents for 4 consecutive weeks. |
| 3. INDUSTRIALISE | Months 3–6 | +1,000 production, full D3/D4/D5/D6/D7 | Human load flat despite agent growth. Revenue covers infra. |
| 4. AUTONOMOUS | Months 6–12 | Scale to 5,000–25,000 across all divisions | Enterprise self-sustaining. Revenue >£100K/month. |

> **INVARIANT:** Phase 1 deploys exactly 14 agents. The purpose is to prove the model earns money before scaling anything.

## 6. The First SIP — Revenue Pipeline Live (5-Day Sprint)

**SIP-001** | Horizon: 5 days | Success: At least one product listed on Gumroad with live payment link AND complete evidence trail.

### Pre-Conditions (Before Freeze)

| # | Pre-Condition | Owner | Verification |
|---|---|---|---|
| 1 | Gumroad account active with API key | Steven | Test API call returns 200 |
| 2 | Stripe connected to Gumroad | Steven | Test payout path verified |
| 3 | Node-0 Docker available | Andy | Docker ps shows capacity |
| 4 | Agent registry database initialised | Andy + Claude | Schema deployed, test row |
| 5 | LT vote: 3/3 YES on SIP-001 | Andy, Steven, Chris | Vote recorded and hashed |

### Atomic Tasks (Post-Freeze)

| # | Task | Agent | Evidence | Deadline |
|---|---|---|---|---|
| 1 | Deploy agent registry on Node-0 | Infrastructure | Schema hash + test query | Day 1 |
| 2 | Create 10 template_generator profiles | Profile engine | 10 validated profiles | Day 1 |
| 3 | Issue capability tokens | Token service | 10 signed tokens | Day 1 |
| 4 | Generate 50 digital templates | template_generator x10 | 50 files + confidence scores | Day 2 |
| 5 | Quality gate reviews all 50 | quality_gate | Pass/fail report | Day 2 |
| 6 | List top 10 on Gumroad | gumroad_publisher | 10 live URLs | Day 3 |
| 7 | Watchtower confirms listings | watchtower_agent | HTTP 200 + screenshots | Day 3 |
| 8 | Initialise three ledgers | reconciliation_agent | Ledger schema + zero-state hash | Day 4 |
| 9 | Auto-SITREP for Day 5 gate | sitrep_generator | SITREP document | Day 5 |
| 10 | LT gate review | **HUMAN (LT)** | Vote + next SIP decision | Day 5 |

## 7. Enterprise Hierarchy

| Level | Entity | Authority |
|---|---|---|
| L0 | STEWARD (Andy) | Absolute. Creates SIPs. Can override any agent at any gate. |
| L1 | LT (Steven, Chris) | Governance. Votes at gates. Cannot override Steward or intervene mid-cycle. |
| L2 | D7 GOVERNANCE AGENTS | Enforcement. Can pause/throttle/terminate D1–D6. Cannot create SIPs. |
| L3 | D1–D6 EXECUTION AGENTS | Execution within capability token scope. Cannot modify own permissions. |

## 8. What This Replaces

| Draft Concept (Source) | Now Covered By |
|---|---|
| Revenue Pipeline Engine (ChatGPT) | D1 + D6 |
| Customer Onboarding Engine (ChatGPT) | D1 (onboarding_agent) + D5 |
| Customer Support Engine (ChatGPT) | D5 (support_responder + retention_agent) |
| Billing Execution Engine (ChatGPT) | D6 (all four agents) |
| Enterprise Readiness Deployment (ChatGPT) | CSS-OPS-DOC-004 + Section 5 above |
| System Briefing (ChatGPT) | This entire document |
| Creator Agency Copy (ChatGPT) | Retained for D1 outreach + D4 templates |

## 9. Constitutional Binding

- **Steward:** Deploy in phased sequence. Enforce phase gates. Never scale before economic validation.
- **LT:** Vote on SIPs per division. Review fleet metrics weekly. Refuse deployments that skip phases.
- **Machine:** Execute within division boundaries. Enforce tier controls. Produce evidence. Prefer stopping to lying.

---

| STEWARD SIGN-OFF | LT MEMBER 2 | LT MEMBER 3 |
|---|---|---|
| Andy Jones | Steven Jones | Chris Bevan |
| Date: ___________ | Date: ___________ | Date: ___________ |
| Vote: YES / NO | Vote: YES / NO | Vote: YES / NO |
