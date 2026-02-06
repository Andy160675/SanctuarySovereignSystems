#!/usr/bin/env python3
"""
Doctrine Assembler v0.1
Codex Sovereign Systems

Assembles doctrine documents from tagged evidence blocks.
The one invariant: doctrine is assembled, not rewritten.

Usage:
    python assemble.py --evidence ./evidence/ --template ./templates/CSS-ARCH-DOC-001.template --output ./builds/
"""

import os
import re
import hashlib
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


# --- Layer 1: Fragment Parser ---

def parse_fragments(evidence_dir):
    """Scan all files in evidence_dir for @block/@end tagged fragments."""
    fragments = {}
    block_pattern = re.compile(
        r'@block\s+(.*?)\n(.*?)@end',
        re.DOTALL
    )
    meta_pattern = re.compile(r'(\w+)=(\S+)')

    evidence_path = Path(evidence_dir)
    for filepath in sorted(evidence_path.rglob('*')):
        if filepath.is_dir():
            continue
        try:
            text = filepath.read_text(encoding='utf-8')
        except (UnicodeDecodeError, PermissionError):
            continue

        for match in block_pattern.finditer(text):
            header = match.group(1).strip()
            content = match.group(2).strip()
            meta = dict(meta_pattern.findall(header))

            block_id = meta.get('id')
            if not block_id:
                continue

            weight = meta.get('weight', 'proposed')
            fragments[block_id] = {
                'id': block_id,
                'domain': meta.get('domain', 'UNKNOWN'),
                'type': meta.get('type', 'unknown'),
                'weight': weight,
                'effective_weight': weight,  # may be promoted by ledger
                'content': content,
                'source_file': str(filepath),
                'content_hash': hashlib.sha256(content.encode()).hexdigest()[:16],
            }

    return fragments


# Promotion ledger loader — append-only JSONL of promotions
# Each line: {"id": "block.id", "content_hash": "abcd1234", "who": "name", "when": "iso8601", "reason": "...", "receipt_id": "..."}

def load_promotions(ledger_path: str) -> dict[tuple[str, str], str]:
    """Returns {(block_id, content_hash): receipt_id} mapping."""
    promotions: dict[tuple[str, str], str] = {}
    p = Path(ledger_path)
    if not p.exists():
        return promotions
    try:
        for line in p.read_text(encoding='utf-8').splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
                bid = rec.get('id')
                ch = rec.get('content_hash')
                rid = rec.get('receipt_id')
                if bid and ch and rid:
                    promotions[(bid, ch)] = rid
            except json.JSONDecodeError:
                continue
    except Exception:
        pass
    return promotions

# --- Layer 2: Deterministic Assembly ---

def assemble_document(template_path, fragments):
    """
    Read a template file. Replace [block.id] references with fragment content.
    No summarization. No rewriting. Just composition.
    """
    template_text = Path(template_path).read_text(encoding='utf-8')

    # Extract metadata from template header
    doc_meta = {}
    for line in template_text.split('\n'):
        if line.startswith('title:'):
            doc_meta['title'] = line.split(':', 1)[1].strip()
        elif line.startswith('doc_id:'):
            doc_meta['doc_id'] = line.split(':', 1)[1].strip()
        elif line.startswith('version:'):
            doc_meta['version'] = line.split(':', 1)[1].strip()
        elif line.startswith('allow_proposed:'):
            val = line.split(':', 1)[1].strip().lower()
            doc_meta['allow_proposed'] = val in ('1', 'true', 'yes', 'y')

    # Strip template header (everything before first ---)
    parts = template_text.split('---', 1)
    body = parts[1] if len(parts) > 1 else template_text

    # Replace block references with content
    ref_pattern = re.compile(r'\[([a-zA-Z0-9_.]+)\]')
    missing = []
    used = []

    allow_proposed = bool(doc_meta.get('allow_proposed', False))

    def replace_ref(match):
        block_id = match.group(1)
        if block_id in fragments:
            f = fragments[block_id]
            # Only include canonical unless template explicitly allows proposed
            if f.get('effective_weight', f.get('weight')) != 'canonical' and not allow_proposed:
                missing.append(block_id)
                return f'**[BLOCK NOT CANONICAL: {block_id}]**'
            used.append(block_id)
            return f['content']
        else:
            missing.append(block_id)
            return f'**[MISSING: {block_id}]**'

    assembled = ref_pattern.sub(replace_ref, body)

    return assembled, doc_meta, used, missing


def generate_build_manifest(doc_meta, fragments, used, missing, template_path):
    """Generate a build manifest for traceability."""
    now = datetime.now(timezone.utc).isoformat()

    manifest_lines = [
        f"# Build Manifest: {doc_meta.get('doc_id', 'UNKNOWN')}",
        f"**Version:** {doc_meta.get('version', '0.0.0')}",
        f"**Built:** {now}",
        f"**Template:** {template_path}",
        f"**Fragments used:** {len(used)}",
        f"**Fragments missing:** {len(missing)}",
        "",
        "## Fragment Provenance",
        "",
        "| Block ID | Domain | Type | Weight | Receipt ID | Source File | Content Hash |",
        "|----------|--------|------|--------|------------|-------------|-------------|",
    ]

    for block_id in used:
        f = fragments[block_id]
        receipt_id = f.get('receipt_id', 'N/A')
        manifest_lines.append(
            f"| `{f['id']}` | {f['domain']} | {f['type']} "
            f"| {f.get('effective_weight', f['weight'])} | `{receipt_id}` "
            f"| `{os.path.basename(f['source_file'])}` "
            f"| `{f['content_hash']}` |"
        )

    if missing:
        manifest_lines.extend([
            "",
            "## Missing Fragments",
            "",
        ])
        for block_id in missing:
            manifest_lines.append(f"- `{block_id}` — **NOT FOUND** in evidence")

    # Document-level hash (assembled content integrity)
    return '\n'.join(manifest_lines)


# --- Layer 3: Output ---

def build_header(doc_meta):
    """Generate document header from metadata."""
    title = doc_meta.get('title', 'Untitled Doctrine Document')
    doc_id = doc_meta.get('doc_id', '')
    version = doc_meta.get('version', '')
    now = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')

    return (
        f"# {title}\n\n"
        f"**Document:** {doc_id} | **Version:** {version} | "
        f"**Assembled:** {now}\n\n"
        f"*This document is mechanically assembled from tagged evidence "
        f"blocks. Do not edit directly. Edit source fragments and "
        f"reassemble.*\n\n"
        f"---\n"
    )


def main():
    parser = argparse.ArgumentParser(description='Doctrine Assembler v0.1')
    parser.add_argument('--evidence', required=True, help='Path to evidence directory')
    parser.add_argument('--template', required=True, help='Path to assembly template')
    parser.add_argument('--output', required=True, help='Output directory for built docs')
    parser.add_argument('--promotion-ledger', default='./governance/promotion_ledger.jsonl', help='Path to promotion ledger JSONL')
    args = parser.parse_args()

    # Ensure output dir exists
    Path(args.output).mkdir(parents=True, exist_ok=True)

    # Step 1: Parse all evidence fragments
    print(f"Scanning evidence: {args.evidence}")
    fragments = parse_fragments(args.evidence)
    print(f"  Found {len(fragments)} tagged fragments")

    # Apply promotion ledger to compute effective weights
    promotions = load_promotions(args.promotion_ledger)
    for fid, f in fragments.items():
        rid = promotions.get((fid, f['content_hash']))
        if f['weight'] == 'canonical' or rid:
            f['effective_weight'] = 'canonical'
            if rid:
                f['receipt_id'] = rid
        else:
            f['effective_weight'] = 'proposed'

    # Step 2: Assemble from template
    print(f"Assembling from: {args.template}")
    assembled, doc_meta, used, missing = assemble_document(args.template, fragments)
    print(f"  Used {len(used)} fragments, {len(missing)} missing")

    # Step 3: Generate outputs
    doc_id = doc_meta.get('doc_id', 'output')

    # Main document
    header = build_header(doc_meta)
    full_doc = header + assembled
    doc_path = Path(args.output) / f"{doc_id}.md"
    doc_path.write_text(full_doc, encoding='utf-8')
    print(f"  Document: {doc_path}")

    # Build manifest (provenance)
    manifest = generate_build_manifest(doc_meta, fragments, used, missing, args.template)
    manifest_path = Path(args.output) / f"{doc_id}.manifest.md"
    manifest_path.write_text(manifest, encoding='utf-8')
    print(f"  Manifest: {manifest_path}")

    # Document hash
    doc_hash = hashlib.sha256(full_doc.encode()).hexdigest()
    print(f"  Document hash: {doc_hash[:16]}")

    if missing:
        print(f"\n  ⚠ WARNING: {len(missing)} missing fragments:")
        for m in missing:
            print(f"    - {m}")

    print("\nAssembly complete.")


if __name__ == '__main__':
    main()
