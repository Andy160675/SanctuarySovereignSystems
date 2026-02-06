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

            fragments[block_id] = {
                'id': block_id,
                'domain': meta.get('domain', 'UNKNOWN'),
                'type': meta.get('type', 'unknown'),
                'weight': meta.get('weight', 'provisional'),
                'content': content,
                'source_file': str(filepath),
                'content_hash': hashlib.sha256(content.encode()).hexdigest()[:16],
            }

    return fragments


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

    # Strip template header (everything before first ---)
    parts = template_text.split('---', 1)
    body = parts[1] if len(parts) > 1 else template_text

    # Replace block references with content
    ref_pattern = re.compile(r'\[([a-zA-Z0-9_.]+)\]')
    missing = []
    used = []

    def replace_ref(match):
        block_id = match.group(1)
        if block_id in fragments:
            used.append(block_id)
            return fragments[block_id]['content']
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
        "| Block ID | Domain | Type | Weight | Source File | Content Hash |",
        "|----------|--------|------|--------|------------|-------------|",
    ]

    for block_id in used:
        f = fragments[block_id]
        manifest_lines.append(
            f"| `{f['id']}` | {f['domain']} | {f['type']} "
            f"| {f['weight']} | `{os.path.basename(f['source_file'])}` "
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
    args = parser.parse_args()

    # Ensure output dir exists
    Path(args.output).mkdir(parents=True, exist_ok=True)

    # Step 1: Parse all evidence fragments
    print(f"Scanning evidence: {args.evidence}")
    fragments = parse_fragments(args.evidence)
    print(f"  Found {len(fragments)} tagged fragments")

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
