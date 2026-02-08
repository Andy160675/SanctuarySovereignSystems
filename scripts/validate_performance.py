from __future__ import annotations
import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

def run_current() -> float:
    t0 = time.perf_counter()
    p = subprocess.run(
        [sys.executable, "-m", "sovereign_engine.tests.run_all"],
        capture_output=True,
        text=True
    )
    t1 = time.perf_counter()
    out = (p.stdout or "") + "\n" + (p.stderr or "")
    if p.returncode != 0 or "74/74" not in out:
        raise RuntimeError("Kernel validation failed during performance validation.")
    return t1 - t0

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--baseline", default="baseline_metrics.json")
    ap.add_argument("--out", default="current_metrics.json")
    ap.add_argument("--threshold", choices=["no_regression", "x10"], default="no_regression")
    args = ap.parse_args()

    b = json.loads(Path(args.baseline).read_text(encoding="utf-8"))
    base = float(b["build_time_seconds"]["median"])
    cur = run_current()

    if args.threshold == "no_regression":
        limit = base * 1.05
        ok = cur <= limit
    else:  # x10
        limit = base / 10.0
        ok = cur <= limit

    result = {
        "baseline_median_s": base,
        "current_s": cur,
        "threshold_mode": args.threshold,
        "limit_s": limit,
        "pass": ok
    }
    Path(args.out).write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0 if ok else 1

if __name__ == "__main__":
    raise SystemExit(main())
