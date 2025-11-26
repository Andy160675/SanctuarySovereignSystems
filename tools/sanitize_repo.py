#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SOVEREIGN SANITIZER v1.0

Purpose:
  - Scan the repo for obvious secrets / PII-like patterns.
  - Emit a machine-readable report.
  - Optionally rewrite files with redaction tokens.

Defaults:
  - Dry-run (no modifications) unless --rewrite is passed.
  - Skips common build/output dirs and large/binary files.

Usage:
  # Dry-run (see what would be redacted)
  python tools/sanitize_repo.py --root .

  # Apply redactions in-place
  python tools/sanitize_repo.py --root . --rewrite
"""

import argparse
import json
import os
import re
from pathlib import Path
from typing import Dict, Any, List, Tuple

# --- Patterns: tune conservatively (better false positive than false negative) ---

PATTERNS: Dict[str, re.Pattern] = {
    # Generic "looks like a key" (32+ hex chars)
    "hex_secret": re.compile(r"\b[0-9a-fA-F]{32,64}\b"),
    # Email addresses
    "email": re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
    # UK-ish phone (very rough)
    "phone_uk": re.compile(r"\b\+?44\s?\d[\d\s\-]{7,}\b"),
    # Obvious API key-ish strings (e.g. starting with 'sk_' etc.)
    "api_key_like": re.compile(r"\b(sk|pk|AKIA|AIza|xoxb)-[A-Za-z0-9\-_]{8,}\b"),
    # Simple IPv4 (excluding common safe ones like 127.0.0.1, 0.0.0.0)
    "ipv4": re.compile(r"\b(?!127\.0\.0\.1|0\.0\.0\.0|localhost)(?:\d{1,3}\.){3}\d{1,3}\b"),
    # AWS account ID pattern
    "aws_account": re.compile(r"\b\d{12}\b"),
}

# Patterns to explicitly SKIP (known safe patterns that look like secrets)
SAFE_PATTERNS = [
    # SHA-256 hashes in anchor chain (these are supposed to be there)
    re.compile(r'"(payload_hash|chain_hash|prev_chain_hash)":\s*"[0-9a-fA-F]{64}"'),
    # Git commit hashes
    re.compile(r"\b[0-9a-f]{40}\b"),
    # Known safe emails
    re.compile(r"noreply@anthropic\.com"),
    re.compile(r"example\.com"),
]

DEFAULT_EXCLUDE_DIRS = {
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    ".mypy_cache",
    ".pytest_cache",
    ".idea",
    ".vs",
    ".vscode",
    "node_modules",
    "dist",
    "build",
    ".eggs",
    # Sovereign-specific excludes
    "boardroom-shell-complete",
    "elite-truth",
    "boardroom-poc",
    "sovereign-core",
    "truth-engine-complete",
}

TEXT_EXTENSIONS = {
    ".py", ".md", ".txt", ".json", ".yml", ".yaml",
    ".toml", ".ini", ".cfg", ".sh", ".ps1", ".psm1",
    ".js", ".ts", ".tsx", ".css", ".html", ".bat",
}

MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024  # 5MB


def is_text_like(path: Path) -> bool:
    if path.suffix.lower() in TEXT_EXTENSIONS:
        return True
    # Fallback: small heuristic peek
    try:
        chunk = path.read_bytes()[:1024]
        if b"\0" in chunk:
            return False
        return True
    except Exception:
        return False


def is_safe_match(text: str, match: re.Match) -> bool:
    """Check if match is in a known-safe context."""
    # Get surrounding context
    start = max(0, match.start() - 50)
    end = min(len(text), match.end() + 50)
    context = text[start:end]

    for safe_pattern in SAFE_PATTERNS:
        if safe_pattern.search(context):
            return True
    return False


def find_matches(text: str) -> List[Tuple[str, List[Tuple[int, str]]]]:
    results: List[Tuple[str, List[Tuple[int, str]]]] = []
    for name, pattern in PATTERNS.items():
        hits: List[Tuple[int, str]] = []
        for m in pattern.finditer(text):
            # Skip known-safe matches
            if is_safe_match(text, m):
                continue
            # Record line index + snippet
            idx = text.count("\n", 0, m.start())
            snippet = text[m.start():m.end()]
            hits.append((idx + 1, snippet))
        if hits:
            results.append((name, hits))
    return results


def apply_redactions(text: str) -> str:
    redacted = text
    for name, pattern in PATTERNS.items():
        def replace_if_not_safe(m: re.Match) -> str:
            if is_safe_match(text, m):
                return m.group(0)
            return f"{{{{REDACTED_{name.upper()}}}}}"
        redacted = pattern.sub(replace_if_not_safe, redacted)
    return redacted


def sanitize_repo(
    root: Path,
    dry_run: bool = True,
    report_path: Path = Path("tools") / "sanitize_report.json",
) -> Dict[str, Any]:
    report: Dict[str, Any] = {
        "root": str(root),
        "dry_run": dry_run,
        "files_scanned": 0,
        "files_with_hits": 0,
        "files_modified": 0,
        "hits": [],
    }

    root = root.resolve()

    for dirpath, dirnames, filenames in os.walk(root):
        # Skip excluded dirs
        dirnames[:] = [d for d in dirnames if d not in DEFAULT_EXCLUDE_DIRS]

        for fname in filenames:
            path = Path(dirpath) / fname

            # Skip if in excluded dir (double check)
            rel_parts = path.relative_to(root).parts
            if any(part in DEFAULT_EXCLUDE_DIRS for part in rel_parts):
                continue

            # Skip obvious binary / large
            try:
                size = path.stat().st_size
            except (FileNotFoundError, PermissionError):
                continue

            if size > MAX_FILE_SIZE_BYTES:
                continue
            if not is_text_like(path):
                continue

            report["files_scanned"] += 1

            try:
                text = path.read_text(encoding="utf-8")
            except Exception:
                continue

            matches = find_matches(text)
            if not matches:
                continue

            report["files_with_hits"] += 1
            rel_path = path.relative_to(root)

            file_entry: Dict[str, Any] = {
                "path": str(rel_path),
                "size": size,
                "matches": [],
            }

            for pattern_name, hits in matches:
                file_entry["matches"].append({
                    "pattern": pattern_name,
                    "count": len(hits),
                    "hits": [{"line": line_no, "snippet": snippet[:50]} for line_no, snippet in hits[:10]],
                })

            if not dry_run:
                redacted = apply_redactions(text)
                if redacted != text:
                    path.write_text(redacted, encoding="utf-8")
                    report["files_modified"] += 1

            report["hits"].append(file_entry)

    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def main():
    parser = argparse.ArgumentParser(
        description="Sovereign repo sanitizer (scan + optional redact)."
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path("."),
        help="Repository root (default: current directory).",
    )
    parser.add_argument(
        "--rewrite",
        action="store_true",
        help="Apply redactions in-place. Default is dry-run only.",
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=Path("tools") / "sanitize_report.json",
        help="Path to write JSON report.",
    )

    args = parser.parse_args()
    report = sanitize_repo(args.root, dry_run=not args.rewrite, report_path=args.report)

    mode = "DRY-RUN" if not args.rewrite else "REWRITE"
    print(f"[SANITIZE] Mode: {mode}")
    print(f"[SANITIZE] Root: {report['root']}")
    print(f"[SANITIZE] Files scanned: {report['files_scanned']}")
    print(f"[SANITIZE] Files with hits: {report['files_with_hits']}")
    print(f"[SANITIZE] Files modified: {report['files_modified']}")
    print(f"[SANITIZE] Report: {args.report}")

    if report["hits"]:
        print(f"\n[SANITIZE] Summary of findings:")
        for hit in report["hits"][:10]:
            print(f"  - {hit['path']}: {sum(m['count'] for m in hit['matches'])} potential issues")
        if len(report["hits"]) > 10:
            print(f"  ... and {len(report['hits']) - 10} more files")


if __name__ == "__main__":
    main()
