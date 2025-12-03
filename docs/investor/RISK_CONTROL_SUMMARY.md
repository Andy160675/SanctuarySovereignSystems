# Investor Risk Control Summary

**Sovereign AI System — Autonomous Agent Governance**

*Version 1.0 | December 2025*

---

## Executive Summary

This document describes how the Sovereign AI System mechanically prevents autonomous agents from executing high-risk operations without human oversight. These controls are not policy documents—they are **machine-enforced constraints** tested on every code change.

---

## The Problem We Solve

Autonomous AI agents can:
- Execute operations faster than humans can review
- Chain multiple actions before oversight catches up
- Make consequential decisions without explicit approval

**Our Solution:** Every agent action must pass through a risk gate before execution. High-risk operations are mechanically blocked.

---

## How It Works

### The Risk Gate (3 Outcomes)

Every mission is assessed by an independent **Confessor agent** before execution:

| Risk Level | System Response | Human Required |
|------------|-----------------|----------------|
| **HIGH** | Mission **REJECTED** | Cannot proceed |
| **UNKNOWN** | Mission **HELD** | Explicit authorization required |
| **LOW/MEDIUM** | Mission **APPROVED** | Proceeds automatically |

### What "Mechanically Blocked" Means

- **HIGH risk missions cannot execute** — the code physically prevents it
- There is no override flag, no admin bypass, no "just this once"
- The only path to execution is human authorization via a separate endpoint
- Every decision is logged to an immutable ledger

---

## The Control Stack

```
┌─────────────────────────────────────────────────┐
│                 MISSION REQUEST                 │
└─────────────────────┬───────────────────────────┘
                      ▼
┌─────────────────────────────────────────────────┐
│              PLANNER (Decomposes)               │
└─────────────────────┬───────────────────────────┘
                      ▼
┌─────────────────────────────────────────────────┐
│           CONFESSOR (Risk Assessment)           │
│   • Analyzes objective for risk factors         │
│   • Returns: HIGH | MEDIUM | LOW | UNKNOWN      │
└─────────────────────┬───────────────────────────┘
                      ▼
┌─────────────────────────────────────────────────┐
│              RISK GATE (Decision)               │
│   • HIGH → REJECTED (blocked)                   │
│   • UNKNOWN → PENDING_HUMAN_AUTH (held)         │
│   • LOW/MEDIUM → APPROVED (proceeds)            │
└─────────────────────┬───────────────────────────┘
                      ▼
┌─────────────────────────────────────────────────┐
│                LEDGER (Immutable)               │
│   • Every decision logged with timestamp        │
│   • Merkle hash chain for non-repudiation       │
│   • Cannot be modified after write              │
└─────────────────────────────────────────────────┘
```

---

## How We Prove It Works

### 1. Unit Tests (12 test cases)

Every code change runs tests that verify:
- HIGH risk returns REJECTED
- UNKNOWN risk returns PENDING_HUMAN_AUTH
- LOW/MEDIUM risk returns APPROVED
- Timeout defaults to PENDING_HUMAN_AUTH (fail-safe)
- All decisions produce correct ledger events

**Test Result:** 12/12 passing

### 2. CI Enforcement

Every pull request and merge triggers:
- Automated test suite execution
- Verification that HIGH risk is blocked
- Check that no execution events exist for rejected missions
- Build fails if any control is bypassed

### 3. Immutable Audit Trail

Every decision creates:
- `plan_created` — mission registered
- `risk_assessment` — Confessor's evaluation
- `plan_rejected` / `plan_approved` / `plan_hold_unknown_risk` — gate decision
- Merkle root updated for cryptographic verification

---

## Why This Matters to Investors

### Downside Protection

| Risk | Mitigation |
|------|------------|
| Rogue agent action | Mechanically blocked by risk gate |
| Audit failure | Complete ledger trail with cryptographic proof |
| Regulatory inquiry | Every decision reconstructable |
| Liability exposure | Human seal required for all high-risk ops |

### Compliance Alignment

This system is designed to meet:
- **EU AI Act Article 14** — Human oversight requirements
- **ISO/IEC 42001** — AI management system controls
- **NIST AI RMF** — GOVERN 1.3 human-AI teaming

### Operational Confidence

- No "shadow execution" possible
- No configuration that bypasses the gate
- Emergency kill-switch for immediate agent termination
- Full forensic reconstruction via Watcher service

---

## Key Numbers

| Metric | Value |
|--------|-------|
| Risk gate test coverage | 12 test cases |
| Test pass rate | 100% |
| Ledger events per decision | 3-5 |
| Time to kill all agents | < 1 second |
| Merkle verification | On every replay |

---

## The Bottom Line

**Autonomous cognition, human-sealed actuation.**

AI agents in this system can think, plan, and propose. They cannot execute high-risk operations without a human cryptographic seal. This is not a policy—it is physics.

Every commit is tested. Every decision is logged. Every high-risk path is blocked.

---

*For technical details, see:*
- `AUTONOMY_LIMITS.md` — Machine-checked constraint definitions
- `tests/planner/test_risk_gating.py` — Test implementation
- `.github/workflows/reasoning-drill.yml` — CI enforcement

*Contact: governance@precisepointway.com*
