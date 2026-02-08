import argparse
import json
import sys
from pathlib import Path

from .claude_client import ClaudeBoardroomClient
from .engine import BoardroomEngine
from .audit import write_audit


def main():
    p = argparse.ArgumentParser(description="S3-EXT-010 Boardroom deliberation runner")
    p.add_argument("--decision", required=True, help="Decision text")
    p.add_argument("--context-file", default="", help="Optional path to context text/json")
    p.add_argument("--model", default="claude-3-5-sonnet-latest")
    p.add_argument("--workers", type=int, default=13)
    args = p.parse_args()

    context = ""
    if args.context_file:
        cpath = Path(args.context_file)
        if not cpath.exists():
            raise SystemExit(f"context file not found: {cpath}")
        context = cpath.read_text(encoding="utf-8")

    client = ClaudeBoardroomClient(model=args.model)
    engine = BoardroomEngine(client=client, max_workers=args.workers)
    bundle = engine.deliberate(decision=args.decision, context=context)
    out_dir = write_audit(bundle)

    print(f"Final: {bundle.final.final.value} | {bundle.final.reason} | score={bundle.final.score}")
    print(f"Distribution: {json.dumps(bundle.final.distribution)}")
    if bundle.final.vetoes:
        print(f"Vetoes: {bundle.final.vetoes}")
    print(f"Evidence: {out_dir}")

    # Non-zero on hard stop for CI gating
    if bundle.final.final.value == "HALT":
        sys.exit(2)


if __name__ == "__main__":
    main()
