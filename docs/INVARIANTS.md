# The 7 Kernel Invariants

These invariants are the constitutional foundation of the Sovereign Recursion Engine. They are enforced architecturally — not by convention, not by code review, but by the structure of the system itself.

No contribution, extension, archetype, or constitutional amendment may violate these invariants.

---

## 1. Halt Doctrine

**Statement:** When the system encounters ambiguity, unknown failure, or unresolvable state, it halts. It does not guess. It does not proceed silently.

**Enforcement:**
- Halt rule is FIRST in routing grammar (preempts all other rules)
- Unknown failure types map to halt in the failure matrix
- Halted signal bus only accepts halt signals
- Router returns halt on no matching rule

**Test coverage:** 12 tests across Phases 0, 2, 5, 6, 8

---

## 2. Authority Separation

**Statement:** Three authority tiers exist — operator, innovator, steward — with strict separation. No component may invoke a handler outside its jurisdiction without routing through the authority ladder.

**Enforcement:**
- Legality gate blocks `cross_authority_direct_call` (forbidden state)
- Router checks handler jurisdiction before dispatch
- Authority handlers have explicit domain sets
- Escalation follows the ladder — never skips levels

**Test coverage:** 8 tests across Phases 2, 3, 8

---

## 3. Legality Gate

**Statement:** All structurally illegal states are eliminated before routing. Every termination produces a containment event for audit.

**Enforcement:**
- Legality gate runs BEFORE the router in the pipeline
- Checks: schema validation, integrity verification, forbidden state matching, custom rules
- Terminated signals never reach a handler
- Every termination generates a containment event written to the audit ledger

**Test coverage:** 9 tests in Phase 3, plus integration tests in Phase 8

---

## 4. Audit Chain

**Statement:** Every state transition is recorded in an append-only, SHA-256 hash-chained ledger. The chain is validated at boot. Corruption triggers truncation to the last valid entry.

**Enforcement:**
- Genesis hash: 64 zeros
- Each entry's hash computed over (index, record, timestamp, previousHash)
- `verify()` validates entire chain from genesis
- Boot validation required before routing can begin
- Corrupted entries truncated; if unrecoverable, ledger is sealed (no further writes)

**Test coverage:** 6 tests in Phase 4, plus integration tests in Phase 8

---

## 5. Escalation Protocol

**Statement:** When a handler cannot process a signal, it escalates up the authority ladder: operator → innovator → steward. If all levels are exhausted, the system halts.

**Enforcement:**
- Router walks the authority ladder on jurisdiction mismatch or inactive handler
- Each escalation level is tried exactly once
- Exhausted escalation triggers halt (not silent drop)
- Escalation without source is a forbidden state (legality gate blocks it)

**Test coverage:** 5 tests across Phases 2, 3, 8

---

## 6. Default Safe Failure

**Statement:** Every failure type has a prescribed constitutional response. No failure is silent. Unknown failures default to halt.

**Enforcement:**
- Failure matrix maps (component, failure_type) → response
- Constitutional responses: halt, escalate+contain, contain
- Unknown failure types → halt (fail-safe default)
- Health monitor tracks component health and auto-escalates on repeated failures

**Test coverage:** 4 tests in Phase 6, plus adversarial tests

---

## 7. Extension Boundary

**Statement:** Season-3 extensions cannot modify the halt doctrine, authority ladder, or audit requirements. All extensions must pass compliance validation before activation.

**Enforcement:**
- Extension manifest declares reads, writes, authority requirements
- Compliance gate checks manifest against kernel invariants
- Non-compliant extensions cannot activate
- Extensions operate under declared authority level only

**Test coverage:** 5 tests in Phase 9

---

## Verification

Run the full invariant test suite:

```bash
python -m sovereign-engine.tests.run_all
```

Expected result: **74/74 tests passing.**

If any test fails, the invariant it covers is violated. Do not deploy, do not merge, do not proceed until all 74 pass.
