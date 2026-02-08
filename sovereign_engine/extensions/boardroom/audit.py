import json
import hashlib
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from .models import DecisionBundle


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def write_audit(bundle: DecisionBundle, base: str = "audit/boardroom") -> Path:
    ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    out_dir = Path(base) / ts
    out_dir.mkdir(parents=True, exist_ok=True)

    payload = {
        "timestamp_utc": ts,
        "decision": bundle.decision,
        "context": bundle.context,
        "model": bundle.model,
        "final": bundle.final.to_dict(),
        "agents": [a.to_dict() for a in bundle.agents],
    }

    verdict_path = out_dir / "BOARDROOM_VERDICT.json"
    verdict_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    manifest = {
        "BOARDROOM_VERDICT.json": _sha256(verdict_path),
    }
    manifest_path = out_dir / "MANIFEST_SHA256.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    return out_dir
