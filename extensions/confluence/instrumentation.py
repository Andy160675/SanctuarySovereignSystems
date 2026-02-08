from __future__ import annotations
from datetime import datetime, timezone
from typing import Dict, Any
import platform
import sys

def collect_runtime_snapshot() -> Dict[str, Any]:
    return {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "python_version": sys.version.split()[0],
        "platform": platform.platform(),
        "implementation": platform.python_implementation(),
    }
