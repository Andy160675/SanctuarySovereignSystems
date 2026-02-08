from __future__ import annotations
from pathlib import Path
from typing import Dict, Any
import json

def export_snapshot_json(snapshot: Dict[str, Any], out_file: str) -> str:
    p = Path(out_file)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(snapshot, indent=2, sort_keys=True), encoding="utf-8")
    return str(p)
