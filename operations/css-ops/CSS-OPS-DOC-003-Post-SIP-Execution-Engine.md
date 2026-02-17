# CSS-OPS-DOC-003 — Post-SIP Autonomous Execution Engine

**CONTROLLED DOCUMENT — DO NOT PRINT**

| Field | Value |
|---|---|
| Document Reference | CSS-OPS-DOC-003 |
| Version | 1.0 DRAFT — FOR LT REVIEW |
| Classification | INTERNAL — LT DISTRIBUTION ONLY |
| Author | Andy Jones, Steward |
| Date | 16 February 2026 |
| Derives From | CSS-GOV-DOC-002 (Governance Framework) |
| Constitutional Weight | **BINDING — Post LT Buy-Off** |
| Distribution | Andy (FULL), Steven (FULL), Chris Bevan (GOV/OPS), Tom Maher (ROLLOUT) |

---

## 1. Core Principle

Once a Strategic Intent Plan (SIP) is frozen and bought off by 3 LT members, no human is required for execution until the next gate. The machine runs. Humans review at gates. Any mid-cycle human intervention is a design failure requiring logging, escalation, and patching.

> **INVARIANT:** A frozen SIP executes autonomously. Humans intervene only at gates. Mid-cycle human dependency = incident, not workaround.

## 2. SIP Lifecycle — Four Phases

| Phase | Name | Mode | Description |
|---|---|---|---|
| 1 | SIP FORMATION | Human | Intent defined, scope locked, LT votes 3/3, plan hashed and timestamped |
| 2 | DECOMPOSITION | Machine | Auto-decomposes to atomic tasks with agent owners, deadlines, evidence requirements |
| 3 | EXECUTION | Machine | Agents execute, Watchtower monitors drift, Sentinel enforces hard stops |
| 4 | GATE REVIEW | Human | LT reviews evidence/drift/completion, votes CONTINUE/AMEND/HALT |

## 3. Freeze Gates — 5/25/90 Day Horizons

| Horizon | Use | Gate Frequency |
|---|---|---|
| 5-day | Tactical sprint, single deliverable | Gate at Day 5 |
| 25-day | Operational cycle | Weekly LT gates |
| 90-day | Strategic programme | Weekly gates + monthly deep review |

> **INVARIANT:** No SIP runs >7 days without gate. No gate without evidence. No evidence without hash verification.

## 4. Atomic Task Schema — 9 Required Fields

| Field | Description |
|---|---|
| task_id | Unique identifier |
| sip_ref | Parent SIP reference |
| description | Verb + object + target |
| agent_owner | Never a person — always an agent |
| deadline | ISO 8601 timestamp |
| evidence_required | What proves completion |
| depends_on | Upstream task IDs |
| failure_mode | What happens if task fails |
| human_dependency | If TRUE = design flaw, must specify escalation ladder + HALT condition |

## 5. Execution Stack — 5 Layers

| Layer | Name | Function |
|---|---|---|
| L0 | STEWARD | Forms SIPs, votes at gates only |
| L1 | DECOMPOSER | Breaks SIP to atomic tasks, validates schema, assigns agents |
| L2 | AGENT FLEET | Executes tasks, produces evidence, reports status, never waits silently |
| L3 | WATCHTOWER (DDT) | Monitors drift/scope creep, 26 detectors operational |
| L4 | SENTINEL | Hard stops on violations, issues HALT_ALL, logs evidence, waits for gate |

## 6. Human Touchpoints — Exactly Four

| # | Touchpoint | When |
|---|---|---|
| 1 | SIP Formation Vote | Weekly standup, 3/3 LT required |
| 2 | Weekly Gate Review | SITREP + evidence + drift, vote CONTINUE/AMEND/HALT |
| 3 | HALT Resolution | Steward decides FIX/AMEND/KILL at next gate |
| 4 | Credential/Auth | ONE-TIME provision BEFORE SIP freeze |

**KEY:** Touchpoint 4 makes credentials a freeze PRE-CONDITION. "Steven hasn't sent credentials" is no longer valid status. No credentials = no frozen SIP = no execution begins.

## 7. Escalation Ladder

| Time | Action | Channel |
|---|---|---|
| T+0 | Automated request to dependency owner | Slack/email |
| T+4h | Automated chase, CC Steward, subject [BLOCKED] | Email with evidence |
| T+12h | Steward direct alert with evidence + impact | Direct message |
| T+24h | HALT with cause, task BLOCKED-HUMAN, evidence sealed | Auto-filed, awaits gate |

> **INVARIANT:** Ladder runs automatically, cannot be suppressed, evidence is immutable.

## 8. Evidence Requirements — 6 Task Types

| Type | Required Evidence |
|---|---|
| Deployment | HTTP 200 + screenshot + log, SHA-256 verified |
| Code | Git commit hash + passing tests |
| Document | File hash + word count + storage location |
| Financial | Transaction ID + amount + counterparty + dual-signature |
| Communication | Message hash + delivery receipt |
| Account setup | Account ID + platform + access verification |

## 9. Weekly LT Gate Protocol — 30 Minutes Max

| Minute | Agenda |
|---|---|
| 0–5 | Auto-SITREP (machine-generated, facts only) |
| 5–10 | Blockers (HALT-HUMAN-DEPENDENCY reviewed first) |
| 10–15 | Drift (Watchtower DDT report) |
| 15–20 | Evidence (completed tasks verified or rejected) |
| 20–25 | Vote (per SIP: CONTINUE/AMEND/HALT, 3/3 required) |
| 25–30 | New SIPs (propose for next cycle) |

5 of 6 inputs are machine-generated. LT reads, verifies, votes — not produces/chases/manages.

## 10. Failure Modes

| Scenario | Response |
|---|---|
| Agent cannot complete | BLOCKED, pipeline continues on non-dependent tasks |
| Human dependency unmet | Escalation ladder → HALT at T+24h |
| Scope creep | DDT flags, Sentinel halts if HIGH severity |
| Evidence fabrication | HALT_ALL, agent decommissioned, forensic audit |
| LT member unresponsive | Quorum 2/3 = CONTINUE only, no quorum = auto-CONTINUE 7 days |
| Infrastructure failure | Affected tasks BLOCKED, healthy branches continue |
| SIP wrong | Cannot change mid-cycle, execute to gate, then AMEND/KILL |

## 11. What This Kills

| Anti-Pattern | How It Dies |
|---|---|
| "Steven hasn't sent credentials" | Credentials are freeze pre-condition |
| "Chris hasn't posted spec" | Spec is atomic task with agent owner |
| "Waiting for someone" | System executes/blocks/halts, never waits silently |
| "I thought it was done" | sovereign_gate.py rejects without evidence |
| "Need to discuss more" | Discussion at Phase 1 or 4, never mid-execution |
| "Plan changed" | Frozen plans complete/amend at gate/kill, no mid-cycle mutations |
| "Massive architecture, zero revenue" | 5-day SIPs with revenue as success criterion |

## 12. Implementation — 4 Immediate Actions

1. LT reviews/votes CSS-OPS-DOC-003 at next standup (3/3 YES required)
2. First SIP drafted: "Revenue Pipeline Live — 5-Day Sprint" with all pre-conditions verified BEFORE freeze
3. Decomposition Engine produces atomic task list, human_dependency field populated, TRUE values trigger pre-freeze resolution
4. Execution begins, first auto-SITREP at T+24h, gate at Day 5

> **INVARIANT:** First SIP must produce revenue or evidence toward revenue. Architecture-only SIPs prohibited for first 25-day cycle.

## 13. Constitutional Binding

- **Steward:** Forms SIPs correctly, ensures pre-conditions met, reviews at gates, no mid-cycle intervention
- **LT:** Votes on evidence not narrative, holds accountability for touchpoint failures
- **Machine:** Executes without invention, halts without hiding, produces evidence without fabrication

Amendments require new SIP, LT vote, version increment. No mid-cycle amendments.

---

| STEWARD SIGN-OFF | LT MEMBER 2 | LT MEMBER 3 |
|---|---|---|
| Andy Jones | Steven Jones | Chris Bevan |
| Date: ___________ | Date: ___________ | Date: ___________ |
| Vote: YES / NO | Vote: YES / NO | Vote: YES / NO |
