"""
Constitutional Compliance Test Suite
======================================
Validates all 9 Articles of the Season 2 Codex.
Every test enforces an impossibility — if it passes,
the system cannot represent the violation.

PDCA Check Phase: This IS the check.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from engine.signals.typed_signal import (
    TypedSignal, SignalType, AuthorityLevel, SystemState,
    SIGNAL_AUTHORITY_MAP, create_signal,
)
from engine.feedback.feedback_log import FeedbackLog, LogEntry
from kernel.legality.legality_lane import LegalityLane
from kernel.router.hierarchical_router import HierarchicalRouter, RouteResult
from kernel.escalation.escalation_protocol import EscalationProtocol
from kernel.context.jurisdiction_context import JurisdictionContext
from kernel.failure.safe_failure import SafeFailure, FailureClass
from engine.pathology.pathology_detector import PathologyDetector


class TestResults:
    """Accumulator for test results."""
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.results = []

    def check(self, name: str, condition: bool, detail: str = ""):
        status = "PASS" if condition else "FAIL"
        self.results.append(f"  [{status}] {name}" + (f" — {detail}" if detail else ""))
        if condition:
            self.passed += 1
        else:
            self.failed += 1


def run_compliance_suite() -> tuple[bool, str]:
    """Execute the full constitutional compliance suite."""
    t = TestResults()
    log = FeedbackLog()

    # ═══════════════════════════════════════════════════
    # ARTICLE I: Typed Signal Ontology
    # ═══════════════════════════════════════════════════
    print("\n═══ ARTICLE I: Typed Signal Ontology ═══")

    # Test: All signal types have authority mappings
    for st in SignalType:
        t.check(
            f"Art.I — {st.name} has authority mapping",
            st in SIGNAL_AUTHORITY_MAP,
        )

    # Test: Signals are immutable (frozen dataclass)
    sig = create_signal(SignalType.STATE_CHECK, AuthorityLevel.OPERATOR, "audit", {"test": True}, "test_operator")
    try:
        sig.payload = {"tampered": True}
        t.check("Art.I — Signal immutability", False, "mutation allowed")
    except (AttributeError, TypeError):
        t.check("Art.I — Signal immutability", True)

    # Test: Evidence hash is computed
    t.check("Art.I — Evidence hash computed", len(sig.evidence_hash) == 64)

    # ═══════════════════════════════════════════════════
    # ARTICLE II: Hierarchical Router
    # ═══════════════════════════════════════════════════
    print("\n═══ ARTICLE II: Hierarchical Router ═══")

    lane = LegalityLane()
    router = HierarchicalRouter(lane, log, SystemState.STABLE)

    # Test: Unhandled signal → containment (not silent pass)
    sig_unhandled = create_signal(SignalType.STATE_CHECK, AuthorityLevel.OPERATOR, "audit", {"x": 1}, "test_op")
    result = router.route(sig_unhandled)
    t.check("Art.II — Unhandled signal → containment", not result.accepted)
    t.check("Art.II — Containment reason logged", "transaction_hold" in result.reason)

    # Test: Registered handler receives signal
    handled = []
    router.register_handler(AuthorityLevel.OPERATOR, "state_check", lambda s: handled.append(s))
    sig_handled = create_signal(SignalType.STATE_CHECK, AuthorityLevel.OPERATOR, "audit", {"x": 1}, "test_op")
    result2 = router.route(sig_handled)
    t.check("Art.II — Registered handler receives signal", result2.accepted)
    t.check("Art.II — Handler actually executed", len(handled) == 1)

    # ═══════════════════════════════════════════════════
    # ARTICLE III: Legality Lane
    # ═══════════════════════════════════════════════════
    print("\n═══ ARTICLE III: Legality Lane ═══")

    # Test: Insufficient authority → blocked
    bad_sig = create_signal(SignalType.OVERRIDE, AuthorityLevel.OPERATOR, "audit", {"x": 1}, "test_op")
    t.check("Art.III — Insufficient authority → None (unrepresentable)", bad_sig is None)

    # Test: Unknown source → blocked
    anon_sig = TypedSignal(
        signal_type=SignalType.STATE_CHECK,
        authority=AuthorityLevel.OPERATOR,
        jurisdiction="audit",
        payload={"x": 1},
        source="unknown",
    )
    anon_result = lane.check(anon_sig)
    t.check("Art.III — Anonymous source → blocked", not anon_result.passed)

    # Test: Empty jurisdiction → blocked
    no_juris = TypedSignal(
        signal_type=SignalType.STATE_CHECK,
        authority=AuthorityLevel.OPERATOR,
        jurisdiction="",
        payload={"x": 1},
        source="test_op",
    )
    juris_result = lane.check(no_juris)
    t.check("Art.III — Empty jurisdiction → blocked", not juris_result.passed)

    # ═══════════════════════════════════════════════════
    # ARTICLE IV: Authority Separation Model
    # ═══════════════════════════════════════════════════
    print("\n═══ ARTICLE IV: Authority Separation Model ═══")

    # Test: Three distinct authority levels exist
    t.check("Art.IV — Three authority levels", len(AuthorityLevel) == 3)
    t.check("Art.IV — OPERATOR exists", AuthorityLevel.OPERATOR.value == "operator")
    t.check("Art.IV — INNOVATOR exists", AuthorityLevel.INNOVATOR.value == "innovator")
    t.check("Art.IV — STEWARD exists", AuthorityLevel.STEWARD.value == "steward")

    # Test: Operator cannot execute Steward signals
    steward_sig = create_signal(SignalType.SYSTEM_HALT, AuthorityLevel.OPERATOR, "audit", {"x": 1}, "test_op")
    t.check("Art.IV — Operator cannot create SYSTEM_HALT signal", steward_sig is None)

    # ═══════════════════════════════════════════════════
    # ARTICLE V: Escalation Protocol
    # ═══════════════════════════════════════════════════
    print("\n═══ ARTICLE V: Escalation Protocol ═══")

    esc_log = FeedbackLog()
    esc = EscalationProtocol(esc_log)
    trigger = create_signal(SignalType.STATE_CHECK, AuthorityLevel.OPERATOR, "audit", {"esc": True}, "test_op")

    # Test: Valid escalation stable → degraded
    d1 = esc.escalate(SystemState.DEGRADED, trigger, "test escalation")
    t.check("Art.V — stable → degraded valid", d1.to_state == SystemState.DEGRADED)

    # Test: Invalid escalation stable → constitutional (from degraded, this IS valid)
    d2 = esc.escalate(SystemState.CONSTITUTIONAL, trigger, "test constitutional")
    t.check("Art.V — degraded → constitutional valid", d2.to_state == SystemState.CONSTITUTIONAL)

    # Test: Cannot jump constitutional → stable (invalid)
    d3 = esc.escalate(SystemState.STABLE, trigger, "test invalid jump")
    t.check("Art.V — constitutional → stable blocked", d3.to_state == SystemState.CONSTITUTIONAL)
    t.check("Art.V — Invalid transition contained", "BLOCKED" in d3.reason)

    # ═══════════════════════════════════════════════════
    # ARTICLE VI: Minimal Feedback Log
    # ═══════════════════════════════════════════════════
    print("\n═══ ARTICLE VI: Minimal Feedback Log ═══")

    t.check("Art.VI — Log entries recorded", log.length > 0)
    t.check("Art.VI — Chain integrity valid", log.verify_integrity())

    # Test: Log is append-only (no delete method)
    t.check("Art.VI — No delete method", not hasattr(log, 'delete'))
    t.check("Art.VI — No remove method", not hasattr(log, 'remove'))
    t.check("Art.VI — No clear method", not hasattr(log, 'clear'))

    # Test: Export produces valid JSON
    import json
    exported = json.loads(log.export_json())
    t.check("Art.VI — Export contains chain_hash", "chain_hash" in exported)
    t.check("Art.VI — Export contains entries", len(exported["entries"]) > 0)

    # ═══════════════════════════════════════════════════
    # ARTICLE VII: Pathology Detection Hooks
    # ═══════════════════════════════════════════════════
    print("\n═══ ARTICLE VII: Pathology Detection Hooks ═══")

    pd = PathologyDetector(log)

    # Test: High failure rate triggers alert
    alerts = pd.check_routing_health(100, 20)
    t.check("Art.VII — High failure rate detected", len(alerts) > 0)

    # Test: Chain integrity violation triggers constitutional alert
    chain_alerts = pd.check_chain_integrity(False)
    t.check("Art.VII — Chain violation → constitutional alert",
            any(a.severity == "constitutional" for a in chain_alerts))

    # Test: Clean state produces no alerts
    clean_alerts = pd.check_routing_health(100, 5)
    t.check("Art.VII — Clean state → no routing alerts", len(clean_alerts) == 0)

    # ═══════════════════════════════════════════════════
    # ARTICLE VIII: Jurisdiction Context Switcher
    # ═══════════════════════════════════════════════════
    print("\n═══ ARTICLE VIII: Jurisdiction Context Switcher ═══")

    jc = JurisdictionContext(log)

    # Test: Default context is safe
    t.check("Art.VIII — Default context is 'audit'", jc.current == "audit")

    # Test: Valid switch works
    switch_sig = create_signal(SignalType.STATE_CHECK, AuthorityLevel.OPERATOR, "audit", {"sw": True}, "test_op")
    ok, msg = jc.switch("sync", AuthorityLevel.OPERATOR, switch_sig)
    t.check("Art.VIII — Valid context switch", ok)

    # Test: Invalid jurisdiction rejected
    ok2, msg2 = jc.switch("nonexistent_domain", AuthorityLevel.OPERATOR, switch_sig)
    t.check("Art.VIII — Invalid jurisdiction rejected", not ok2)

    # Test: Cross-domain signal detection
    wrong_ctx_sig = create_signal(SignalType.STATE_CHECK, AuthorityLevel.OPERATOR, "audit", {"x": 1}, "test_op")
    t.check("Art.VIII — Cross-domain signal detected", not jc.check_signal_jurisdiction(wrong_ctx_sig))

    # ═══════════════════════════════════════════════════
    # ARTICLE IX: Default Safe Failure State
    # ═══════════════════════════════════════════════════
    print("\n═══ ARTICLE IX: Default Safe Failure State ═══")

    sf = SafeFailure(log)

    # Test: Process block works
    pb = sf.process_block("test_component", "test_reason", "test_id")
    t.check("Art.IX — Process block recorded", pb.failure_class == FailureClass.PROCESS_BLOCK)

    # Test: Kernel panic halts system
    kp = sf.kernel_panic("test_component", "axiom_violation", "test_id")
    t.check("Art.IX — Kernel panic halts system", sf.is_halted)

    # Test: Halted system blocks further execution
    result = sf.safe_execute(lambda: "should_not_run", "test", "test_id")
    t.check("Art.IX — Halted system blocks execution", result is None)

    # Test: Exception → safe failure (not crash)
    sf2 = SafeFailure(log)
    result2 = sf2.safe_execute(lambda: 1/0, "div_test", "test_id")
    t.check("Art.IX — Exception → safe failure", result2 is None)

    # ═══════════════════════════════════════════════════
    # FINAL INTEGRITY CHECK
    # ═══════════════════════════════════════════════════
    print("\n═══ FINAL INTEGRITY CHECK ═══")
    t.check("FINAL — Full log chain integrity", log.verify_integrity())

    # Print results
    print("\n" + "=" * 60)
    for r in t.results:
        print(r)
    print("=" * 60)
    print(f"\nTOTAL: {t.passed + t.failed} | PASSED: {t.passed} | FAILED: {t.failed}")
    all_passed = t.failed == 0
    print(f"VERDICT: {'CONSTITUTIONAL COMPLIANCE VERIFIED' if all_passed else 'COMPLIANCE VIOLATIONS DETECTED'}")
    print("=" * 60)

    report = "\n".join(t.results) + f"\n\nTOTAL: {t.passed + t.failed} | PASSED: {t.passed} | FAILED: {t.failed}"
    return all_passed, report


if __name__ == "__main__":
    passed, report = run_compliance_suite()
    sys.exit(0 if passed else 1)
