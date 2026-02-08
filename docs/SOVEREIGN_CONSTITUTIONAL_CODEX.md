# The Sovereign Constitutional Codex

**Version:** 1.0
**Status:** Ratified
**Classification:** Foundational Law

---

## Preamble: The Invariant Remainder

This Codex is founded upon the principle of **Subtractive Invariance**. It posits that a system achieves stability, resilience, and sovereignty not by accumulating features, but by eliminating impossibilities. The constitution of this system is therefore defined by what cannot be, and the core architecture is the mechanism that enforces these impossibilities.

> A system becomes real when its invariants are written down in a way that a builder can't accidentally violate them. The machine is what remains when everything that can fail has been removed.

This document is the mechanical specification of that remainder. It is not a guide; it is the law.

---

## Layer 0: The Axioms of Sovereignty

These are the three non-negotiable truths upon which the entire system rests. A violation of these axioms is not an error; it is a cessation of the system's existence. The kernel's primary function is to make their violation impossible.

### Axiom I: Evidence is Immutable

All state transitions, decisions, and observations are recorded in an append-only, hash-chained ledger. The past cannot be altered, deleted, or repudiated. The system's memory is absolute and verifiable.

### Axiom II: Ambiguity Resolves to Containment

Any state, signal, or command that is ambiguous, undefined, or outside the explicit authority of the actor is resolved to a state of **halt**. The system will not guess, infer, or fall through to a permissive state. In the absence of certainty, the system chooses safety and containment over action.

### Axiom III: Illegality is Unrepresentable

The system shall not possess the capacity to represent or execute a state that violates its own constitutional laws or the external legal and compliance frameworks to which it is bound. Compliance is not a check; it is a structural boundary. An illegal state is a logical impossibility, not a failed operation.

---

## Layer 1: The Six Invariants of Governance

These six industry-agnostic invariants are the pillars of governance that manifest from the Axioms. They are true for all domains of operation, from finance to defence, and are enforced by the Constitutional Kernel.

| Invariant | Question It Answers |
|---|---|
| **1. Authority** | Who is allowed to decide? Under what conditions? With what checks? |
| **2. Accountability** | Who is responsible when something goes wrong? Can this be proven immutably? |
| **3. Evidence** | What happened and when? Can it be independently and cryptographically verified? |
| **4. Risk Containment** | What could go wrong? What prevents the worst-case outcome? |
| **5. Override & Intervention** | How do humans intervene? Who can stop the system, and what is the proof? |
| **6. Change Control** | What changes over time? Who approved it? Can systemic drift be detected and audited? |

---

## Layer 2: The Constitutional Kernel (Season 2 Architecture)

This is the mechanical implementation of the Axioms and Invariants — the constitutional plumbing. These nine articles define a system that cannot misroute decisions, even if it is not yet intelligent. Each article enforces an impossibility.

### Article I: The Typed Signal Ontology
All information flowing through the system is a **Typed Signal**. A signal without a type is noise and is discarded. Each type maps to a non-negotiable Level and Authority (`Signal → Type → Level → Authority`). This makes implicit or untyped routing impossible.

### Article II: The Hierarchical Router
Routing is an act of **jurisdiction**, not optimization. The router guarantees that signals are first processed by the lowest competent authority. Escalation is deterministic and follows the protocol defined in Article V. This makes jurisdictional leakage and heuristic routing impossible.

### Article III: The Legality Lane
Before any inference or execution, all signals pass through a **Legality Lane**. This guard stops domain violations, undefined operations, and constitutional singularities. This makes the downstream representation of an illegal state impossible.

### Article IV: The Authority Separation Model
System actors are separated into three non-overlapping roles: **Operator, Innovator, and Steward**. Each role owns specific classes of decisions and cannot overwrite the authority of another. This makes mode bleed and silent overwrites impossible.

### Article V: The Escalation Protocol
Escalation is not ad-hoc. The system state dictates the routing path: `stable → operator`, `degraded → innovator`, `constitutional → steward`. This makes intuitive or arbitrary escalation impossible.

### Article VI: The Minimal Feedback Log
Every action is logged as a minimal, atomic record: `type → route → handler → outcome`. This is the seed of observability. This makes un-auditable actions impossible.

### Article VII: The Pathology Detection Hooks
Anomaly markers, edge-case triggers, and boundary flags are embedded in the kernel. They do not act, but they observe and signal when a state approaches a defined pathology. This allows the Escalation Protocol to activate correctly and makes systemic blindness impossible.

### Article VIII: The Jurisdiction Context Switcher
All operations are tagged with a **Jurisdiction Context** (e.g., `math`, `policy`, `execution`). Tools and reasoning from one context cannot be applied to another without an explicit and authorized context switch. This makes cross-domain contamination impossible.

### Article IX: The Default Safe Failure State
Any component or process that fails does so in a **halt** state. There is no silent fall-through. The system prefers inaction to incorrect action. This makes ambiguous or unsafe failure modes impossible.

---

## Layer 3: The Adaptive Interface (Season 3 Bolt-Ons)

This layer defines the sanctioned interfaces through which adaptive intelligence may be connected to the Constitutional Kernel. These are not features; they are controlled extension points that are structurally incapable of violating the lower layers.

| Interface | Function | Constraint |
|---|---|---|
| **Learnable Routing** | Optimises routing patterns based on historical data. | Cannot override the Hierarchical Router's jurisdictional rules. |
| **Glyph-Chain Immutability** | Introduces advanced cryptographic proof methods. | Cannot alter the core append-only nature of the Evidence axiom. |
| **Meta-Governance Evolution** | Allows for the evolution of policies via governed process. | Cannot amend the Axioms or Invariants without a Phoenix Protocol event. |
| **Simulation Sandbox** | Provides a space to test new logic or policies. | Is read-only with respect to the production kernel; cannot write to the live ledger. |
| **Adaptive Trainers** | Fine-tunes handlers and models. | Operates only within the jurisdiction defined for its associated handler. |
| **Surgical Rollback** | Automates the reversal of specific, authorised actions. | Can only be triggered by the Judgment Circle and leaves an immutable record. |

---

## Enforcement & Ratification

Violation of this Codex is enforced by the kernel itself. Any operation that conflicts with Layers 0, 1, or 2 will trigger one of the following non-negotiable responses:

| Response | Trigger | Effect |
|----------|---------|--------|
| `process_block` | Gate bypass attempt | Operation halted |
| `transaction_hold` | Authority violation | Held in escrow |
| `kernel_panic` | Axiom violation | System-wide halt |

This Codex is hereby **SEALED** and serves as the single source of truth for the system's architecture and governance. It is the machine that holds.

**Auth Code:** `CODEX-V1-SUBTRACTIVE-INVARIANCE`
