from __future__ import annotations
import argparse
import datetime as dt
import json
import statistics
import subprocess
import sys
import time
from pathlib import Path

def run_once() -> float:
    t0 = time.perf_counter()
    p = subprocess.run(
        [sys.executable, "-m", "sovereign_engine.tests.run_all"],
        capture_output=True,
        text=True
    )
    t1 = time.perf_counter()
    out = (p.stdout or "") + "\n" + (p.stderr or "")
    if p.returncode != 0 or "74/74" not in out:
        raise RuntimeError("Kernel validation failed during baseline run.")
    return t1 - t0

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", type=int, default=3)
    ap.add_argument("--out", default="baseline_metrics.json")
    args = ap.parse_args()

    times = [run_once() for _ in range(args.runs)]
    payload = {
        "timestamp_utc": dt.datetime.utcnow().isoformat() + "Z",
        "command": f"{sys.executable} -m sovereign_engine.tests.run_all",
        "runs": args.runs,
        "build_time_seconds": {
            "samples": times,
            "min": min(times),
            "max": max(times),
            "mean": statistics.mean(times),
            "median": statistics.median(times)
        },
        "test_parallelism": 1,
        "manual_steps_estimate": 2
    }
    Path(args.out).write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Baseline written: {args.out}")
    print(f"Median build time: {payload['build_time_seconds']['median']:.3f}s")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
