#!/usr/bin/env python3
"""
D1 skeleton: compare run_dir delivery-manifest against optional golden snapshot.

NOT in validate_release must_ok. If ``contracts/telegram-golden/`` is absent → exit 0 (skip).
Full enforcement deferred to v19.0.4 per plan.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GOLDEN_DIR = ROOT / "contracts" / "telegram-golden"


def _deep_diff(a: object, b: object, path: str, ignore_paths: frozenset[str]) -> list[str]:
    diffs: list[str] = []
    pfx = path or "$"

    def ign() -> bool:
        return pfx in ignore_paths or any(pfx.endswith(suffix) for suffix in ignore_paths if suffix.startswith("."))

    if ign():
        return diffs
    if type(a) != type(b) and not (isinstance(a, (int, float)) and isinstance(b, (int, float))):
        diffs.append(f"type {pfx}: {type(a).__name__} vs {type(b).__name__}")
        return diffs
    if isinstance(a, dict) and isinstance(b, dict):
        keys = set(a) | set(b)
        for k in sorted(keys):
            np = f"{pfx}.{k}"
            if k not in a or k not in b:
                diffs.append(f"missing key {np}")
                continue
            diffs.extend(_deep_diff(a[k], b[k], np, ignore_paths))
    elif isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            diffs.append(f"len {pfx}: {len(a)} vs {len(b)}")
        else:
            for i, (x, y) in enumerate(zip(a, b, strict=True)):
                diffs.extend(_deep_diff(x, y, f"{pfx}[{i}]", ignore_paths))
    else:
        if a != b:
            diffs.append(f"value {pfx}: {a!r} != {b!r}")
    return diffs


def main() -> int:
    if len(sys.argv) < 2:
        print(json.dumps({"status": "skip", "reason": "usage: _diff_telegram_against_golden.py <run_dir>"}, ensure_ascii=False))
        return 0
    rd = Path(sys.argv[1])
    if not GOLDEN_DIR.is_dir():
        print(json.dumps({"status": "skip", "reason": "contracts/telegram-golden absent (D1 skeleton)"}, ensure_ascii=False))
        return 0
    golden_manifest = GOLDEN_DIR / "delivery-manifest.json"
    allow = GOLDEN_DIR / "allowlist-paths.txt"
    if not golden_manifest.is_file():
        print(json.dumps({"status": "skip", "reason": "no delivery-manifest.json in telegram-golden"}, ensure_ascii=False))
        return 0
    dm_path = rd / "delivery-manifest.json"
    if not dm_path.is_file():
        print(json.dumps({"status": "skip", "reason": "run_dir has no delivery-manifest.json"}, ensure_ascii=False))
        return 0
    cur = json.loads(dm_path.read_text(encoding="utf-8"))
    gold = json.loads(golden_manifest.read_text(encoding="utf-8"))
    ignore: set[str] = set()
    if allow.is_file():
        for line in allow.read_text(encoding="utf-8").splitlines():
            s = line.strip()
            if s and not s.startswith("#"):
                ignore.add(s)
    diffs = _deep_diff(gold, cur, "$", frozenset(sorted(ignore)))
    if diffs:
        print(json.dumps({"status": "fail", "diffs": diffs[:80], "diff_count": len(diffs)}, ensure_ascii=False, indent=2))
        return 1
    print(json.dumps({"status": "pass", "detail": "golden match"}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
