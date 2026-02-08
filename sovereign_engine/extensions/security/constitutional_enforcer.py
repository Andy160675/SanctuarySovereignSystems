from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import Iterable, List


IMMUTABLE_PATHS = [
    "sovereign_engine/core/",
    "sovereign_engine/configs/constitution.json",
    "INVARIANTS.md",
    "SEASONS.md",
    "ROADMAP.md",
]


def _norm(path: str) -> str:
    return path.replace("\\", "/").lstrip("./")


def _is_under(path: str, immutable: str) -> bool:
    p = _norm(path)
    i = _norm(immutable)
    if i.endswith("/"):
        return p.startswith(i)
    return p == i


def _iter_files(root: Path, paths: Iterable[str]) -> List[Path]:
    out: List[Path] = []
    for rel in paths:
        p = root / rel
        if p.is_file():
            out.append(p)
        elif p.is_dir():
            for f in sorted(p.rglob("*")):
                if f.is_file():
                    out.append(f)
    return sorted(out)


def compute_kernel_fingerprint(
    repo_root: str | Path = ".",
    immutable_paths: Iterable[str] = IMMUTABLE_PATHS,
) -> str:
    root = Path(repo_root).resolve()
    files = _iter_files(root, immutable_paths)
    h = sha256()
    for f in files:
        rel = f.relative_to(root).as_posix()
        b = f.read_bytes()
        fh = sha256(b).hexdigest()
        h.update(f"{rel}:{fh}\n".encode("utf-8"))
    return h.hexdigest()


@dataclass
class EnforcementResult:
    allowed: bool
    reasons: List[str]
    current_fingerprint: str


class ConstitutionalEnforcer:
    def __init__(
        self,
        expected_kernel_fingerprint: str,
        immutable_paths: Iterable[str] = IMMUTABLE_PATHS,
        required_invariant_phrase: str = "74/74",
    ) -> None:
        self.expected_kernel_fingerprint = expected_kernel_fingerprint
        self.immutable_paths = list(immutable_paths)
        self.required_invariant_phrase = required_invariant_phrase
        self.blocked_event_types = {"kernel_mutation", "policy_override"}

    def validate(
        self,
        repo_root: str | Path,
        event_type: str,
        changed_files: Iterable[str],
        invariant_output: str,
    ) -> EnforcementResult:
        reasons: List[str] = []

        current = compute_kernel_fingerprint(repo_root, self.immutable_paths)
        if current != self.expected_kernel_fingerprint:
            reasons.append("Kernel fingerprint mismatch")

        if self.required_invariant_phrase not in invariant_output:
            reasons.append("Invariant proof missing required phrase")

        for f in changed_files:
            for immutable in self.immutable_paths:
                if _is_under(f, immutable):
                    reasons.append(f"Immutable path modified: {f}")
                    break

        if event_type in self.blocked_event_types:
            reasons.append(f"Blocked event_type: {event_type}")

        return EnforcementResult(
            allowed=(len(reasons) == 0),
            reasons=reasons,
            current_fingerprint=current,
        )
