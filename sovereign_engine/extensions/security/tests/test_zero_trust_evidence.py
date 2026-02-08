import json
import tempfile
import unittest
from pathlib import Path

from sovereign_engine.extensions.security.zero_trust_evidence import ZeroTrustEvidenceChain


class TestZeroTrustEvidenceChain(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.ledger = Path(self.tmp.name) / "ledger.jsonl"
        self.secret_map = {"boardroom-key": b"super-secret"}
        self.chain = ZeroTrustEvidenceChain(
            ledger_path=self.ledger,
            allowed_sources={"boardroom", "merge_gate"},
            secret_resolver=lambda key_id: self.secret_map[key_id],
            pow_difficulty=2,  # faster test
        )

    def tearDown(self):
        self.tmp.cleanup()

    def test_append_and_verify(self):
        rec = self.chain.append(
            event_type="boardroom_decision",
            source_id="boardroom",
            content={"decision_id": "d-1", "verdict": "APPROVE"},
            key_id="boardroom-key",
        )
        self.assertEqual(rec.source_id, "boardroom")
        ok, errors = self.chain.verify_chain()
        self.assertTrue(ok)
        self.assertEqual(errors, [])

    def test_tamper_detection(self):
        self.chain.append(
            event_type="boardroom_decision",
            source_id="boardroom",
            content={"decision_id": "d-2", "verdict": "REJECT"},
            key_id="boardroom-key",
        )

        lines = self.ledger.read_text(encoding="utf-8").splitlines()
        obj = json.loads(lines[0])
        obj["content"]["verdict"] = "APPROVE"  # tamper content
        lines[0] = json.dumps(obj)
        self.ledger.write_text("\n".join(lines) + "\n", encoding="utf-8")

        ok, errors = self.chain.verify_chain()
        self.assertFalse(ok)
        self.assertTrue(any("invalid signature" in e or "invalid record_hash" in e for e in errors))


if __name__ == "__main__":
    unittest.main()
