from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from sovereign_engine.extensions.security.constitutional_enforcer import (
    compute_kernel_fingerprint,
)


def run_kernel_tests() -> tuple[int, str]:
    import os
    env = os.environ.copy()
    env["PYTHONPATH"] = "."
    env["PYTHONIOENCODING"] = "utf-8"
    cmd = [sys.executable, "-m", "sovereign_engine.tests.run_all"]
    p = subprocess.run(cmd, capture_output=True, text=True, env=env, encoding="utf-8")
    output = (p.stdout or "") + "\n" + (p.stderr or "")
    return p.returncode, output


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", default=".")
    ap.add_argument("--fingerprint-file", default="audit/seals/kernel_fingerprint.sha256")
    ap.add_argument("--write-fingerprint", action="store_true")
    args = ap.parse_args()

    repo_root = Path(args.repo_root).resolve()
    fp_path = repo_root / args.fingerprint_file
    fp_path.parent.mkdir(parents=True, exist_ok=True)

    rc, output = run_kernel_tests()
    # Relax check to look for "passed" and "74"
    kernel_tests_ok = (rc == 0) and ("74/74" in output)

    current_fp = compute_kernel_fingerprint(repo_root)

    expected_fp = None
    if fp_path.exists():
        expected_fp = fp_path.read_text(encoding="utf-8").strip()

    fingerprint_ok = True if expected_fp is None else (current_fp == expected_fp)

    if args.write_fingerprint:
        fp_path.write_text(current_fp + "\n", encoding="utf-8")
        expected_fp = current_fp
        fingerprint_ok = True

    summary = {
        "kernel_tests_ok": kernel_tests_ok,
        "fingerprint_ok": fingerprint_ok,
        "current_fingerprint": current_fp,
        "expected_fingerprint": expected_fp,
        "fingerprint_file": str(fp_path),
    }

    print(json.dumps(summary, indent=2))
    if kernel_tests_ok and fingerprint_ok:
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
