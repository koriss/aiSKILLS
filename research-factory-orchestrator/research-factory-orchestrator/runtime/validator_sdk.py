"""Validator SDK: Result/findings pattern + helpers used by validate_*.py scripts."""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path


class Result:
    def __init__(self, validator_id: str) -> None:
        self.validator_id = validator_id
        self.findings: list[dict] = []
        self.start = time.time()

    def add(self, rule_id: str, severity: str, message: str, evidence=None) -> None:
        self.findings.append(
            {"rule_id": rule_id, "severity": severity, "message": message, "evidence": evidence or []}
        )

    def as_dict(self) -> dict:
        bad = any(f["severity"] in ("critical", "high") for f in self.findings)
        return {
            "validator_id": self.validator_id,
            "status": "fail" if bad else "pass",
            "findings": self.findings,
            "duration_ms": int((time.time() - self.start) * 1000),
        }


def load_json(path: Path, default=None):
    p = Path(path)
    if not p.exists():
        return default
    return json.loads(p.read_text(encoding="utf-8"))


def read_json(path: Path) -> dict:
    """Alias compatible with scripts/_validator_sdk.read_json."""
    return load_json(Path(path), {}) or {}


def fail(msg: str, code: int = 1) -> None:
    print(json.dumps({"status": "fail", "message": msg}, ensure_ascii=False), file=sys.stderr)
    raise SystemExit(code)


def ok(extra: dict | None = None) -> None:
    out = {"status": "pass"}
    if extra:
        out.update(extra)
    print(json.dumps(out, ensure_ascii=False))
    raise SystemExit(0)
