@block id=arch.autonomous.agents domain=ARCH type=doctrine weight=proposed
Scripts are agents; autonomy must be bounded. Every autonomous action must be: deterministic entry → bounded execution → evidenced exit. Autonomy is not the problem — unbounded state transition is.
@end

@block id=arch.cascade.failure domain=ARCH type=doctrine weight=proposed
Gate failure = containment trigger, not continuation signal. Cascade failure patterns (gate bypass, retry storms, runaway loops) must be met with preflight validation, hard abort on invariant breach, and evidence capture before exit.
@end

@block id=arch.invisible.scaffolding domain=ARCH type=doctrine weight=proposed
Governance infrastructure is dark matter. Visible success without structural integrity (invariant checks, evidence capture, rollback snapshotting) is an illusion. Scaffolding preserves system coherence over time.
@end

@block id=arch.autonomy.calibration domain=ARCH type=doctrine weight=proposed
Attractor calibration: Over-constrained systems decay into operator fatigue; under-constrained systems drift into substrate corruption. The stability basin is engineered through hard invariant boundaries with automatic evidence capture and deterministic abort paths.
@end
