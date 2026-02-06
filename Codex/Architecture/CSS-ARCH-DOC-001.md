# Codex Sovereign Systems — Architectural Doctrine

**Document:** CSS-ARCH-DOC-001 | **Version:** 0.1.0 | **Assembled:** 2026-02-06 13:35 UTC

*This document is mechanically assembled from tagged evidence blocks. Do not edit directly. Edit source fragments and reassemble.*

---

## Executive Summary
Codex Sovereign Systems builds constitutional AI governance — systems
where compliance is structural, not behavioural. The architecture
enforces rules that cannot be broken, produces evidence that cannot be
forged, and halts rather than operating outside verified parameters.

## Constitutional Principles

### Prevention Over Detection
Constitutional systems make violations impossible, not just detectable.
Prevention is enforced structurally — not through monitoring, alerts, or
post-hoc audit. If a rule can be broken, it is not constitutional.

### Prefer Stopping to Lying
Sovereign systems prefer stopping to lying. When integrity cannot be
verified, the system halts rather than producing unverified output.
Silence is safer than confabulation.

### Append-Only Evidence
Evidence is append-only. No fragment, log entry, or audit record may be
modified after capture. New evidence supersedes old evidence; it does not
replace it. The full history is always preserved.

## Enforcement Architecture

### Three-Layer Enforcement Model
Enforcement operates at three layers: structural constraints (what the
system cannot do), runtime validation (what the system checks before
acting), and audit trails (what the system records after acting). All
three layers must agree. Disagreement triggers halt.

### Trust Model
Trust is structural, not reputational. Systems do not trust agents
because they have behaved well — they trust agents because the
architecture makes misbehaviour impossible within scope. Trust boundaries
are enforced, not assumed.

## Governance

### BOARDROOM-13 Deliberation Chamber
BOARDROOM-13 implements a 13-agent deliberation chamber. No single agent
holds unilateral authority. Decisions require constitutional quorum.
Dissenting opinions are recorded, not suppressed. The chamber's output
is the decision plus its full deliberation trace.

## Infrastructure

### Distributed Mesh Architecture
The Sovereign Stack operates as a distributed mesh across geographic
nodes connected via Tailscale. Node-0 (UK) and Node-1 (Tenerife)
maintain independent operational capability. Neither node is a single
point of failure. Sovereignty requires redundancy.

### Offline-First Sovereignty
Sovereign systems must operate without external dependencies. Cloud
services are convenience layers, not requirements. If network
connectivity fails, the system continues operating on local
infrastructure. Sovereignty means no landlord.

## Audit and Verification

### Cryptographic Audit Chain
Every action produces a cryptographically timestamped record. Audit
chains use RFC-3161 timestamps and hash-linked sequences. Any break in
the chain is detectable. The audit trail is the system's memory — it
cannot be edited, only extended.

