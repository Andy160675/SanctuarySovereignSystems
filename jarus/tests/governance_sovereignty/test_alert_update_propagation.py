import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ALERTS_ACKS = ROOT / "Governance" / "alerts" / "acks"
BROADCAST = ROOT / "scripts" / "governance" / "broadcast_alert_update.py"
ACK = ROOT / "scripts" / "governance" / "acknowledge_alert.py"
VERIFY = ROOT / "scripts" / "governance" / "verify_alert_propagation.py"


def run_py(script, *args):
    cmd = [sys.executable, str(script), *args]
    return subprocess.run(cmd, capture_output=True, text=True)


def test_alert_propagation_roundtrip(tmp_path):
    alert_id = "ALERT_TEST_001"

    # Clean any prior residue
    ack_dir = ALERTS_ACKS / alert_id
    if ack_dir.exists():
        shutil.rmtree(ack_dir)

    # Broadcast minimal alert (constructed via flags)
    res = run_py(
        BROADCAST,
        "--alert-id", alert_id,
        "--incident-id", "INC_TEST_123",
        "--observed", "demo near miss",
        "--boundary", "safety.guard.x",
        "--change-type", "guard_patch",
        "--change-summary", "tightened threshold",
        "--origin-node", "MASTER"
    )
    assert res.returncode == 0, res.stderr or res.stdout

    # Required nodes for this test
    required_nodes = ["NODE_A", "NODE_B"]
    rn_path = tmp_path / "required_nodes.json"
    rn_path.write_text(json.dumps(required_nodes), encoding="utf-8")

    # Verify should fail initially (no ACKs)
    res = run_py(VERIFY, alert_id, "--required-nodes", str(rn_path))
    assert res.returncode != 0, "verification should fail without ACKs"

    # ACK by NODE_A only -> still fail
    res_ack = run_py(ACK, alert_id, "--node-id", "NODE_A", "--applied")
    assert res_ack.returncode == 0, res_ack.stderr or res_ack.stdout
    res = run_py(VERIFY, alert_id, "--required-nodes", str(rn_path))
    assert res.returncode != 0, "verification should fail when some ACKs missing"

    # ACK by NODE_B -> now pass
    res_ack2 = run_py(ACK, alert_id, "--node-id", "NODE_B", "--applied")
    assert res_ack2.returncode == 0, res_ack2.stderr or res_ack2.stdout
    res = run_py(VERIFY, alert_id, "--required-nodes", str(rn_path))
    assert res.returncode == 0, res.stdout
