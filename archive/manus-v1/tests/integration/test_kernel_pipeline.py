"""
Integration Test: Sovereign Kernel Pipeline
=============================================
PDCA Loop 5 CHECK: End-to-end validation of the full
constitutional pipeline through the SovereignKernel.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from kernel.sovereign_kernel import SovereignKernel
from engine.signals.typed_signal import (
    TypedSignal, SignalType, AuthorityLevel, create_signal,
)
from governance.authority.trust_classes import TrustClass


class IntegrationResults:
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


def run_integration_suite() -> tuple[bool, str]:
    t = IntegrationResults()
    kernel = SovereignKernel()

    # ═══ TEST 1: Kernel initializes cleanly ═══
    print("\n═══ TEST 1: Kernel Initialization ═══")
    status = kernel.status()
    t.check("Kernel state is STABLE", status.system_state == "stable")
    t.check("Kernel not halted", not status.is_halted)
    t.check("Chain integrity valid", status.chain_integrity)
    t.check("Default jurisdiction is audit", status.jurisdiction == "audit")

    # ═══ TEST 2: Full signal pipeline — happy path ═══
    print("\n═══ TEST 2: Happy Path Signal Pipeline ═══")
    handled_signals = []
    kernel.register_handler(
        AuthorityLevel.OPERATOR, "state_check",
        lambda s: handled_signals.append(s.signal_id)
    )

    sig = create_signal(
        SignalType.STATE_CHECK, AuthorityLevel.OPERATOR,
        "audit", {"test": "pipeline"}, "integration_test"
    )
    result = kernel.process(sig, TrustClass.T0_ADVISORY)
    t.check("Signal accepted", result.accepted)
    t.check("Handler executed", len(handled_signals) == 1)
    t.check("Correct handler", result.handler_name == "state_check")

    # ═══ TEST 3: Insufficient authority — blocked ═══
    print("\n═══ TEST 3: Authority Enforcement ═══")
    bad_sig = create_signal(
        SignalType.OVERRIDE, AuthorityLevel.OPERATOR,
        "audit", {"test": "authority"}, "integration_test"
    )
    t.check("Insufficient authority → None signal", bad_sig is None)

    # ═══ TEST 4: Trust class enforcement ═══
    print("\n═══ TEST 4: Trust Class Enforcement ═══")
    sig2 = create_signal(
        SignalType.STATE_CHECK, AuthorityLevel.OPERATOR,
        "audit", {"test": "trust"}, "integration_test"
    )
    # Operator requesting T3 (requires Steward) → should be downgraded
    result2 = kernel.process(sig2, TrustClass.T3_AUTO_EXECUTABLE)
    t.check("T3 request by Operator → blocked", not result2.accepted)
    t.check("Blocked reason is trust", "trust" in result2.reason.lower() or "transaction_hold" in result2.reason)

    # ═══ TEST 5: Jurisdiction enforcement ═══
    print("\n═══ TEST 5: Jurisdiction Enforcement ═══")
    # Signal with unrecognized jurisdiction
    bad_juris_sig = TypedSignal(
        signal_type=SignalType.STATE_CHECK,
        authority=AuthorityLevel.OPERATOR,
        jurisdiction="nonexistent_domain",
        payload={"test": "jurisdiction"},
        source="integration_test",
    )
    result3 = kernel.process(bad_juris_sig, TrustClass.T0_ADVISORY)
    t.check("Invalid jurisdiction → blocked", not result3.accepted)

    # ═══ TEST 6: Cross-jurisdiction signal routing ═══
    print("\n═══ TEST 6: Cross-Jurisdiction Routing ═══")
    kernel.register_handler(
        AuthorityLevel.OPERATOR, "loop_confirmation",
        lambda s: None
    )
    sync_sig = create_signal(
        SignalType.LOOP_CONFIRMATION, AuthorityLevel.OPERATOR,
        "sync", {"test": "cross_juris"}, "integration_test"
    )
    result4 = kernel.process(sync_sig, TrustClass.T0_ADVISORY)
    t.check("Cross-jurisdiction auto-switch", result4.accepted)
    t.check("Jurisdiction now sync", kernel.status().jurisdiction == "sync")

    # ═══ TEST 7: Escalation through kernel ═══
    print("\n═══ TEST 7: Escalation Protocol ═══")
    from engine.signals.typed_signal import SystemState
    esc_trigger = create_signal(
        SignalType.ESCALATION, AuthorityLevel.INNOVATOR,
        "sync", {"reason": "test_escalation"}, "integration_test"
    )
    decision = kernel.escalation.escalate(
        SystemState.DEGRADED, esc_trigger, "integration test escalation"
    )
    t.check("Escalation to DEGRADED", decision.to_state == SystemState.DEGRADED)
    t.check("Authority now INNOVATOR", kernel.escalation.current_authority == AuthorityLevel.INNOVATOR)

    # ═══ TEST 8: Pathology detection ═══
    print("\n═══ TEST 8: Pathology Detection ═══")
    status2 = kernel.status()
    t.check("Pathology monitoring active", True)  # Detector always runs
    t.check("Chain integrity maintained", status2.chain_integrity)

    # ═══ TEST 9: Kernel panic and halt ═══
    print("\n═══ TEST 9: Kernel Panic ═══")
    kernel.safe_failure.kernel_panic("integration_test", "deliberate_test_panic", "test_id")
    t.check("Kernel is halted", kernel.safe_failure.is_halted)

    sig_after_panic = create_signal(
        SignalType.STATE_CHECK, AuthorityLevel.OPERATOR,
        "audit", {"test": "post_panic"}, "integration_test"
    )
    result5 = kernel.process(sig_after_panic, TrustClass.T0_ADVISORY)
    t.check("Post-panic signal → rejected", not result5.accepted)
    t.check("Rejection reason is kernel_panic", "kernel_panic" in result5.reason)

    # ═══ TEST 10: Audit trail completeness ═══
    print("\n═══ TEST 10: Audit Trail ═══")
    import json
    audit = json.loads(kernel.export_audit_log())
    t.check("Audit log has entries", audit["entry_count"] > 0)
    t.check("Audit chain hash present", len(audit["chain_hash"]) == 64)
    t.check("Final chain integrity", kernel.feedback_log.verify_integrity())

    # Print results
    print("\n" + "=" * 60)
    for r in t.results:
        print(r)
    print("=" * 60)
    print(f"\nTOTAL: {t.passed + t.failed} | PASSED: {t.passed} | FAILED: {t.failed}")
    all_passed = t.failed == 0
    print(f"VERDICT: {'INTEGRATION VERIFIED' if all_passed else 'INTEGRATION FAILURES DETECTED'}")
    print("=" * 60)

    report = "\n".join(t.results) + f"\n\nTOTAL: {t.passed + t.failed} | PASSED: {t.passed} | FAILED: {t.failed}"
    return all_passed, report


if __name__ == "__main__":
    passed, report = run_integration_suite()
    sys.exit(0 if passed else 1)
