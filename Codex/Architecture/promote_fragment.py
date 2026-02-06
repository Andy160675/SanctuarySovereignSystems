#!/usr/bin/env python3
"""
Fragment Promotion Tool — proposed -> canonical

Append-only: writes a JSONL receipt to governance/promotion_ledger.jsonl
containing: id, content_hash, who, when, reason, receipt_id

Usage:
  python promote_fragment.py --evidence ./evidence --id CSS.ARCH.001 --reason "validated by review" [--who you]

Note: Does NOT edit evidence files. Canonicality is a state transition recorded
in the ledger. The assembler will treat a fragment as canonical if a matching
(id, content_hash) receipt exists.
"""
import argparse
import getpass
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
import re

BLOCK_RE = re.compile(r"@block\s+(.*?)\n(.*?)@end", re.DOTALL)
META_RE = re.compile(r"(\w+)=(\S+)")

def find_fragment(evidence_dir: str, target_id: str):
    base = Path(evidence_dir)
    for fp in sorted(base.rglob('*')):
        if fp.is_dir():
            continue
        try:
            text = fp.read_text(encoding='utf-8')
        except Exception:
            continue
        for m in BLOCK_RE.finditer(text):
            header = m.group(1).strip()
            content = m.group(2).strip()
            meta = dict(META_RE.findall(header))
            if meta.get('id') == target_id:
                ch = hashlib.sha256(content.encode()).hexdigest()[:16]
                return {
                    'id': target_id,
                    'content': content,
                    'content_hash': ch,
                    'source_file': str(fp)
                }
    return None


def main():
    ap = argparse.ArgumentParser(description='Promote fragment to canonical (append-only receipt)')
    ap.add_argument('--evidence', required=True, help='Path to evidence directory')
    ap.add_argument('--id', required=True, help='Fragment block id to promote')
    ap.add_argument('--reason', required=True, help='Reason/evidence summary for promotion')
    ap.add_argument('--who', default=None, help='Promoter identity (default: current user)')
    ap.add_argument('--ledger', default='./governance/promotion_ledger.jsonl', help='Path to promotion ledger JSONL')
    args = ap.parse_args()

    frag = find_fragment(args.evidence, args.id)
    if not frag:
        raise SystemExit(f"Fragment id not found in evidence: {args.id}")

    who = args.who or getpass.getuser()
    when = datetime.now(timezone.utc).isoformat()

    receipt_seed = f"{frag['id']}|{frag['content_hash']}|{who}|{when}|{args.reason}".encode('utf-8')
    receipt_id = hashlib.sha256(receipt_seed).hexdigest()[:16]

    record = {
        'receipt_id': receipt_id,
        'id': frag['id'],
        'content_hash': frag['content_hash'],
        'who': who,
        'when': when,
        'reason': args.reason,
        'source_file': frag['source_file'],
    }

    ledger_path = Path(args.ledger)
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    with ledger_path.open('a', encoding='utf-8') as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

    print(f"Promoted {frag['id']}@{frag['content_hash']} -> canonical")
    print(f"Receipt: {record['receipt_id']} | Ledger: {ledger_path}")

if __name__ == '__main__':
    main()
