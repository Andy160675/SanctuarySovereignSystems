from sovereign_engine.extensions.observatory.instrumentation import collect_runtime_snapshot

def test_collect_runtime_snapshot_has_required_keys():
    s = collect_runtime_snapshot()
    for k in ("timestamp_utc", "python_version", "platform", "implementation"):
        assert k in s