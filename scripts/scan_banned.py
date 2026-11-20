#!/usr/bin/env python3
"""Scan hand-written sources for patterns banned by the project rules.

Rules:
  - Python: explicit ``Any``, ``# type: ignore``
  - TypeScript/Svelte: explicit ``any``, ``@ts-*`` suppression comments
  - Frontend: imports that traverse parent directories, hardcoded colors

Exit codes: 0 clean, 1 violations found, 2 internal error.
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, Pattern, Sequence

ROOT = Path(__file__).resolve().parents[1]
FRONTEND_SOURCE = ROOT / "frontend" / "src"
BACKEND_SOURCE = ROOT / "backend"

EXCLUDED_DIRECTORY_NAMES = {
    ".venv",
    "node_modules",
    "__pycache__",
    ".mypy_cache",
    ".pytest_cache",
    "dist",
    ".db",
}

# Generated shadcn components are not hand-written and must not be edited.
GENERATED_FRONTEND_COMPONENTS = FRONTEND_SOURCE / "lib" / "components" / "ui"

FRONTEND_SUFFIXES = {".ts", ".js", ".svelte"}
COLOR_SUFFIXES = {".ts", ".svelte"}

# Three.js material and light colors are GPU parameters, not CSS design tokens.
COLOR_ALLOWLIST = {
    "frontend/src/pages/seatmap/scene-model.ts",
    "frontend/src/pages/seatmap/VenueScene.svelte",
}

PYTHON_RULES: tuple[tuple[str, Pattern[str]], ...] = (
    ("python-any", re.compile(r"\bAny\b")),
    ("python-type-ignore", re.compile(r"#\s*type:\s*ignore")),
)

FRONTEND_RULES: tuple[tuple[str, Pattern[str]], ...] = (
    ("ts-any", re.compile(r"(?::\s*any\b|\bas\s+any\b|<any>|\bany\[\])")),
    ("ts-suppress", re.compile(r"@ts-(?:ignore|expect-error|nocheck)\b")),
    (
        "relative-import",
        re.compile(
            r"(?:\bfrom\s+|\bimport\s*\(\s*|\bimport\s+|\brequire\s*\(\s*)['\"]\.\./"
        ),
    ),
)

COLOR_PATTERN = re.compile(r"(#[0-9a-fA-F]{3,8}\b|\brgba?\(|\bhsla?\()")


@dataclass(frozen=True)
class Finding:
    rule: str
    path: str
    line: int
    text: str


def iter_frontend_files() -> Iterator[Path]:
    if not FRONTEND_SOURCE.is_dir():
        return
    for path in sorted(FRONTEND_SOURCE.rglob("*")):
        if not path.is_file() or path.suffix not in FRONTEND_SUFFIXES:
            continue
        if GENERATED_FRONTEND_COMPONENTS in path.parents:
            continue
        yield path


def iter_backend_files() -> Iterator[Path]:
    if not BACKEND_SOURCE.is_dir():
        return
    for path in sorted(BACKEND_SOURCE.rglob("*.py")):
        if not path.is_file():
            continue
        relative_parts = path.relative_to(ROOT).parts
        if any(part in EXCLUDED_DIRECTORY_NAMES for part in relative_parts):
            continue
        yield path


def iter_source_files() -> Iterator[Path]:
    yield from iter_frontend_files()
    yield from iter_backend_files()


def scan_file(path: Path) -> list[Finding]:
    relative = path.relative_to(ROOT).as_posix()
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise RuntimeError(f"cannot read {relative}: {exc}") from exc

    rules = PYTHON_RULES if path.suffix == ".py" else FRONTEND_RULES
    findings: list[Finding] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        for rule, pattern in rules:
            if pattern.search(line):
                findings.append(Finding(rule, relative, line_number, line))
        if (
            path.suffix in COLOR_SUFFIXES
            and relative not in COLOR_ALLOWLIST
            and COLOR_PATTERN.search(line)
        ):
            findings.append(Finding("hardcoded-color", relative, line_number, line))
    return findings


def main(argv: Sequence[str]) -> int:
    if argv:
        print("usage: scan_banned.py", file=sys.stderr)
        return 2
    if not FRONTEND_SOURCE.is_dir() or not BACKEND_SOURCE.is_dir():
        print("frontend/src or backend directory not found", file=sys.stderr)
        return 2

    findings: list[Finding] = []
    try:
        for path in iter_source_files():
            findings.extend(scan_file(path))
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    if not findings:
        return 0

    for finding in findings:
        print(
            f"{finding.rule}: {finding.path}:{finding.line}: {finding.text.strip()}",
            file=sys.stderr,
        )
    print(f"{len(findings)} banned item(s) found", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
