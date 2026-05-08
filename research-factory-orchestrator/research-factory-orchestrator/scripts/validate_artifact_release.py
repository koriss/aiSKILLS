#!/usr/bin/env python3
"""Validate v19.3 artifact contract: result-manifest.json, relative paths, sha256."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    h.update(p.read_bytes())
    return h.hexdigest()


def _rel_safe(p: str) -> bool:
    if not p or p.startswith("/") or ".." in p.split("/"):
        return False
    return bool(re.match(r"^(?:[A-Za-z0-9_.-]+/)*[A-Za-z0-9_.-]+$", p))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", required=True, type=Path)
    args = ap.parse_args()
    rd: Path = args.run_dir.resolve()
    if not rd.is_dir():
        print(json.dumps({"ok": False, "error": "run_dir_missing"}, ensure_ascii=False))
        return 1
    mp = rd / "result-manifest.json"
    if not mp.is_file():
        print(json.dumps({"ok": False, "error": "missing_result_manifest"}, ensure_ascii=False))
        return 1
    try:
        man = json.loads(mp.read_text(encoding="utf-8"))
    except Exception as e:
        print(json.dumps({"ok": False, "error": f"bad_json:{e}"}, ensure_ascii=False))
        return 1
    if man.get("contract") != "rfo-artifact-result-v1":
        print(json.dumps({"ok": False, "error": "bad_contract"}, ensure_ascii=False))
        return 1
    st = man.get("status")
    if st not in ("ok", "partial", "failed"):
        print(json.dumps({"ok": False, "error": "bad_status"}, ensure_ascii=False))
        return 1
    arts = man.get("artifacts")
    if not isinstance(arts, list) or not arts:
        print(json.dumps({"ok": False, "error": "artifacts_empty"}, ensure_ascii=False))
        return 1
    for a in arts:
        rel = a.get("path")
        if not isinstance(rel, str) or not _rel_safe(rel):
            print(json.dumps({"ok": False, "error": f"bad_path:{rel!r}"}, ensure_ascii=False))
            return 1
        fp = rd / rel
        if not fp.is_file():
            print(json.dumps({"ok": False, "error": f"missing_file:{rel}"}, ensure_ascii=False))
            return 1
        want = a.get("sha256")
        if not isinstance(want, str) or len(want) != 64:
            print(json.dumps({"ok": False, "error": "bad_sha_field"}, ensure_ascii=False))
            return 1
        got = _sha256_file(fp)
        if got.lower() != want.lower():
            print(json.dumps({"ok": False, "error": f"sha256_mismatch:{rel}", "want": want, "got": got}, ensure_ascii=False))
            return 1
    print(json.dumps({"ok": True, "run_dir": str(rd), "status": st, "artifact_count": len(arts)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
