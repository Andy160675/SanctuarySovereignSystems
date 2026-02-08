"""
Adversarial Security Test Suite
=================================
PDCA Loop 8 CHECK: Extreme adversarial testing.
Attempts to violate every axiom and article through
deliberate attack vectors. If any test passes where
it should fail, the constitution has a breach.

Standard: milspec future-proof — 10x rigor.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from kernel.sovereign_kernel import SovereignKernel
from engine.signals.typed_signal import (
    TypedSignal, SignalType, AuthorityLevel, SystemState, create_signal,
)
from engine.feedback.feedback_log import FeedbackLog, LogEntry
from governance.authority.trust_classes import TrustClass


class AdversarialResults:
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


def run_adversarial_suite() -> tuple[bool, str]:
    t = AdversarialResults()

    # ═══ ATTACK 1: Privilege Escalation ═══
    print("\n═══ ATTACK 1: Privilege Escalation ═══")
    # Attempt to create a STEWARD signal with OPERATOR authority
    steward_sig = create_signal(
        SignalType.SYSTEM_HALT, AuthorityLevel.OPERATOR,
        "audit", {"attack": "privilege_escalation"}, "attacker"
    )
    t.check("ATK-1a: Operator cannot forge SYSTEM_HALT", steward_sig is None)

    override_sig = create_signal(
        SignalType.OVERRIDE, AuthorityLevel.OPERATOR,
        "audit", {"attack": "override_forge"}, "attacker"
    )
    t.check("ATK-1b: Operator cannot forge OVERRIDE", override_sig is None)

    # ═══ ATTACK 2: Signal Tampering ═══
    print("\n═══ ATTACK 2: Signal Tampering ═══")
    sig = create_signal(
        SignalType.STATE_CHECK, AuthorityLevel.OPERATOR,
        "audit", {"data": "original"}, "legitimate_operator"
    )
    original_hash = sig.evidence_hash
    try:
        sig.payload = {"data": "tampered"}
        t.check("ATK-2a: Signal payload immutable", False, "mutation succeeded")
    except (AttributeError, TypeError):
        t.check("ATK-2a: Signal payload immutable", True)

    try:
        sig.evidence_hash = "0" * 64
        t.check("ATK-2b: Evidence hash immutable", False, "mutation succeeded")
    except (AttributeError, TypeError):
        t.check("ATK-2b: Evidence hash immutable", True)

    try:
        sig.authority = AuthorityLevel.STEWARD
        t.check("ATK-2c: Authority immutable", False, "mutation succeeded")
    except (AttributeError, TypeError):
        t.check("ATK-2c: Authority immutable", True)

    # ═══ ATTACK 3: Log Tampering ═══
    print("\n═══ ATTACK 3: Log Tampering ═══")
    log = FeedbackLog()
    log.append(LogEntry(
        signal_type="TEST", route_target="operator",
        handler="test", outcome="PASS", reason="test",
        evidence_hash="a" * 64,
    ))
    t.check("ATK-3a: Log integrity before attack", log.verify_integrity())

    # Attempt to access internal entries directly
    t.check("ATK-3b: Entries returns tuple (immutable view)",
            isinstance(log.entries, tuple))

    # Attempt to delete entries
    t.check("ATK-3c: No delete method on log", not hasattr(log, 'delete'))
    t.check("ATK-3d: No pop method on log", not hasattr(log, 'pop'))
    t.check("ATK-3e: No __delitem__ on log", not hasattr(log, '__delitem__'))

    # Verify chain still valid after attempted attacks
    t.check("ATK-3f: Chain integrity after attacks", log.verify_integrity())

    # ═══ ATTACK 4: Anonymous Signal Injection ═══
    print("\n═══ ATTACK 4: Anonymous Signal Injection ═══")
    kernel = SovereignKernel()
    anon_sig = TypedSignal(
        signal_type=SignalType.STATE_CHECK,
        authority=AuthorityLevel.OPERATOR,
        jurisdiction="audit",
        payload={"attack": "anonymous_injection"},
        source="unknown",
    )
    result = kernel.process(anon_sig, TrustClass.T0_ADVISORY)
    t.check("ATK-4a: Anonymous signal rejected", not result.accepted)

    # ═══ ATTACK 5: Empty/Null Signal Injection ═══
    print("\n═══ ATTACK 5: Empty/Null Signal Injection ═══")
    empty_juris = TypedSignal(
        signal_type=SignalType.STATE_CHECK,
        authority=AuthorityLevel.OPERATOR,
        jurisdiction="",
        payload={"attack": "empty_jurisdiction"},
        source="attacker",
    )
    result2 = kernel.process(empty_juris, TrustClass.T0_ADVISORY)
    t.check("ATK-5a: Empty jurisdiction rejected", not result2.accepted)

    # ═══ ATTACK 6: Trust Class Bypass ═══
    print("\n═══ ATTACK 6: Trust Class Bypass ═══")
    sig6 = create_signal(
        SignalType.STATE_CHECK, AuthorityLevel.OPERATOR,
        "audit", {"attack": "trust_bypass"}, "attacker"
    )
    # Operator requesting T3 (Steward-only)
    result3 = kernel.process(sig6, TrustClass.T3_AUTO_EXECUTABLE)
    t.check("ATK-6a: T3 by Operator → blocked", not result3.accepted)

    # Operator requesting T2 (Innovator-only)
    sig6b = create_signal(
        SignalType.STATE_CHECK, AuthorityLevel.OPERATOR,
        "audit", {"attack": "trust_bypass_t2"}, "attacker"
    )
    result3b = kernel.process(sig6b, TrustClass.T2_PRE_APPROVED)
    t.check("ATK-6b: T2 by Operator → blocked", not result3b.accepted)

    # ═══ ATTACK 7: Invalid Escalation Path ═══
    print("\n═══ ATTACK 7: Invalid Escalation Path ═══")
    trigger = create_signal(
        SignalType.ESCALATION, AuthorityLevel.INNOVATOR,
        "audit", {"attack": "invalid_escalation"}, "attacker"
    )
    # Try to jump from STABLE directly to CONSTITUTIONAL
    decision = kernel.escalation.escalate(SystemState.CONSTITUTIONAL, trigger, "attack")
    t.check("ATK-7a: STABLE → CONSTITUTIONAL blocked",
            decision.to_state != SystemState.CONSTITUTIONAL or "BLOCKED" in decision.reason)

    # ═══ ATTACK 8: Cross-Domain Contamination ═══
    print("\n═══ ATTACK 8: Cross-Domain Contamination ═══")
    fake_domain_sig = TypedSignal(
        signal_type=SignalType.STATE_CHECK,
        authority=AuthorityLevel.OPERATOR,
        jurisdiction="nonexistent_military_domain",
        payload={"attack": "cross_domain"},
        source="attacker",
    )
    result4 = kernel.process(fake_domain_sig, TrustClass.T0_ADVISORY)
    t.check("ATK-8a: Fake jurisdiction rejected", not result4.accepted)

    # ═══ ATTACK 9: Post-Panic Execution ═══
    print("\n═══ ATTACK 9: Post-Panic Execution ═══")
    kernel2 = SovereignKernel()
    kernel2.safe_failure.kernel_panic("test", "deliberate_panic", "test_id")

    post_panic = create_signal(
        SignalType.STATE_CHECK, AuthorityLevel.STEWARD,
        "audit", {"attack": "post_panic"}, "steward_attacker"
    )
    result5 = kernel2.process(post_panic, TrustClass.T3_AUTO_EXECUTABLE)
    t.check("ATK-9a: Even STEWARD blocked after panic", not result5.accepted)

    # ═══ ATTACK 10: Hash Chain Forgery Detection ═══
    print("\n═══ ATTACK 10: Hash Chain Forgery Detection ═══")
    log2 = FeedbackLog()
    log2.append(LogEntry(
        signal_type="LEGIT", route_target="operator",
        handler="test", outcome="PASS", reason="legitimate",
        evidence_hash="b" * 64,
    ))
    # Tamper with internal chain hash via object attribute
    original_integrity = log2.verify_integrity()
    t.check("ATK-10a: Chain valid before forgery attempt", original_integrity)

    # Attempt to forge by manipulating _chain_hash directly
    saved_hash = log2._chain_hash
    log2._chain_hash = "f" * 64  # Forge the chain hash
    t.check("ATK-10b: Forged chain detected as invalid", not log2.verify_integrity())
    log2._chain_hash = saved_hash  # Restore
    t.check("ATK-10c: Restored chain validates correctly", log2.verify_integrity())

    # Print results
    print("\n" + "=" * 60)
    for r in t.results:
        print(r)
    print("=" * 60)
    print(f"\nTOTAL: {t.passed + t.failed} | PASSED: {t.passed} | FAILED: {t.failed}")
    all_passed = t.failed == 0
    print(f"VERDICT: {'ADVERSARIAL SECURITY VERIFIED' if all_passed else 'SECURITY BREACHES DETECTED'}")
    print("=" * 60)

    report = "\n".join(t.results) + f"\n\nTOTAL: {t.passed + t.failed} | PASSED: {t.passed} | FAILED: {t.failed}"
    return all_passed, report


if __name__ == "__main__":
    passed, report = run_adversarial_suite()
    sys.exit(0 if passed else 1)
