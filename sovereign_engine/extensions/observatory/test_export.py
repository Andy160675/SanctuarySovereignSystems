from sovereign_engine.extensions.observatory.export import export_snapshot_json

def test_export_snapshot_json_writes_file(tmp_path):
    out = tmp_path / "telemetry" / "snapshot.json"
    path = export_snapshot_json({"ok": True}, str(out))
    assert out.exists()
    assert path.endswith("snapshot.json")