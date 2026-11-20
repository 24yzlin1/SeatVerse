#!/usr/bin/env python3
"""Detect synchronous database calls inside async route handlers.

Only async route handlers are inspected: startup lifetime hooks are not request
handlers and are intentionally out of scope. Repository functions are
synchronous by design, so calling any of them from an async handler is flagged.

Exit codes: 0 clean, 1 violations found, 2 internal error.
"""

from __future__ import annotations

import ast
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, Sequence

ROOT = Path(__file__).resolve().parents[1]
BACKEND_SOURCE = ROOT / "backend"
REPOSITORIES = BACKEND_SOURCE / "app" / "repos"

EXCLUDED_DIRECTORY_NAMES = {
    ".venv",
    "__pycache__",
    ".mypy_cache",
    ".pytest_cache",
    ".db",
}

HTTP_METHODS = {
    "get",
    "post",
    "put",
    "patch",
    "delete",
    "head",
    "options",
    "api_route",
}

DATABASE_METHODS = {
    "execute",
    "executemany",
    "executescript",
    "fetchone",
    "fetchall",
    "commit",
    "rollback",
    "cursor",
}


@dataclass(frozen=True)
class Finding:
    path: str
    line: int
    endpoint: str
    callee: str


def iter_backend_files(root: Path) -> Iterator[Path]:
    if not root.is_dir():
        return
    for path in sorted(root.rglob("*.py")):
        if not path.is_file():
            continue
        relative_parts = path.relative_to(ROOT).parts
        if any(part in EXCLUDED_DIRECTORY_NAMES for part in relative_parts):
            continue
        yield path


def parse_module(path: Path) -> ast.Module:
    relative = path.relative_to(ROOT).as_posix()
    try:
        source = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise RuntimeError(f"cannot read {relative}: {exc}") from exc
    try:
        return ast.parse(source, filename=relative)
    except SyntaxError as exc:
        raise RuntimeError(f"cannot parse {relative}: {exc}") from exc


def collect_repository_functions() -> set[str]:
    names: set[str] = set()
    for path in iter_backend_files(REPOSITORIES):
        tree = parse_module(path)
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                names.add(node.name)
    return names


def is_route_handler(node: ast.AsyncFunctionDef) -> bool:
    for decorator in node.decorator_list:
        target = decorator.func if isinstance(decorator, ast.Call) else decorator
        if isinstance(target, ast.Attribute) and target.attr in HTTP_METHODS:
            return True
    return False


def database_call(call: ast.Call, repository_functions: set[str]) -> str | None:
    func = call.func
    if isinstance(func, ast.Name) and func.id in repository_functions:
        return func.id
    if isinstance(func, ast.Attribute):
        if func.attr in DATABASE_METHODS:
            return f".{func.attr}"
        if (
            func.attr == "connect"
            and isinstance(func.value, ast.Name)
            and func.value.id == "sqlite3"
        ):
            return "sqlite3.connect"
    return None


def scan_file(path: Path, repository_functions: set[str]) -> list[Finding]:
    tree = parse_module(path)
    relative = path.relative_to(ROOT).as_posix()
    findings: list[Finding] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.AsyncFunctionDef) or not is_route_handler(node):
            continue
        for call in ast.walk(node):
            if not isinstance(call, ast.Call):
                continue
            callee = database_call(call, repository_functions)
            if callee is not None:
                findings.append(Finding(relative, call.lineno, node.name, callee))
    return findings


def main(argv: Sequence[str]) -> int:
    if argv:
        print("usage: scan_sync_endpoints.py", file=sys.stderr)
        return 2
    if not BACKEND_SOURCE.is_dir():
        print("backend directory not found", file=sys.stderr)
        return 2

    try:
        repository_functions = collect_repository_functions()
        findings: list[Finding] = []
        for path in iter_backend_files(BACKEND_SOURCE):
            findings.extend(scan_file(path, repository_functions))
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    if not findings:
        return 0

    for finding in findings:
        print(
            f"{finding.path}:{finding.line}: async endpoint {finding.endpoint} "
            f"calls sync database call {finding.callee}",
            file=sys.stderr,
        )
    print(
        f"{len(findings)} synchronous database call(s) found in async endpoints",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
