# CSS-OPS-TRACK-001 — Immediate Actions Tracker

**CONTROLLED DOCUMENT — DO NOT PRINT**

| Field | Value |
|---|---|
| Document Reference | CSS-OPS-TRACK-001 |
| Version | 1.0 |
| Classification | INTERNAL — ALL TEAM |
| Author | Andy Jones, Steward |
| Date | 17 February 2026 |
| Derives From | CSS-OPS-DOC-002 (Master Build Plan), CSS-OPS-DOC-003 (SIP Engine), CSS-OPS-DOC-004 (Agent Deployment) |
| Review Cadence | **Daily at 12:30 UK stand-up** |
| Distribution | Andy (FULL), Steven (FULL), Chris Bevan (FULL), Tom Maher (FULL), Blue (TASK VISIBILITY) |

---

## Purpose

Single-source execution tracker across all five operational tracks. Reviewed daily at stand-up. Updated by task owners. Status changes produce evidence.

> **INVARIANT:** Every action has an owner, a deadline, and a status. No action exists without all three. Status must be one of: ✅ Done, ⏳ Due, 🔴 Blocked, ❌ Missed.

---

## TRACK 1: BUILD PLAN EXECUTION (CSS-OPS-DOC-002)

| # | Action | Owner | Deadline | Status |
|---|--------|-------|----------|--------|
| 1.1 | Send Blue credentials + CSS-OPS-DOC-003 | Steven | 17 Feb | ✅ Done |
| 1.2 | Verify n8n trend scanner runs | Andy | 17 Feb | ✅ Done |
| 1.3 | Confirm Gumroad/Etsy accounts active | Andy/Steven | 17 Feb | ⏳ **Due today** |
| 1.4 | Post Tenerife operator job spec | Chris | 18 Feb | ⏳ Due tomorrow |
| 1.5 | Schedule Monday check-in with Blue | Steven | 18 Feb | ⏳ Due tomorrow |
| 1.6 | Blue runs Monday routine | Blue | 24 Feb | ⏳ Next week |
| 1.7 | First product listed | System | 24 Feb | ⏳ Next week |

**Critical path:** 1.3 gates 1.7. No product listing without confirmed marketplace accounts.

---

## TRACK 2: SOVEREIGN COMMAND DECK (CSS-DECK-001)

| # | Action | Owner | Deadline | Status |
|---|--------|-------|----------|--------|
| 2.1 | Create Notion/Google Sheets template from spec | Steven | 18 Feb | ⏳ Due tomorrow |
| 2.2 | Share with Blue (edit), Andy/Chris/Josh (view) | Steven | 18 Feb | ⏳ Due tomorrow |
| 2.3 | Blue enters first weekly entry | Blue | 23 Feb | ⏳ Next week |
| 2.4 | Steven reviews and stores in Tresorit | Steven | 24 Feb | ⏳ Next week |

**Critical path:** 2.1 gates 2.3. No deck entries without template.

---

## TRACK 3: PIOPL AGENT DEPLOYMENT (CSS-OPS-DOC-004)

| # | Action | Owner | Deadline | Status |
|---|--------|-------|----------|--------|
| 3.1 | Build agent registry database (PostgreSQL on Node-0) | Tom | 1 Mar | ⏳ Not started |
| 3.2 | Extend SIP engine to support agent profiles | Andy + Claude | 15 Mar | ⏳ Not started |
| 3.3 | Create first agent template (Digital Product Generator) | Andy | 15 Mar | ⏳ Not started |
| 3.4 | Deploy first 10 agents manually to test pipeline | Tom | 1 Apr | ⏳ Not started |
| 3.5 | Set up agent revenue ledger (Stripe Connect) | Steven | 1 Apr | ⏳ Not started |
| 3.6 | Scale to 100 agents after validation | Tom + Blue | 1 May | ⏳ Not started |

**Critical path:** 3.1 → 3.2 → 3.3 → 3.4 (sequential). 3.5 parallel to 3.1–3.4 but gates 3.6.

**Dependency:** Track 1 (payment rails) must be complete before 3.5 can begin.

---

## TRACK 4: NODE-1 PHYSICAL SOVEREIGNTY

| # | Action | Owner | Deadline | Status |
|---|--------|-------|----------|--------|
| 4.1 | ZEC company registration | Steven | 1 Mar | ⏳ Not started |
| 4.2 | RIC investment reserve setup | Steven | 1 Mar | ⏳ Not started |
| 4.3 | Hardware order (MVP €26k config) | Andy/Steven | 5 Mar | ⏳ Not started |
| 4.4 | Colo reservation (D-ALiX or Civicos) | Chris | 5 Mar | ⏳ Not started |
| 4.5 | Tenerife operator start date | Chris | 24 Feb | ⏳ Next week |

**Critical path:** 4.1 + 4.2 gate 4.3. 4.5 gates operational readiness.

---

## TRACK 5: ENTERPRISE INSTANT READINESS (CSS-OPS-DOC-003)

| # | Action | Owner | Deadline | Status |
|---|--------|-------|----------|--------|
| 5.1 | Document frozen as canonical | Andy | 16 Feb | ✅ Done |
| 5.2 | Next profile test (e.g., "scale test 1,000 hires") | Optional | TBD | ⏳ On hold |
| 5.3 | Integrate with Node-1 for audit mirroring | Tom | Post-Node-1 | ⏳ Future |

---

## 48-HOUR WINDOW — ACTIONS DUE BY 19 FEBRUARY 2026

| # | Action | Owner | Due | Escalation Trigger |
|---|--------|-------|-----|-------------------|
| 1.3 | Confirm Gumroad/Etsy accounts active | Andy/Steven | 17 Feb (today) | E1 at 21 Feb if unresolved |
| 1.4 | Post Tenerife operator job spec | Chris | 18 Feb | E1 at 22 Feb if unresolved |
| 1.5 | Schedule Monday check-in with Blue | Steven | 18 Feb | E1 at 22 Feb if unresolved |
| 2.1 | Create Command Deck template | Steven | 18 Feb | E1 at 22 Feb if unresolved |
| 2.2 | Share Command Deck with team | Steven | 18 Feb | E1 at 22 Feb if unresolved |

> **PATTERN:** 4 of 5 actions in the 48-hour window are Steven dependencies. If these slip, escalation ladder from CSS-OPS-DOC-006 activates automatically.

---

## CROSS-TRACK DEPENDENCIES

```
TRACK 1 (Payment Rails)
    └── 1.3 (Gumroad/Etsy) ──gates──► 1.7 (First product listed)
                                           │
                                           └──gates──► TRACK 3.5 (Revenue ledger)
                                                            │
                                                            └──gates──► TRACK 3.6 (Scale to 100)

TRACK 2 (Command Deck)
    └── 2.1 (Template) ──gates──► 2.3 (First entry) ──gates──► Operational visibility

TRACK 4 (Node-1)
    └── 4.1 + 4.2 (Entity + Reserve) ──gates──► 4.3 (Hardware) ──gates──► 4.5 (Operator)
```

---

## UPDATE RULES

1. Status updates at daily stand-up (12:30 UK)
2. Owner updates their own actions — no proxy updates
3. Missed deadlines auto-trigger escalation per CSS-OPS-DOC-006
4. New actions require Steward approval and track assignment
5. Completed actions remain visible with ✅ for audit trail
6. This document is version-controlled in git — every update is a commit

---

| STEWARD SIGN-OFF |
|---|
| Andy Jones |
| Date: 17 February 2026 |
