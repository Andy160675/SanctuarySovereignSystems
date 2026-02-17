# CSS-OPS-DOC-006 — Meeting Structures, Escalation Paths & Andon System

**CONTROLLED DOCUMENT — DO NOT PRINT**

| Field | Value |
|---|---|
| Document Reference | CSS-OPS-DOC-006 |
| Version | 1.0 DRAFT — FOR LT REVIEW |
| Classification | INTERNAL — ALL TEAM |
| Author | Andy Jones, Steward |
| Date | 17 February 2026 |
| Derives From | CSS-OPS-DOC-003 (SIP Engine, Sec 9), CSS-OPS-DOC-005 (Enterprise Plan) |
| Constitutional Weight | **BINDING — Post LT Buy-Off** |
| Distribution | Andy (FULL), Steven (FULL), Chris Bevan (FULL), Tom Maher (FULL) — ALL TEAM |

---

## 1. What This Document Does

Three operational systems that make the SIP engine and enterprise plan function:

**PART A — MEETING STRUCTURES:** Cadence, format, and rules for every meeting. When they happen, what they cover, how long they take, what they produce.

**PART B — ESCALATION PATHS:** How blockers surface, who they escalate to, on what timeline, and what happens when escalation fails.

**PART C — ANDON SYSTEM:** Toyota-principle cord-pull. Anyone — human or agent — can halt the line when something is wrong. Stop, diagnose, fix, restart.

> **INVARIANT:** Without these three systems, the governance documents are paper. SIPs that never get reviewed die. Blockers that never surface rot. Quality problems that nobody catches compound.

---

# PART A — MEETING STRUCTURES

## 2. Meeting Cadence Overview

| Meeting | Frequency | Time | Attendees | Duration |
|---|---|---|---|---|
| DAILY STAND-UP | Daily | 12:30 UK | All active team + AI (via SITREP) | **15 min MAX** |
| WEEKLY LT GATE | Weekly | Monday 12:30 UK | LT: Andy, Steven, Chris | **30 min MAX** |
| MONTHLY STRATEGIC | Monthly | First Monday, 12:30 UK | LT + Tom Maher | **60 min MAX** |

> **INVARIANT:** No meeting exceeds its time limit. Unresolved items carry forward or become escalation blockers.

### 2.1 Daily Stand-Up (15 minutes)

Purpose: Surface blockers. Synchronise humans with machine status. Not a discussion forum.

| Minute | Agenda Item | Source | Output |
|---|---|---|---|
| 0–2 | Auto-SITREP read-out | sitrep_generator (D7) | Status confirmed |
| 2–5 | BLOCKER BOARD | Each human + escalation log | Blockers acknowledged or Andon pulled |
| 5–10 | TODAY'S PRIORITY: one thing each person will unblock today | Each human | Commitment logged |
| 10–13 | ANDON STATUS: any active alerts? | Andon dashboard (D7) | Andon acknowledged or resolved |
| 13–15 | CLOSE: any escalation needed? | Steward | Stand-up log filed |

**Stand-up Rules:**
1. Three questions per person: What did you unblock? What will you unblock today? What's blocking you?
2. No problem-solving in the stand-up. Blockers go to escalation or working sessions.
3. Absent? Auto-SITREP speaks for you. The machine always shows up.
4. Log is hashed and stored. It is evidence.

### 2.2 Weekly LT Gate (30 minutes)

Per CSS-OPS-DOC-003 Section 9. The governance checkpoint.

| Minute | Agenda Item | Source | Output |
|---|---|---|---|
| 0–5 | AUTO-SITREP: weekly summary, revenue, costs, agent count | sitrep_generator (D7) | Facts confirmed |
| 5–10 | BLOCKERS & ESCALATIONS: all HALT-HUMAN-DEPENDENCY items | Escalation log + Andon dashboard | Resolved or owners assigned |
| 10–15 | DRIFT REPORT: Watchtower DDT output | watchtower_agent (D7) | Drift acknowledged or actioned |
| 15–20 | EVIDENCE REVIEW: completed tasks verified or rejected | evidence_manager (D7) | COMPLETE or REJECTED |
| 20–25 | SIP VOTE: CONTINUE / AMEND / HALT per SIP (3/3 for CONTINUE) | LT members | Vote recorded + hashed |
| 25–30 | NEW SIPs: propose, check pre-conditions, vote to freeze | Steward proposes | SIP frozen or deferred |

5 of 6 inputs are machine-generated. The LT reads, verifies, votes.

### 2.3 Monthly Strategic Review (60 minutes)

Replaces the weekly gate on the first Monday of each month.

| Minute | Agenda Item | Output |
|---|---|---|
| 0–10 | Monthly dashboard: revenue, fleet health, costs, phase progress | Trajectory confirmed or flagged |
| 10–20 | Phase gate assessment: ADVANCE / HOLD / RETREAT | Phase decision |
| 20–35 | Strategic blockers: systemic issues | Actions assigned or SIPs proposed |
| 35–50 | 90-day horizon: trajectory if current course holds | Updated forecast |
| 50–60 | Team health: capacity, gaps, hiring | People actions captured |

---

# PART B — ESCALATION PATHS

## 3. Escalation Philosophy

A blocker not escalated is a blocker that kills silently.

- **Principle 1:** No blocker waits silently. The system escalates automatically.
- **Principle 2:** Escalation is not blame. It is asking for help.
- **Principle 3:** Every escalation produces evidence.

### 3.1 Escalation Levels

| Level | Trigger | Action | Channel | Response Expected |
|---|---|---|---|---|
| E0 | T+0 (immediate) | Auto-request to dependency owner | Slack/Signal + email | Acknowledge within 4 hours |
| E1 | T+4 hours | Auto chase. CC Steward. | Subject: [BLOCKED] + task ID | Resolution within 12 hours |
| E2 | T+12 hours | Steward direct alert with evidence + impact | Direct message from Andy | Resolution within 12 hours |
| E3 | T+24 hours | HALT. Task: BLOCKED-HUMAN. Evidence sealed. | Auto-filed in blocker log | LT decides at next gate |

> **DESIGN RULE:** The escalation ladder runs automatically. Cannot be suppressed except by Steward.

### 3.2 Escalation Message Format

```
Subject: [BLOCKED-E{level}] {task_id}: {one-line description}
What is blocked: Task {task_id} in SIP {sip_ref}: {description}
Who is blocking: {person_name} — awaiting: {specific action}
Since when: Blocked since {timestamp}. Level: E{level}.
Impact: {N} downstream tasks blocked. SIP at risk of HALT at Day {X}.
Action needed: {specific action, e.g. "Provide Gumroad API key"}
Next escalation: If unresolved by {timestamp}, advances to E{level+1}.
```

### 3.3 Escalation Types

| Type | Examples | Path |
|---|---|---|
| CREDENTIAL GATE | API keys, logins, payment access | E0 → E1 → E2 → E3. Standard ladder. |
| APPROVAL GATE | LT vote, Tier 2 approval, compliance | Surfaces at next LT gate. Emergency gate if critical. |
| INFRASTRUCTURE GATE | Server down, rate limit, storage full | Auto-detected. Immediate Andon. Fix within 4 hours. |
| SPECIFICATION GATE | Requirements unclear, design incomplete | E0 → E1 → Steward decides: build in-house or HALT. |
| EXTERNAL DEPENDENCY | Platform terms change, third-party outage | Immediate Andon. Affected tasks paused. Non-dependent continue. |

> **INVARIANT:** A credential gate that blocks a SIP after freeze is a governance failure. Credentials must be verified BEFORE freeze. If this repeats, LT must reject SIPs with unverified credentials.

---

# PART C — ANDON SYSTEM

## 4. What Is Andon

Toyota manufacturing principle: any worker pulls a cord to stop the line when they detect a quality problem. Stop. Diagnose. Fix. Restart. No defect passes downstream.

In the PIOPL enterprise: any human or agent can halt any pipeline, agent, or the entire enterprise when they detect a problem.

> **INVARIANT:** Pulling the cord is never punished. An Andon that should have been pulled but wasn't is the governance failure. False alarm cost < defect at scale cost. Always.

### 4.1 Signal Levels

| Signal | Name | Meaning | Response |
|---|---|---|---|
| **YELLOW** | ATTENTION | Something looks wrong. Not confirmed. Investigating. Production continues. | Alert to Steward + division. Investigation: 4 hours. If confirmed → ORANGE. |
| **ORANGE** | STOP LINE | Problem confirmed. Affected pipeline stops. Others continue. | Agents paused. Root cause investigation. Fix-or-halt within 12 hours. |
| **RED** | STOP EVERYTHING | Constitutional violation, evidence fabrication, systemic threat. | HALT_ALL. All agents paused. All pipelines frozen. Emergency LT gate within 4 hours. |

### 4.2 Who Can Pull

| Who | YELLOW | ORANGE | RED |
|---|---|---|---|
| Any human team member | YES | YES | YES |
| Steward (Andy) | YES | YES | YES |
| Watchtower agent (D7) | YES (auto) | YES (auto) | NO — recommends to Sentinel |
| Sentinel agent (D7) | YES (auto) | YES (auto) | YES (auto) |
| Execution agents (D1–D6) | YES (self-halt) | NO — escalate to Watchtower | NO — escalate to Watchtower |

### 4.3 Pre-Defined Triggers

**YELLOW:**
- Agent output quality below confidence floor for 3+ consecutive cycles
- Revenue variance >1.5% between ledgers
- Escalation reaching E2 without resolution
- Behaviour score entering DEGRADED range (60–79)

**ORANGE:**
- Agent attempting action outside capability token scope
- Platform terms violation detected
- Infrastructure failure affecting production
- Behaviour score entering PAUSED range (40–59)

**RED:**
- Constitutional invariant violation
- Evidence fabrication or tampering detected
- Unauthorised spend or financial irregularity
- Systemic governance failure (escalation suppressed, evidence offline, audit chain broken)

### 4.4 Response Protocol

| Step | Timing | Action | Evidence |
|---|---|---|---|
| 1 | T+0 | ACKNOWLEDGE: Confirm receipt. Identify scope. | Andon receipt log |
| 2 | T+0 to T+5min | CONTAIN: Pause affected scope. Non-affected continue. | Pause commands issued |
| 3 | T+5min to T+4hr | DIAGNOSE: Root cause. Isolated / pattern / systemic? | Root cause report |
| 4 | T+4hr to T+12hr | FIX: Implement corrective action. If needs SIP, propose at gate. | Fix description + evidence |
| 5 | After fix verified | RESTART: Resume affected pipeline. Watchtower confirms. | Restart + health check |
| 6 | Next LT gate | REVIEW: Post-mortem. Root cause analysis. Preventive action. | Post-mortem in governance record |

For RED signals: Steps 1–2 are automatic via Sentinel. Emergency LT gate within 4 hours.

### 4.5 Andon Dashboard

Real-time view generated by watchtower_agent (D7). First thing reviewed at every daily stand-up.

| Signal | Source | Description | Since | Status |
|---|---|---|---|---|
| YELLOW | reconciliation_agent | Revenue variance 2.1% on Gumroad | 2026-02-17 09:00 | INVESTIGATING |
| (CLEAR) | — | No active signals | — | ALL CLEAR |

---

## 5. How All Three Systems Connect

| Event | System Activated | Where It Surfaces |
|---|---|---|
| Task blocked by human | Escalation ladder (E0→E3) | Daily stand-up + Weekly LT gate |
| Agent quality drops | Andon YELLOW → possible ORANGE | Daily stand-up. LT gate if unresolved. |
| Constitutional violation | Andon RED → HALT_ALL → emergency gate | Emergency gate within 4 hours. |
| Escalation reaches E3 | Andon YELLOW auto-triggered | Weekly LT gate. FIX / AMEND / KILL. |
| Phase gate assessment | Monthly strategic review | Monthly replaces weekly on first Monday. |
| SIP needs voting | Weekly LT gate (SIP Vote) | SIP frozen or deferred. |

> **INVARIANT:** Every problem surfaces within 24 hours. Every problem reaches the right decision-maker. Escalation runs between meetings. Meetings are where decisions happen. Andon bypasses normal cadence for emergencies.

## 6. Constitutional Binding

- **Steward:** Attend/delegate daily stand-up. Review all E2+ escalations. Convene emergency gates within 4 hours of RED. Never suppress an escalation or punish an Andon pull.
- **LT:** Attend weekly gate. Resolve blockers. Vote on SIPs with evidence. Review Andon events. Hold monthly strategic review.
- **Machine:** Generate auto-SITREPs. Run escalation ladder automatically. Trigger Andon signals. Produce evidence for every event.
- **All Team:** Pull the cord without hesitation. Surface blockers at stand-up. Respond to escalations within timeframes.

---

| STEWARD SIGN-OFF | LT MEMBER 2 | LT MEMBER 3 |
|---|---|---|
| Andy Jones | Steven Jones | Chris Bevan |
| Date: ___________ | Date: ___________ | Date: ___________ |
| Vote: YES / NO | Vote: YES / NO | Vote: YES / NO |
