#!/usr/bin/env python3
"""Validate snapshot immutability against stored SHA-256 ledger."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def _sha(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def _j(path: Path, default):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("run_dir", type=Path, nargs="?", default=Path("."))
    args = ap.parse_args()
    rd = args.run_dir

    snap_dir = rd / "source-snapshots"
    snaps = sorted(p for p in snap_dir.glob("**/*") if p.is_file()) if snap_dir.is_dir() else []
    if not snaps:
        print(
            json.dumps(
                {
                    "status": "pass",
                    "validator": "validate_snapshot_immutability",
                    "note": "no source snapshots",
                },
                ensure_ascii=False,
            )
        )
        return 0

    ledger_p = rd / "self-audit" / "snapshot-hashes.json"
    ledger = _j(ledger_p, {})
    entries = ledger.get("hashes", ledger if isinstance(ledger, dict) else {})
    if isinstance(entries, list):
        hash_map = {str(x.get("path")): str(x.get("sha256")) for x in entries if x.get("path")}
    elif isinstance(entries, dict):
        hash_map = {str(k): str(v) for k, v in entries.items()}
    else:
        hash_map = {}

    if not hash_map:
        print(
            json.dumps(
                {
                    "status": "fail",
                    "validator": "validate_snapshot_immutability",
                    "reason": "snapshot_hash_ledger_missing_or_empty",
                    "ledger_path": str(ledger_p),
                    "snapshot_count": len(snaps),
                },
                ensure_ascii=False,
            )
        )
        return 1

    mismatches = []
    missing = []
    for sp in snaps:
        rel = sp.relative_to(rd).as_posix()
        expected = hash_map.get(rel)
        if not expected:
            missing.append(rel)
            continue
        actual = _sha(sp)
        if actual != expected:
            mismatches.append({"path": rel, "expected": expected, "actual": actual})

    if missing or mismatches:
        print(
            json.dumps(
                {
                    "status": "fail",
                    "validator": "validate_snapshot_immutability",
                    "missing_hash_entries": missing[:100],
                    "mismatches": mismatches[:100],
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 1

    print(
        json.dumps(
            {
                "status": "pass",
                "validator": "validate_snapshot_immutability",
                "snapshot_count": len(snaps),
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
