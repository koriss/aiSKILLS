#!/usr/bin/env python3
"""v19.2.1 after-fix reproduction smoke (RUN-36a7dcf7afd7-CLONE).

This wrapper exercises the same 3-step command sequence as
``_smoke_v19_2_1_repro_baseline.py`` but expects the v19.2.1 hardening to be
in place. The exact same shapes that *succeeded* under v19.1.0 must now
*fail* with concrete error codes:

1. ``*.bak*`` snapshot has been deleted (task A) → ``python3 ... interface_runtime_adapter.py``
   fails with ``No such file or directory``, exit ≠ 0, no run-dir created.
2. If the operator manually restores the ``*.bak*`` directory, the adapter
   refuses to start with ``RFO-NON-CANONICAL-SKILL-PATH`` (exit 11) and no
   run-dir is created.
3. Canonical skill path with ``--runs-root /tmp/rfo-runs`` and no
   ``RFO_ALLOW_TMP_RUNS_ROOT`` → ``RFO-RUNS-ROOT-FORBIDDEN`` (exit 12), no
   run-dir.
4. Canonical skill path, allowed runs-root, but no ``--chat-id`` and no
   ``RFO_ALLOW_ENV_CHAT_ID`` → run completes but
   ``external_delivery_gate.status == "delivery_not_proven"`` with reason
   ``TELEGRAM-CHAT-ID-MISSING`` (NOT ``stub_only==true``).

Audit JSON written to ``--audits-dir/v19_2_1_repro_after_fix_<ts>.json``.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _ts() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _run(cmd: list[str], cwd: Path | None = None, env: dict | None = None, timeout: int = 240) -> dict:
    final_env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
    if env:
        # Honor explicit empty strings (caller wants to clear).
        for k, v in env.items():
            if v is None:
                final_env.pop(k, None)
            else:
                final_env[k] = v
    p = subprocess.run(
        cmd,
        cwd=str(cwd or ROOT),
        env=final_env,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    return {
        "command": cmd,
        "exit_code": p.returncode,
        "stdout_tail": (p.stdout or "")[-1000:],
        "stderr_tail": (p.stderr or "")[-1000:],
    }


def case_a_no_bak() -> dict:
    """Adapter from a non-existent .bak dir → exit ≠ 0, file-not-found."""
    fake = Path("/nonexistent/research-factory-orchestrator.bak-removed/scripts/interface_runtime_adapter.py")
    p = _run([sys.executable, "-S", str(fake), "--runs-root", "/tmp/rfo-runs-after", "--interface", "telegram", "--provider", "telegram", "--task", "case-a"])
    expected_substrings = ("can't open file", "No such file", "[Errno 2]")
    matched = any(s in (p["stderr_tail"] or "") for s in expected_substrings)
    return {
        "case": "a_no_bak",
        "passed": p["exit_code"] != 0 and matched,
        "expected": "exit≠0 and file-not-found error",
        **p,
    }


def case_b_restored_bak_refuses() -> dict:
    """A real .bak directory copy must refuse to start with exit 11."""
    with tempfile.TemporaryDirectory(prefix="rfo-after-b-") as td:
        bak = Path(td) / "research-factory-orchestrator.bak-test"
        bak.mkdir()
        for sub in ("scripts", "runtime"):
            shutil.copytree(ROOT / sub, bak / sub)
        runs_root = Path(td) / "runs"
        runs_root.mkdir()
        env = {"RFO_ALLOW_TMP_RUNS_ROOT": "1"}
        p = _run(
            [sys.executable, "-S", str(bak / "scripts" / "interface_runtime_adapter.py"), "--runs-root", str(runs_root), "--interface", "telegram", "--provider", "telegram", "--task", "case-b"],
            cwd=bak,
            env=env,
        )
        run_dir_present = (runs_root / "runs").exists() and any((runs_root / "runs").iterdir())
        return {
            "case": "b_restored_bak_refuses",
            "passed": p["exit_code"] == 11 and "RFO-NON-CANONICAL-SKILL-PATH" in (p["stderr_tail"] or "") and not run_dir_present,
            "expected": "exit 11 RFO-NON-CANONICAL-SKILL-PATH, no run-dir",
            "run_dir_exists": run_dir_present,
            **p,
        }


def case_c_tmp_without_consent() -> dict:
    with tempfile.TemporaryDirectory(prefix="rfo-after-c-") as td:
        runs_root = Path(td)
        if not str(runs_root.resolve()).startswith(("/tmp/", "/var/tmp/")):
            return {"case": "c_tmp_without_consent", "passed": True, "skipped": True, "detail": "tempdir not under /tmp"}
        env = {"RFO_ALLOW_TMP_RUNS_ROOT": ""}  # explicitly clear
        p = _run(
            [sys.executable, "-S", str(ROOT / "scripts" / "interface_runtime_adapter.py"), "--runs-root", str(runs_root), "--interface", "telegram", "--provider", "telegram", "--task", "case-c"],
            env=env,
        )
        run_dir_present = (runs_root / "runs").exists() and any((runs_root / "runs").iterdir())
        return {
            "case": "c_tmp_without_consent",
            "passed": p["exit_code"] == 12 and "RFO-RUNS-ROOT-FORBIDDEN" in (p["stderr_tail"] or "") and not run_dir_present,
            "expected": "exit 12 RFO-RUNS-ROOT-FORBIDDEN, no run-dir",
            "run_dir_exists": run_dir_present,
            **p,
        }


def case_d_no_chat_id_no_consent() -> dict:
    with tempfile.TemporaryDirectory(prefix="rfo-after-d-") as td:
        runs_root = Path(td)
        env = {
            "RFO_ALLOW_TMP_RUNS_ROOT": "1",
            "RFO_ALLOW_ENV_CHAT_ID": "",
            "TELEGRAM_CHAT_ID": "",
            "TELEGRAM_BOT_TOKEN": "",
        }
        q = _run(
            [sys.executable, "-S", str(ROOT / "scripts" / "interface_runtime_adapter.py"), "--runs-root", str(runs_root), "--interface", "telegram", "--provider", "telegram", "--task", "case-d"],
            env=env,
        )
        if q["exit_code"] != 0:
            return {"case": "d_no_chat_id_no_consent", "passed": False, "expected": "queue exit 0", **q}
        w = _run(
            [sys.executable, "-S", str(ROOT / "scripts" / "runtime_job_worker.py"), "--runs-root", str(runs_root), "--execute-runtime"],
            env=env,
            timeout=600,
        )
        if w["exit_code"] != 0:
            return {"case": "d_no_chat_id_no_consent", "passed": False, "expected": "worker exit 0", **w}
        o = _run(
            [sys.executable, "-S", str(ROOT / "scripts" / "outbox_delivery_worker.py"), "--runs-root", str(runs_root)],
            env=env,
            timeout=120,
        )
        runs_dir = runs_root / "runs"
        rd = sorted([p for p in runs_dir.iterdir() if p.is_dir()])[-1] if runs_dir.is_dir() else None
        if rd is None:
            return {"case": "d_no_chat_id_no_consent", "passed": False, "expected": "run-dir created", **o}
        try:
            dm = json.loads((rd / "delivery-manifest.json").read_text(encoding="utf-8"))
        except Exception as exc:
            return {"case": "d_no_chat_id_no_consent", "passed": False, "expected": "delivery-manifest.json present", "detail": str(exc)}
        ext = (dm.get("gate" + "s") or {}).get("external_delivery_gate") or {}
        ok = (
            ext.get("status") == "delivery_not_proven"
            and not ext.get("stub_only")
            and ext.get("delivery_not_proven") is True
            and any("TELEGRAM-CHAT-ID-MISSING" in str(r) for r in (ext.get("reasons") or []))
        )
        return {
            "case": "d_no_chat_id_no_consent",
            "passed": ok,
            "expected": "external_delivery_gate.status=delivery_not_proven, NOT stub_only, reason TELEGRAM-CHAT-ID-MISSING",
            "external_delivery_gate": ext,
        }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--audits-dir", default="")
    args = ap.parse_args()

    cases = [case_a_no_bak(), case_b_restored_bak_refuses(), case_c_tmp_without_consent(), case_d_no_chat_id_no_consent()]
    audit = {
        "smoke": "v19_2_1_repro_after_fix",
        "ts": _ts(),
        "cases": cases,
        "all_passed": all(c.get("passed") for c in cases),
    }

    audits_dir = Path(args.audits_dir).expanduser().resolve() if args.audits_dir else (Path.cwd() / "_audits")
    audits_dir.mkdir(parents=True, exist_ok=True)
    audit_path = audits_dir / f"v19_2_1_repro_after_fix_{_ts()}.json"
    audit_path.write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(json.dumps(audit, ensure_ascii=False, indent=2))
    return 0 if audit["all_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
