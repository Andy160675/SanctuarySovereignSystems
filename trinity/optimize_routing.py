import json
from pathlib import Path
import argparse


def analyze(jsonl_path: Path):
    total = 0
    successes = 0
    evidence_sum = 0
    mismatches_sum = 0

    with jsonl_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            total += 1
            try:
                obj = json.loads(line)
            except Exception:
                continue
            if obj.get("success"):
                successes += 1
                summary = obj.get("summary") or {}
                evidence_sum += int(summary.get("evidence_found", 0))
                # best-effort for mismatch count
                # sometimes in svc we logged mismatch_count under "mismatch_count"
                mismatches_sum += int(summary.get("mismatch_count", 0))

    avg_evidence = (evidence_sum / successes) if successes else 0
    avg_mismatches = (mismatches_sum / successes) if successes else 0
    success_rate = (successes / total) if total else 0

    policy = {
        "version": 1,
        "source": str(jsonl_path),
        "stats": {
            "total_runs": total,
            "success_rate": success_rate,
            "avg_evidence_found": avg_evidence,
            "avg_mismatches": avg_mismatches,
        },
        # Simple heuristic policy proposal: if mismatches low, keep default; else increase verification rigor
        "routing": {
            "investigator": {
                "query_boost": 1.0 if avg_evidence >= 5 else 1.2
            },
            "verifier": {
                "rigor_level": "high" if avg_mismatches > 0.5 else "standard"
            },
            "guardian": {
                "actuation": "audit-only"
            }
        }
    }

    return policy


def main():
    parser = argparse.ArgumentParser(description="Generate an optimized routing policy from Trinity campaign JSONL.")
    parser.add_argument("jsonl", type=str, help="Input JSONL produced by run_campaign.py")
    parser.add_argument("--out", type=str, default=str(Path("CONFIG")/"routing.optimized.json"), help="Output policy file")
    args = parser.parse_args()

    policy = analyze(Path(args.jsonl))

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(policy, f, indent=2)

    print(f"[INFO] Optimized routing written to {out_path}")


if __name__ == "__main__":
    main()
