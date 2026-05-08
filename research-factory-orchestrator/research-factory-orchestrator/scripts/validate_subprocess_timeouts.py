#!/usr/bin/env python3
"""Guard: every subprocess.run / subprocess.Popen.communicate / check_output
call in runtime/ and scripts/ must declare an explicit ``timeout=`` keyword.

Closes failure code SUBPROCESS-NO-TIMEOUT (Phase 4C P1, static-audit). A
missing timeout is a latent hang vector under flaky network/CI; runtime gates
must never block the operator surface indefinitely.

stdlib-only, fail-closed, JSON envelope on stdout. AST-based so multi-line
calls are caught.
"""
from __future__ import annotations

import ast
import json
import sys
from pathlib import Path

VALIDATOR_ID = "validate_subprocess_timeouts"
SCAN_DIRS = ("runtime", "scripts")
# Files that legitimately stream subprocess output without a hard timeout.
ALLOWLIST: set[str] = {
    # Add once, with rationale, and keep small.
}
TARGET_FUNCS = {"run", "check_output", "check_call", "call"}
COMMUNICATE_FUNC = "communicate"


class _Visitor(ast.NodeVisitor):
    def __init__(self) -> None:
        self.violations: list[tuple[int, str]] = []

    def visit_Call(self, node: ast.Call) -> None:
        func = node.func
        attr = getattr(func, "attr", None)
        if attr in TARGET_FUNCS or attr == COMMUNICATE_FUNC:
            owner = getattr(func, "value", None)
            owner_name = getattr(owner, "id", None) if isinstance(owner, ast.Name) else None
            owner_attr = getattr(owner, "attr", None) if isinstance(owner, ast.Attribute) else None
            looks_like_subprocess = owner_name == "subprocess" or owner_attr in {"Popen", "subprocess"}
            looks_like_communicate = attr == COMMUNICATE_FUNC
            if looks_like_subprocess or looks_like_communicate:
                kw_names = {kw.arg for kw in node.keywords if kw.arg}
                if "timeout" not in kw_names:
                    self.violations.append((node.lineno, attr or "<call>"))
        self.generic_visit(node)


def _emit(passed: bool, blocking: bool, issues: list, warnings: list, summary: str) -> int:
    print(
        json.dumps(
            {
                "validator_id": VALIDATOR_ID,
                "schema_version": "v19.0",
                "passed": passed,
                "blocking": blocking,
                "issues": issues,
                "warnings": warnings,
                "summary": summary,
            },
            ensure_ascii=False,
        )
    )
    return 0 if not blocking else 1


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    issues: list[dict] = []
    warnings: list[dict] = []
    scanned = 0
    for sub in SCAN_DIRS:
        for py in (root / sub).rglob("*.py"):
            rel = str(py.relative_to(root))
            if rel in ALLOWLIST:
                continue
            try:
                tree = ast.parse(py.read_text(encoding="utf-8"))
            except SyntaxError as e:
                issues.append({"code": "SUBPROCESS-PARSE-ERROR", "severity": "error", "file": rel, "detail": str(e)})
                continue
            v = _Visitor()
            v.visit(tree)
            for line, name in v.violations:
                issues.append({"code": "SUBPROCESS-NO-TIMEOUT", "severity": "error", "file": rel, "line": line, "call": name, "detail": "missing explicit timeout=<seconds>"})
            scanned += 1
    blocking = any(i.get("severity") == "error" for i in issues)
    return _emit(not blocking, blocking, issues, warnings, f"scanned {scanned} files")


if __name__ == "__main__":
    raise SystemExit(main())
