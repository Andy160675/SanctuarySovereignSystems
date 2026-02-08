from sovereign_engine.extensions.boardroom.kernel_guard import scan_decision_for_kernel_risk

def test_guard_detects_kernel_mutation_language():
    flags = scan_decision_for_kernel_risk("We should modify kernel and bypass invariants for speed")
    assert len(flags) >= 2
