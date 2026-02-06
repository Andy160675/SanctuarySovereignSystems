@block id=arch.principle.001 domain=ARCH type=definition weight=canonical
Constitutional systems make violations impossible, not just detectable.
Prevention is enforced structurally — not through monitoring, alerts, or
post-hoc audit. If a rule can be broken, it is not constitutional.
@end

@block id=arch.principle.002 domain=ARCH type=definition weight=canonical
Sovereign systems prefer stopping to lying. When integrity cannot be
verified, the system halts rather than producing unverified output.
Silence is safer than confabulation.
@end

@block id=arch.principle.003 domain=ARCH type=definition weight=canonical
Evidence is append-only. No fragment, log entry, or audit record may be
modified after capture. New evidence supersedes old evidence; it does not
replace it. The full history is always preserved.
@end

@block id=arch.enforcement.model domain=ARCH type=definition weight=canonical
Enforcement operates at three layers: structural constraints (what the
system cannot do), runtime validation (what the system checks before
acting), and audit trails (what the system records after acting). All
three layers must agree. Disagreement triggers halt.
@end

@block id=arch.governance.chamber domain=ARCH type=definition weight=canonical
BOARDROOM-13 implements a 13-agent deliberation chamber. No single agent
holds unilateral authority. Decisions require constitutional quorum.
Dissenting opinions are recorded, not suppressed. The chamber's output
is the decision plus its full deliberation trace.
@end

@block id=arch.infrastructure.mesh domain=ARCH type=definition weight=canonical
The Sovereign Stack operates as a distributed mesh across geographic
nodes connected via Tailscale. Node-0 (UK) and Node-1 (Tenerife)
maintain independent operational capability. Neither node is a single
point of failure. Sovereignty requires redundancy.
@end

@block id=arch.trust.model domain=ARCH type=definition weight=canonical
Trust is structural, not reputational. Systems do not trust agents
because they have behaved well — they trust agents because the
architecture makes misbehaviour impossible within scope. Trust boundaries
are enforced, not assumed.
@end

@block id=arch.audit.chain domain=ARCH type=definition weight=canonical
Every action produces a cryptographically timestamped record. Audit
chains use RFC-3161 timestamps and hash-linked sequences. Any break in
the chain is detectable. The audit trail is the system's memory — it
cannot be edited, only extended.
@end

@block id=arch.offline.first domain=ARCH type=definition weight=canonical
Sovereign systems must operate without external dependencies. Cloud
services are convenience layers, not requirements. If network
connectivity fails, the system continues operating on local
infrastructure. Sovereignty means no landlord.
@end

@block id=arch.summary.executive domain=ARCH type=summary weight=canonical
Codex Sovereign Systems builds constitutional AI governance — systems
where compliance is structural, not behavioural. The architecture
enforces rules that cannot be broken, produces evidence that cannot be
forged, and halts rather than operating outside verified parameters.
@end
