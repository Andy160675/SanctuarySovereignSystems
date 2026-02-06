import os
import asyncio
import json
from datetime import datetime
from pathlib import Path
import argparse

# Ensure we can import trinity backend classes when run as a script
from trinity_backend import TrinityOrchestrator

DEFAULT_TOTAL = 12000
DEFAULT_CONCURRENCY = int(os.getenv("TRINITY_MAX_CONCURRENCY", "2000"))  # per-node safe default


def now_ts():
    return datetime.utcnow().strftime("%Y-%m-%dT%H-%M-%SZ")


async def run_one(orchestrator: TrinityOrchestrator, case_id: str, query: str):
    return await orchestrator.run_case(case_id=case_id, query=query)


async def bounded_runner(total: int, concurrency: int, query: str, out_path: Path):
    sem = asyncio.Semaphore(concurrency)
    orch = TrinityOrchestrator()

    async def task(i: int):
        case_id = f"CASE-{i:06d}"
        async with sem:
            result = await run_one(orch, case_id=case_id, query=query)
            line = json.dumps({
                "ts": datetime.utcnow().isoformat() + "Z",
                "case_id": case_id,
                "query": query,
                "success": result.get("success"),
                "summary": result.get("summary"),
                "svc": result.get("svc"),
            }, ensure_ascii=False)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            with out_path.open("a", encoding="utf-8") as f:
                f.write(line + "\n")

    await asyncio.gather(*(task(i) for i in range(1, total + 1)))


def main():
    parser = argparse.ArgumentParser(description="Run a bounded Trinity campaign and write JSONL results.")
    parser.add_argument("--total", type=int, default=DEFAULT_TOTAL, help="Total number of cases to run (default 12000)")
    parser.add_argument("--concurrency", type=int, default=DEFAULT_CONCURRENCY, help="Max concurrent cases (default from TRINITY_MAX_CONCURRENCY or 2000)")
    parser.add_argument("--query", type=str, default="system sweep", help="Query phrase to seed investigations")
    parser.add_argument("--out", type=str, default=str(Path("evidence")/"campaigns"/f"trinity_campaign_{now_ts()}.jsonl"), help="Output JSONL file")
    parser.add_argument("--auditOnly", action="store_true", help="Set TRINITY_AUDIT_ONLY=1 to prevent actuation")

    args = parser.parse_args()

    if args.auditOnly:
        os.environ["TRINITY_AUDIT_ONLY"] = "1"

    # Hard governance cap guard
    if args.concurrency > 5000:
        print("[WARN] Concurrency capped at 5000 for safety.")
        args.concurrency = 5000

    out_path = Path(args.out)
    print(f"[INFO] Starting Trinity campaign: total={args.total}, concurrency={args.concurrency}, auditOnly={'1' if args.auditOnly else '0'}")
    print(f"[INFO] Output: {out_path}")

    asyncio.run(bounded_runner(args.total, args.concurrency, args.query, out_path))

    print("[INFO] Campaign complete.")


if __name__ == "__main__":
    main()
