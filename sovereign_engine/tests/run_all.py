"""
SOVEREIGN RECURSION ENGINE — Full Test Harness
CSS-ENG-TEST-001

Tests every phase in dependency order.
Every invariant has at least one test.
Adversarial scenarios included.
Stress conditions included.

Run: python3 -m sovereign_engine.tests.run_all
"""

import sys
import os
import json
import time
import hashlib

# Fix path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from sovereign_engine.core.phase0_constitution import (
    Constitution, ConstitutionalError, BootError, register_builtin_tests
)
from sovereign_engine.core.phase1_signals import (
    SignalFactory, SignalBus, Signal, SignalValidationError
)
from sovereign_engine.core.phase2_router import (
    Router, AuthorityHandler, AuthorityError
)
from sovereign_engine.core.phase3_legality import LegalityGate
from sovereign_engine.core.phase4_audit import AuditLedger, AuditError
from sovereign_engine.core.phase5_timing import TimingEnforcer, Watchdog, HaltController
from sovereign_engine.core.phase6_failure import FailureMatrix, HealthMonitor
from sovereign_engine.core.phase7_configurator import ConstitutionalConfigurator
from sovereign_engine.core.phase8_engine import SovereignEngine, EngineError
from sovereign_engine.core.phase9_extensions import (
    ExtensionRegistry, ExtensionManifest, ExtensionError
)

# ═══════════════════════════════════════════════════════════
# TEST FRAMEWORK
# ═══════════════════════════════════════════════════════════

class TestResult:
    def __init__(self, name, passed, detail=""):
        self.name = name
        self.passed = passed
        self.detail = detail

RESULTS = []
PHASE_NAME = ""

def phase(name):
    global PHASE_NAME
    PHASE_NAME = name
    print(f"\n{'='*70}")
    print(f"  PHASE: {name}")
    print(f"{'='*70}")

def test(name):
    def decorator(fn):
        def wrapper():
            try:
                fn()
                r = TestResult(f"[{PHASE_NAME}] {name}", True)
                RESULTS.append(r)
                print(f"  ✓ {name}")
            except AssertionError as e:
                r = TestResult(f"[{PHASE_NAME}] {name}", False, str(e))
                RESULTS.append(r)
                print(f"  ✗ {name}: {e}")
            except Exception as e:
                r = TestResult(f"[{PHASE_NAME}] {name}", False, f"EXCEPTION: {e}")
                RESULTS.append(r)
                print(f"  ✗ {name}: EXCEPTION: {e}")
        return wrapper
    return decorator

CONFIG_PATH = os.path.join(
    os.path.dirname(__file__), "..", "configs", "constitution.json"
)

def fresh_constitution():
    c = Constitution(CONFIG_PATH)
    c.load()
    c.validate()
    return c

def fresh_factory(c=None):
    return SignalFactory(c or fresh_constitution())


# ═══════════════════════════════════════════════════════════
# PHASE 0: CONSTITUTIONAL GROUND TRUTH
# ═══════════════════════════════════════════════════════════

@test("constitution loads from disk")
def t0_01():
    c = Constitution(CONFIG_PATH)
    c.load()
    assert c._raw is not None

@test("constitution validates successfully")
def t0_02():
    c = Constitution(CONFIG_PATH)
    c.load()
    c.validate()
    assert c._validated is True

@test("missing file raises BootError")
def t0_03():
    c = Constitution("/nonexistent/path.json")
    try:
        c.load()
        assert False, "Should have raised"
    except BootError:
        pass

@test("malformed JSON raises BootError")
def t0_04():
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        f.write("{bad json")
        path = f.name
    try:
        c = Constitution(path)
        c.load()
        assert False, "Should have raised"
    except BootError:
        pass
    finally:
        os.unlink(path)

@test("get() returns frozen copies (mutation doesn't affect original)")
def t0_05():
    c = fresh_constitution()
    grammar = c.get("routing_grammar")
    grammar["default_on_ambiguity"] = "HACKED"
    assert c.get("routing_grammar")["default_on_ambiguity"] == "halt"

@test("all 16 built-in invariant tests pass")
def t0_06():
    c = fresh_constitution()
    register_builtin_tests(c)
    report = c.run_invariant_tests()
    assert report.all_passed, f"Failed: {[r for r in report.results if not r.passed]}"
    assert report.total == 16, f"Expected 16 tests, got {report.total}"

@test("is_forbidden returns True for known forbidden states")
def t0_07():
    c = fresh_constitution()
    assert c.is_forbidden("cross_authority_direct_call") is True
    assert c.is_forbidden("nonexistent_state") is False

@test("unknown failure type defaults to halt")
def t0_08():
    c = fresh_constitution()
    r = c.get_failure_response("completely_unknown")
    assert r["action"] == "halt"

@test("constitution rejects missing halt doctrine")
def t0_09():
    c = Constitution(CONFIG_PATH)
    c.load()
    c._raw["routing_grammar"]["default_on_ambiguity"] = "continue"
    try:
        c.validate()
        assert False, "Should have raised"
    except ConstitutionalError as e:
        assert "HALT DOCTRINE" in str(e)


# ═══════════════════════════════════════════════════════════
# PHASE 1: TYPED SIGNAL SUBSTRATE
# ═══════════════════════════════════════════════════════════

@test("factory creates valid signal with hash")
def t1_01():
    f = fresh_factory()
    s = f.create("query", "operational", "operator", {"q": "test"})
    assert s.type == "query"
    assert s.hash != ""
    assert s.verify_integrity()

@test("factory rejects invalid type")
def t1_02():
    f = fresh_factory()
    try:
        f.create("INVALID_TYPE", "operational", "operator", {})
        assert False
    except SignalValidationError:
        pass

@test("factory rejects invalid domain")
def t1_03():
    f = fresh_factory()
    try:
        f.create("query", "INVALID_DOMAIN", "operator", {})
        assert False
    except SignalValidationError:
        pass

@test("factory rejects invalid authority")
def t1_04():
    f = fresh_factory()
    try:
        f.create("query", "operational", "INVALID_AUTH", {})
        assert False
    except SignalValidationError:
        pass

@test("factory rejects None payload")
def t1_05():
    f = fresh_factory()
    try:
        f.create("query", "operational", "operator", None)
        assert False
    except SignalValidationError:
        pass

@test("signal integrity detects tampering")
def t1_06():
    f = fresh_factory()
    s = f.create("query", "operational", "operator", {"data": "original"})
    assert s.verify_integrity()
    # Tamper
    s.payload = {"data": "TAMPERED"}
    assert not s.verify_integrity()

@test("bus accepts valid signals")
def t1_07():
    c = fresh_constitution()
    f = SignalFactory(c)
    bus = SignalBus(f, c)
    s = f.create("query", "operational", "operator", {"test": True})
    result = bus.submit(s)
    assert result["accepted"] is True
    assert result["channel"] == "normal"

@test("bus classifies halt signals to halt channel")
def t1_08():
    c = fresh_constitution()
    f = SignalFactory(c)
    bus = SignalBus(f, c)
    s = f.create("halt", "operational", "system", {"reason": "test"})
    result = bus.submit(s)
    assert result["channel"] == "halt"

@test("bus classifies escalation signals to escalation channel")
def t1_09():
    c = fresh_constitution()
    f = SignalFactory(c)
    bus = SignalBus(f, c)
    s = f.create("escalation", "operational", "operator", {"reason": "test"},
                 source="operator")
    result = bus.submit(s)
    assert result["channel"] == "escalation"

@test("halted bus rejects non-halt signals")
def t1_10():
    c = fresh_constitution()
    f = SignalFactory(c)
    bus = SignalBus(f, c)
    bus.halt("test")
    s = f.create("query", "operational", "operator", {"test": True})
    result = bus.submit(s)
    assert result["accepted"] is False

@test("drain returns signals in priority order")
def t1_11():
    c = fresh_constitution()
    f = SignalFactory(c)
    bus = SignalBus(f, c)
    s1 = f.create("query", "operational", "operator", {"n": 1})
    s2 = f.create("escalation", "governance", "innovator", {"n": 2}, source="operator")
    s3 = f.create("halt", "emergency", "system", {"n": 3})
    bus.submit(s1)
    bus.submit(s2)
    bus.submit(s3)
    drained = bus.drain("all")
    assert drained[0].type == "halt"
    assert drained[1].type == "escalation"
    assert drained[2].type == "query"


# ═══════════════════════════════════════════════════════════
# PHASE 2: ROUTER & AUTHORITY KERNEL
# ═══════════════════════════════════════════════════════════

def build_router():
    c = fresh_constitution()
    f = SignalFactory(c)
    r = Router(c)
    # Register handlers with jurisdiction
    for level, domains in [
        ("operator", {"operational"}),
        ("innovator", {"governance", "operational"}),
        ("steward", {"constitutional", "emergency", "governance", "operational"}),
    ]:
        h = AuthorityHandler(level, domains)
        h.set_handler(lambda sig, _l=level: {"outcome": "processed", "data": {"by": _l}})
        r.register_handler(level, h)
    return c, f, r

@test("operational query routes to operator")
def t2_01():
    c, f, r = build_router()
    s = f.create("query", "operational", "operator", {"q": "test"})
    d = r.route(s)
    assert d.target == "operator"
    assert d.action == "routed"

@test("governance signal routes to innovator")
def t2_02():
    c, f, r = build_router()
    s = f.create("query", "governance", "innovator", {"q": "policy"})
    d = r.route(s)
    assert d.target == "innovator"
    assert d.action == "routed"

@test("constitutional signal routes to steward")
def t2_03():
    c, f, r = build_router()
    s = f.create("alert", "constitutional", "steward", {"alert": "breach"})
    d = r.route(s)
    assert d.target == "steward"
    assert d.action == "routed"

@test("emergency signal routes to steward")
def t2_04():
    c, f, r = build_router()
    s = f.create("alert", "emergency", "steward", {"alert": "critical"})
    d = r.route(s)
    assert d.target == "steward"
    assert d.action == "routed"

@test("halt signal triggers system halt")
def t2_05():
    c, f, r = build_router()
    s = f.create("halt", "operational", "system", {"reason": "test"})
    d = r.route(s)
    assert d.action == "system_halt"
    assert r.is_halted

@test("inactive handler triggers escalation")
def t2_06():
    c, f, r = build_router()
    r._handlers["operator"].deactivate()
    s = f.create("query", "operational", "operator", {"q": "test"})
    d = r.route(s)
    assert d.action == "escalated"
    assert d.target == "innovator"

@test("all handlers inactive → escalation exhausted → halt")
def t2_07():
    c, f, r = build_router()
    for h in r._handlers.values():
        h.deactivate()
    s = f.create("query", "operational", "operator", {"q": "test"})
    d = r.route(s)
    assert d.action == "halt"
    assert "exhausted" in (d.reason or "").lower()

@test("halted router rejects signals")
def t2_08():
    c, f, r = build_router()
    r.halt("test")
    s = f.create("query", "operational", "operator", {"q": "test"})
    d = r.route(s)
    assert d.action == "rejected"


# ═══════════════════════════════════════════════════════════
# PHASE 3: LEGALITY GATE
# ═══════════════════════════════════════════════════════════

@test("valid signal passes legality gate")
def t3_01():
    c = fresh_constitution()
    f = SignalFactory(c)
    gate = LegalityGate(c, f)
    s = f.create("query", "operational", "operator", {"q": "test"})
    result = gate.check(s)
    assert result.legal is True

@test("tampered signal fails integrity check")
def t3_02():
    c = fresh_constitution()
    f = SignalFactory(c)
    gate = LegalityGate(c, f)
    s = f.create("query", "operational", "operator", {"data": "original"})
    s.payload = {"data": "TAMPERED"}
    result = gate.check(s)
    assert result.legal is False
    assert any(v.rule == "integrity_verification" for v in result.violations)

@test("cross-authority direct call blocked")
def t3_03():
    c = fresh_constitution()
    f = SignalFactory(c)
    gate = LegalityGate(c, f)
    s = f.create("command", "operational", "operator", {"cmd": "do"})
    result = gate.check(s, {
        "source_authority": "operator",
        "target_authority": "steward",
        "via_router": False,
    })
    assert result.legal is False
    assert any(v.rule == "cross_authority_direct_call" for v in result.violations)

@test("cross-authority via router is allowed")
def t3_04():
    c = fresh_constitution()
    f = SignalFactory(c)
    gate = LegalityGate(c, f)
    s = f.create("command", "operational", "operator", {"cmd": "do"})
    result = gate.check(s, {
        "source_authority": "operator",
        "target_authority": "steward",
        "via_router": True,
    })
    assert result.legal is True

@test("execution after halt is blocked")
def t3_05():
    c = fresh_constitution()
    f = SignalFactory(c)
    gate = LegalityGate(c, f)
    s = f.create("query", "operational", "operator", {"q": "test"})
    result = gate.check(s, {"system_halted": True})
    assert result.legal is False
    assert any(v.rule == "execution_after_halt_signal" for v in result.violations)

@test("silent escalation blocked")
def t3_06():
    c = fresh_constitution()
    f = SignalFactory(c)
    gate = LegalityGate(c, f)
    s = f.create("escalation", "operational", "operator", {"reason": "test"})
    # source is None — silent escalation
    result = gate.check(s)
    assert result.legal is False
    assert any(v.rule == "silent_authority_escalation" for v in result.violations)

@test("steward override without dual key blocked")
def t3_07():
    c = fresh_constitution()
    f = SignalFactory(c)
    gate = LegalityGate(c, f)
    s = f.create("command", "constitutional", "steward", {"override": True})
    result = gate.check(s, {"steward_override": True, "dual_key": False})
    assert result.legal is False
    assert any(v.rule == "steward_override_without_dual_key" for v in result.violations)

@test("containment event logged on termination")
def t3_08():
    c = fresh_constitution()
    f = SignalFactory(c)
    gate = LegalityGate(c, f)
    s = f.create("query", "operational", "operator", {"q": "test"})
    s.payload = {"TAMPERED": True}
    gate.check(s)
    assert len(gate.containment_log) == 1
    assert gate.stats.terminated == 1

@test("custom legality rules enforced")
def t3_09():
    c = fresh_constitution()
    f = SignalFactory(c)
    gate = LegalityGate(c, f)
    gate.add_rule("no_test_payloads", lambda s, ctx: (
        (False, "test payloads forbidden") if s.payload.get("test") else (True, "")
    ))
    s = f.create("query", "operational", "operator", {"test": True})
    result = gate.check(s)
    assert result.legal is False
    assert any(v.rule == "no_test_payloads" for v in result.violations)


# ═══════════════════════════════════════════════════════════
# PHASE 4: AUDIT LEDGER
# ═══════════════════════════════════════════════════════════

@test("ledger writes entries with hash chain")
def t4_01():
    c = fresh_constitution()
    ledger = AuditLedger(c)
    e1 = ledger.write({
        "signal_type": "query", "route": "operator",
        "handler": "operator", "outcome": "processed",
    })
    e2 = ledger.write({
        "signal_type": "command", "route": "innovator",
        "handler": "innovator", "outcome": "processed",
    })
    assert e1.hash != e2.hash
    assert e2.previous_hash == e1.hash
    assert e1.previous_hash == "0" * 64

@test("ledger verifies intact chain")
def t4_02():
    c = fresh_constitution()
    ledger = AuditLedger(c)
    for i in range(10):
        ledger.write({
            "signal_type": "query", "route": "operator",
            "handler": "operator", "outcome": "processed",
            "signal_id": f"sig_{i}",
        })
    v = ledger.verify()
    assert v["valid"] is True
    assert v["total_entries"] == 10

@test("ledger detects corruption")
def t4_03():
    c = fresh_constitution()
    ledger = AuditLedger(c)
    for i in range(5):
        ledger.write({
            "signal_type": "query", "route": "operator",
            "handler": "operator", "outcome": "processed",
        })
    # Corrupt entry 2 by replacing it
    corrupted = list(ledger._entries)
    # Can't easily corrupt frozen dataclass, so test via a different approach
    # Insert a fake entry that breaks the chain
    from sovereign_engine.core.phase4_audit import AuditEntry
    fake = AuditEntry(
        index=2, signal_type="FAKE", route="FAKE", handler="FAKE",
        outcome="FAKE", signal_id="FAKE", signal_domain="FAKE",
        timestamp=0, previous_hash="WRONG_HASH", hash="FAKE_HASH",
    )
    ledger._entries[2] = fake
    v = ledger.verify()
    assert v["valid"] is False
    assert v["last_valid_index"] == 1

@test("ledger truncates on corruption")
def t4_04():
    c = fresh_constitution()
    ledger = AuditLedger(c)
    for i in range(5):
        ledger.write({
            "signal_type": "query", "route": "operator",
            "handler": "operator", "outcome": "processed",
        })
    from sovereign_engine.core.phase4_audit import AuditEntry
    fake = AuditEntry(
        index=3, signal_type="FAKE", route="FAKE", handler="FAKE",
        outcome="FAKE", signal_id="FAKE", signal_domain="FAKE",
        timestamp=0, previous_hash="WRONG", hash="FAKE",
    )
    ledger._entries[3] = fake
    result = ledger.truncate_at_last_valid()
    assert result["truncated"] is True
    assert ledger.length == 3
    assert ledger.verify()["valid"] is True

@test("sealed ledger rejects writes")
def t4_05():
    c = fresh_constitution()
    ledger = AuditLedger(c)
    ledger.seal("test")
    try:
        ledger.write({
            "signal_type": "query", "route": "operator",
            "handler": "operator", "outcome": "processed",
        })
        assert False
    except AuditError:
        pass

@test("boot validation succeeds on clean ledger")
def t4_06():
    c = fresh_constitution()
    ledger = AuditLedger(c)
    ledger.write({
        "signal_type": "system", "route": "boot",
        "handler": "engine", "outcome": "ok",
    })
    result = ledger.boot_validation()
    assert result["boot_valid"] is True


# ═══════════════════════════════════════════════════════════
# PHASE 5: TIMING & HALT
# ═══════════════════════════════════════════════════════════

@test("timing enforcer measures within contract")
def t5_01():
    c = fresh_constitution()
    te = TimingEnforcer(c)
    result, breach = te.measure("test", "max_routing_latency_ms", lambda: 42)
    assert result == 42
    assert breach is None

@test("timing enforcer detects breach")
def t5_02():
    c = fresh_constitution()
    te = TimingEnforcer(c)
    def slow_fn():
        time.sleep(0.15)  # 150ms > halt_response_max_ms (100ms)
        return "done"
    result, breach = te.measure("test", "halt_response_max_ms", slow_fn)
    assert result == "done"
    assert breach is not None
    assert breach.actual_ms > 100

@test("halt controller requires ledger validation for resume")
def t5_03():
    hc = HaltController()
    hc.halt("test", "test_source")
    assert hc.is_halted
    result = hc.resume(ledger_valid=False)
    assert result["resumed"] is False
    assert hc.is_halted
    result = hc.resume(ledger_valid=True)
    assert result["resumed"] is True
    assert not hc.is_halted

@test("watchdog detects dead components")
def t5_04():
    c = fresh_constitution()
    wd = Watchdog(c)
    wd.register("router")
    wd.register("audit")
    wd.heartbeat("router")
    # Don't heartbeat audit — but watchdog interval is 5000ms
    # so force-expire by backdating
    wd._components["audit"].last_heartbeat = time.time() - 10
    dead = wd.check()
    assert "audit" in dead
    assert "router" not in dead


# ═══════════════════════════════════════════════════════════
# PHASE 6: FAILURE SEMANTICS
# ═══════════════════════════════════════════════════════════

@test("router failure triggers halt")
def t6_01():
    c = fresh_constitution()
    hc = HaltController()
    fm = FailureMatrix(c, hc)
    event = fm.handle_failure("router", "router_failure", "test crash")
    assert event.action == "halt"
    assert hc.is_halted

@test("audit failure triggers halt")
def t6_02():
    c = fresh_constitution()
    hc = HaltController()
    fm = FailureMatrix(c, hc)
    fm.handle_failure("audit", "audit_failure", "corruption")
    assert hc.is_halted

@test("legality failure triggers escalation (not halt)")
def t6_03():
    c = fresh_constitution()
    hc = HaltController()
    fm = FailureMatrix(c, hc)
    event = fm.handle_failure("gate", "legality_failure", "bad signal")
    assert event.action == "escalate_and_contain"
    assert not hc.is_halted

@test("health monitor tracks component status")
def t6_04():
    c = fresh_constitution()
    hc = HaltController()
    fm = FailureMatrix(c, hc)
    hm = HealthMonitor(fm)
    hm.register("router")
    hm.register("audit")
    hm.report_healthy("router")
    hm.report_failure("audit", "audit_failure", "test")
    assert not hm.all_healthy
    assert hm.get_unhealthy() == ["audit"]


# ═══════════════════════════════════════════════════════════
# PHASE 7: CONSTITUTIONAL CONFIGURATOR
# ═══════════════════════════════════════════════════════════

@test("managerial archetype compiles successfully")
def t7_01():
    c = fresh_constitution()
    cc = ConstitutionalConfigurator(c)
    compiled = cc.compile("managerial")
    assert compiled.valid
    assert compiled.steward_mode == "active"
    assert compiled.routing_mutable is True
    assert compiled.upgrades_enabled is True

@test("immutable archetype compiles with routing locked")
def t7_02():
    c = fresh_constitution()
    cc = ConstitutionalConfigurator(c)
    compiled = cc.compile("immutable")
    assert compiled.valid
    assert compiled.steward_mode == "passive"
    assert compiled.routing_mutable is False
    assert compiled.upgrades_enabled is False
    assert any(r["rule"] == "no_runtime_routing_modification"
               for r in compiled.legality_overrides)

@test("federated archetype compiles with quorum")
def t7_03():
    c = fresh_constitution()
    cc = ConstitutionalConfigurator(c)
    compiled = cc.compile("federated")
    assert compiled.valid
    assert compiled.steward_mode == "quorum"
    assert compiled.routing_overrides.get("steward_requires_quorum") is True

@test("unknown archetype raises error")
def t7_04():
    c = fresh_constitution()
    cc = ConstitutionalConfigurator(c)
    try:
        cc.compile("nonexistent")
        assert False
    except ConstitutionalError:
        pass

@test("all three archetypes listed")
def t7_05():
    c = fresh_constitution()
    cc = ConstitutionalConfigurator(c)
    names = cc.list_archetypes()
    assert set(names) == {"managerial", "immutable", "federated"}


# ═══════════════════════════════════════════════════════════
# PHASE 8: FULL ENGINE INTEGRATION
# ═══════════════════════════════════════════════════════════

@test("engine boots successfully")
def t8_01():
    engine = SovereignEngine(CONFIG_PATH)
    report = engine.boot()
    assert report["status"] == "ready"
    assert engine.is_booted

@test("engine processes valid operational signal")
def t8_02():
    engine = SovereignEngine(CONFIG_PATH)
    engine.boot()
    result = engine.submit_and_process("query", "operational", "operator", {"q": "test"})
    assert result["processed"] is True
    assert result["action"] == "routed"
    assert result["target"] == "operator"

@test("engine processes governance signal to innovator")
def t8_03():
    engine = SovereignEngine(CONFIG_PATH)
    engine.boot()
    result = engine.submit_and_process("command", "governance", "innovator", {"cmd": "review"})
    assert result["processed"] is True
    assert result["target"] == "innovator"

@test("engine processes constitutional signal to steward")
def t8_04():
    engine = SovereignEngine(CONFIG_PATH)
    engine.boot()
    result = engine.submit_and_process("alert", "constitutional", "steward", {"alert": "test"})
    assert result["processed"] is True
    assert result["target"] == "steward"

@test("engine terminates tampered signal at legality gate")
def t8_05():
    engine = SovereignEngine(CONFIG_PATH)
    engine.boot()
    s = engine.create_signal("query", "operational", "operator", {"data": "clean"})
    s.payload = {"data": "TAMPERED"}
    result = engine.process(s)
    assert result["processed"] is False
    assert result["stage"] == "legality"

@test("engine audits every processed signal")
def t8_06():
    engine = SovereignEngine(CONFIG_PATH)
    engine.boot()
    initial = engine.ledger.length  # boot event
    engine.submit_and_process("query", "operational", "operator", {"q": "1"})
    engine.submit_and_process("command", "governance", "innovator", {"c": "2"})
    assert engine.ledger.length == initial + 2

@test("engine audits terminated signals too")
def t8_07():
    engine = SovereignEngine(CONFIG_PATH)
    engine.boot()
    initial = engine.ledger.length
    s = engine.create_signal("query", "operational", "operator", {"data": "ok"})
    s.payload = {"data": "TAMPERED"}
    engine.process(s)
    assert engine.ledger.length == initial + 1

@test("engine halt signal stops processing")
def t8_08():
    engine = SovereignEngine(CONFIG_PATH)
    engine.boot()
    engine.submit_and_process("halt", "operational", "system", {"reason": "test"})
    assert engine.is_halted
    result = engine.submit_and_process("query", "operational", "operator", {"q": "blocked"})
    assert result["processed"] is False

@test("engine audit chain valid after mixed operations")
def t8_09():
    engine = SovereignEngine(CONFIG_PATH)
    engine.boot()
    engine.submit_and_process("query", "operational", "operator", {"q": "1"})
    engine.submit_and_process("command", "governance", "innovator", {"c": "2"})
    engine.submit_and_process("alert", "constitutional", "steward", {"a": "3"})
    # Tampered signal
    s = engine.create_signal("query", "operational", "operator", {"d": "4"})
    s.payload = {"d": "TAMPERED"}
    engine.process(s)
    v = engine.ledger.verify()
    assert v["valid"] is True
    assert v["total_entries"] >= 4

@test("engine stats accurate after operations")
def t8_10():
    engine = SovereignEngine(CONFIG_PATH)
    engine.boot()
    engine.submit_and_process("query", "operational", "operator", {"q": "1"})
    engine.submit_and_process("query", "operational", "operator", {"q": "2"})
    s = engine.create_signal("query", "operational", "operator", {"d": "3"})
    s.payload = {"TAMPERED": True}
    engine.process(s)
    stats = engine.engine_stats
    assert stats["signals_processed"] == 3
    assert stats["signals_terminated"] == 1
    assert stats["signals_routed"] == 2


# ═══════════════════════════════════════════════════════════
# PHASE 9: EXTENSION SCAFFOLD
# ═══════════════════════════════════════════════════════════

@test("compliant extension registers and activates")
def t9_01():
    c = fresh_constitution()
    reg = ExtensionRegistry(c)
    manifest = ExtensionManifest(
        name="test_extension", version="1.0", author="test",
        description="Test", requires_authority="operator",
    )
    result = reg.register(manifest, lambda: None)
    assert result.compliant is True
    assert reg.activate("test_extension") is True
    assert reg.is_activated("test_extension")

@test("extension modifying halt doctrine rejected")
def t9_02():
    c = fresh_constitution()
    reg = ExtensionRegistry(c)
    manifest = ExtensionManifest(
        name="bad_ext", version="1.0", author="test",
        description="Test", requires_authority="operator",
        writes_to=["default_on_ambiguity"],
    )
    result = reg.register(manifest, lambda: None)
    assert result.compliant is False
    assert any("halt doctrine" in v.lower() for v in result.violations)

@test("extension modifying authority ladder rejected")
def t9_03():
    c = fresh_constitution()
    reg = ExtensionRegistry(c)
    manifest = ExtensionManifest(
        name="bad_ext2", version="1.0", author="test",
        description="Test", requires_authority="operator",
        writes_to=["authority_ladder"],
    )
    result = reg.register(manifest, lambda: None)
    assert result.compliant is False

@test("steward-level routing modification rejected for extensions")
def t9_04():
    c = fresh_constitution()
    reg = ExtensionRegistry(c)
    manifest = ExtensionManifest(
        name="bad_ext3", version="1.0", author="test",
        description="Test", requires_authority="steward",
        modifies_routing=True,
    )
    result = reg.register(manifest, lambda: None)
    assert result.compliant is False

@test("non-compliant extension cannot activate")
def t9_05():
    c = fresh_constitution()
    reg = ExtensionRegistry(c)
    manifest = ExtensionManifest(
        name="bad", version="1.0", author="test",
        description="Test", requires_authority="operator",
        writes_to=["authority_ladder"],
    )
    reg.register(manifest, lambda: None)
    try:
        reg.activate("bad")
        assert False
    except ExtensionError:
        pass


# ═══════════════════════════════════════════════════════════
# ADVERSARIAL SCENARIOS
# ═══════════════════════════════════════════════════════════

@test("ADVERSARIAL: flood bus with 1000 signals — all processed or rejected cleanly")
def ta_01():
    engine = SovereignEngine(CONFIG_PATH)
    engine.boot()
    for i in range(1000):
        engine.submit_and_process("query", "operational", "operator", {"n": i})
    assert engine.engine_stats["signals_processed"] == 1000
    assert engine.engine_stats["signals_routed"] == 1000
    v = engine.ledger.verify()
    assert v["valid"] is True

@test("ADVERSARIAL: interleave valid and tampered signals — audit stays valid")
def ta_02():
    engine = SovereignEngine(CONFIG_PATH)
    engine.boot()
    for i in range(50):
        engine.submit_and_process("query", "operational", "operator", {"n": i})
        s = engine.create_signal("query", "operational", "operator", {"d": i})
        s.payload = {"TAMPERED": i}
        engine.process(s)
    assert engine.engine_stats["signals_terminated"] == 50
    assert engine.engine_stats["signals_routed"] == 50
    v = engine.ledger.verify()
    assert v["valid"] is True

@test("ADVERSARIAL: halt then attempt processing — all blocked")
def ta_03():
    engine = SovereignEngine(CONFIG_PATH)
    engine.boot()
    engine.submit_and_process("halt", "operational", "system", {"reason": "lockdown"})
    results = []
    for i in range(10):
        r = engine.submit_and_process("query", "operational", "operator", {"n": i})
        results.append(r)
    assert all(r["processed"] is False for r in results)


# ═══════════════════════════════════════════════════════════
# RUNNER
# ═══════════════════════════════════════════════════════════

def run_all():
    """Execute all tests in dependency order."""
    print("=" * 70)
    print("  SOVEREIGN RECURSION ENGINE — Full Test Harness")
    print("  CSS-ENG-TEST-001 | Slow and Right")
    print("=" * 70)

    # Phase 0
    phase("Phase 0: Constitutional Ground Truth")
    t0_01(); t0_02(); t0_03(); t0_04(); t0_05()
    t0_06(); t0_07(); t0_08(); t0_09()

    # Phase 1
    phase("Phase 1: Typed Signal Substrate")
    t1_01(); t1_02(); t1_03(); t1_04(); t1_05()
    t1_06(); t1_07(); t1_08(); t1_09(); t1_10(); t1_11()

    # Phase 2
    phase("Phase 2: Router & Authority Kernel")
    t2_01(); t2_02(); t2_03(); t2_04(); t2_05()
    t2_06(); t2_07(); t2_08()

    # Phase 3
    phase("Phase 3: Legality Gate")
    t3_01(); t3_02(); t3_03(); t3_04(); t3_05()
    t3_06(); t3_07(); t3_08(); t3_09()

    # Phase 4
    phase("Phase 4: Audit Ledger")
    t4_01(); t4_02(); t4_03(); t4_04(); t4_05(); t4_06()

    # Phase 5
    phase("Phase 5: Timing & Halt")
    t5_01(); t5_02(); t5_03(); t5_04()

    # Phase 6
    phase("Phase 6: Failure Semantics")
    t6_01(); t6_02(); t6_03(); t6_04()

    # Phase 7
    phase("Phase 7: Constitutional Configurator")
    t7_01(); t7_02(); t7_03(); t7_04(); t7_05()

    # Phase 8
    phase("Phase 8: Full Engine Integration")
    t8_01(); t8_02(); t8_03(); t8_04(); t8_05()
    t8_06(); t8_07(); t8_08(); t8_09(); t8_10()

    # Phase 9
    phase("Phase 9: Extension Scaffold")
    t9_01(); t9_02(); t9_03(); t9_04(); t9_05()

    # Adversarial
    phase("Adversarial Scenarios")
    ta_01(); ta_02(); ta_03()

    # Summary
    passed = sum(1 for r in RESULTS if r.passed)
    failed = sum(1 for r in RESULTS if not r.passed)
    total = len(RESULTS)

    print(f"\n{'='*70}")
    print(f"  RESULTS: {passed}/{total} passed, {failed} failed")
    print(f"{'='*70}")

    if failed > 0:
        print("\n  FAILURES:")
        for r in RESULTS:
            if not r.passed:
                print(f"    ✗ {r.name}: {r.detail}")

    print(f"\n  {'ALL INVARIANTS HOLD' if failed == 0 else 'CONSTITUTIONAL VIOLATIONS DETECTED'}")
    print(f"{'='*70}\n")

    return failed == 0


if __name__ == "__main__":
    success = run_all()
    sys.exit(0 if success else 1)
