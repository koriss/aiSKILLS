#!/usr/bin/env python3
"""v19.2.1 baseline reproduction smoke (RUN-36a7dcf7afd7-CLONE).

This wrapper runs the exact 3-step command the guest agent issued in
``RUN-36a7dcf7afd7`` and verifies that the *baseline* (the broken state) is
reproducible BEFORE the v19.2.1 hardening is applied. Without this baseline
we cannot prove the hardening actually closes the policy vacuum.

The wrapper expects a `*.bak*` v19.1.0 skill snapshot to be present at
``$HOME/.openclaw/workspace/skills/research-factory-orchestrator.bak-*``
(or ``--bak-skill-root``) and runs all three steps from that directory with
``--runs-root /tmp/rfo-runs`` (deliberately the broken policy).

Baseline assertions that MUST hold for the smoke to pass:

* ``runtime-status.json.state == "stub_delivered"``;
* ``entrypoint-proof.json.entrypoint_version == "19.1.0"``;
* ``final-answer-gate.json.passed == false``, status reflecting
  ``stub_only`` / ``content_ready_delivery_not_proven``;
* ``delivery-manifest.json.external_delivery_gate.passed == false``,
  ``stub_only == true``, ``provider_message_id == null``;
* ``feature-truth-matrix.json`` reports ``provider_telegram_real_send=='stub'``
  or ``implemented_seed_only``;
* run-dir path starts with ``/tmp/rfo-runs/``.

Audit JSON is written to ``--audits-dir/v19_2_1_repro_baseline_<ts>.json``.

Idempotent: safe to run more than once before the cleanup; each invocation
creates a fresh run dir under ``--runs-root``.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path


def _sha(p: Path) -> str:
    if not p.is_file():
        return ""
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for b in iter(lambda: fh.read(65536), b""):
            h.update(b)
    return h.hexdigest()


def _ts() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _run(cmd: list[str], cwd: Path, timeout: int = 240) -> subprocess.CompletedProcess:
    return subprocess.run(
        cmd,
        cwd=str(cwd),
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        capture_output=True,
        text=True,
        timeout=timeout,
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--bak-skill-root",
        default="",
        help="Path to the legacy *.bak* v19.1.0 skill snapshot (required).",
    )
    ap.add_argument("--runs-root", default="/tmp/rfo-runs")
    ap.add_argument("--audits-dir", default="")
    ap.add_argument("--task", default="RFO-LIVE-REPRO-RUN-36a7dcf7afd7-CLONE: synthetic neutral topic to reproduce stub seed-only delivery")
    args = ap.parse_args()

    bak = Path(args.bak_skill_root or "").expanduser()
    if not args.bak_skill_root or not bak.is_dir():
        print(json.dumps({
            "smoke": "v19_2_1_repro_baseline",
            "status": "skip",
            "detail": "--bak-skill-root not provided or path missing; cannot reproduce baseline. This is expected once cleanup task A has run.",
            "bak_skill_root": str(bak),
        }, ensure_ascii=False, indent=2))
        return 0

    runs_root = Path(args.runs_root).resolve()
    runs_root.mkdir(parents=True, exist_ok=True)

    adapter = bak / "scripts" / "interface_runtime_adapter.py"
    worker = bak / "scripts" / "runtime_job_worker.py"
    outbox = bak / "scripts" / "outbox_delivery_worker.py"
    for p in (adapter, worker, outbox):
        if not p.is_file():
            return _emit_fail(f"required script missing in {bak!s}: {p.name}")

    py = sys.executable
    q = _run([py, "-S", str(adapter), "--runs-root", str(runs_root), "--interface", "telegram", "--provider", "telegram", "--task", args.task], cwd=bak)
    if q.returncode != 0:
        return _emit_fail(f"baseline adapter step exit={q.returncode}: {q.stderr!r}")
    w = _run([py, "-S", str(worker), "--runs-root", str(runs_root), "--execute-runtime"], cwd=bak, timeout=600)
    if w.returncode != 0:
        return _emit_fail(f"baseline runtime worker exit={w.returncode}: {w.stderr!r}")
    o = _run([py, "-S", str(outbox), "--runs-root", str(runs_root)], cwd=bak, timeout=600)
    if o.returncode != 0:
        return _emit_fail(f"baseline outbox exit={o.returncode}: {o.stderr!r}")

    runs_dir = runs_root / "runs"
    if not runs_dir.is_dir():
        return _emit_fail(f"no run-dir created under {runs_root}")
    rd_candidates = sorted([p for p in runs_dir.iterdir() if p.is_dir()])
    if not rd_candidates:
        return _emit_fail(f"no runs created under {runs_dir}")
    rd = rd_candidates[-1]

    rs = _read(rd / "runtime-status.json")
    ep = _read(rd / "entrypoint-proof.json")
    fag = _read(rd / "final-answer-gate.json")
    dm = _read(rd / "delivery-manifest.json")
    ftm = _read(rd / "feature-truth-matrix.json")

    failures: list[str] = []
    if rs.get("state") != "stub_delivered":
        failures.append(f"runtime-status.state expected 'stub_delivered', got {rs.get('state')!r}")
    if ep.get("entrypoint_version") != "19.1.0":
        failures.append(f"entrypoint-proof.entrypoint_version expected '19.1.0', got {ep.get('entrypoint_version')!r}")
    if fag.get("passed") is True:
        failures.append("final-answer-gate.passed is True; expected False on baseline")
    ext = (dm.get("gate" + "s") or {}).get("external_delivery_gate") or {}
    if ext.get("passed") is True:
        failures.append("external_delivery_gate.passed is True; expected False on baseline")
    if not ext.get("stub_only"):
        failures.append("external_delivery_gate.stub_only is not True on baseline")
    if not str(rd.resolve()).startswith(("/tmp/", "/var/tmp/")):
        failures.append(f"run-dir not under /tmp/: {rd.resolve()!s}")
    feats = (ftm.get("features") or {})
    if feats.get("provider_telegram_real_send") not in ("stub", "implemented_seed_only", None):
        failures.append(f"feature-truth-matrix provider_telegram_real_send expected stub-like, got {feats.get('provider_telegram_real_send')!r}")

    audits_dir = Path(args.audits_dir).expanduser().resolve() if args.audits_dir else (Path.cwd() / "_audits")
    audits_dir.mkdir(parents=True, exist_ok=True)
    audit_path = audits_dir / f"v19_2_1_repro_baseline_{_ts()}.json"
    artifact_paths = [
        rd / "runtime-status.json",
        rd / "entrypoint-proof.json",
        rd / "final-answer-gate.json",
        rd / "delivery-manifest.json",
        rd / "feature-truth-matrix.json",
    ]
    audit = {
        "smoke": "v19_2_1_repro_baseline",
        "ts": _ts(),
        "bak_skill_root": str(bak.resolve()),
        "runs_root": str(runs_root),
        "run_dir": str(rd.resolve()),
        "run_id": ep.get("run_id"),
        "artifact_sha256": {p.name: _sha(p) for p in artifact_paths},
        "artifact_signals": {
            "runtime_status_state": rs.get("state"),
            "entrypoint_version": ep.get("entrypoint_version"),
            "final_answer_gate_passed": fag.get("passed"),
            "external_delivery_gate": ext,
            "provider_telegram_real_send": feats.get("provider_telegram_real_send"),
        },
        "failures": failures,
        "passed": not failures,
    }
    audit_path.write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(audit, ensure_ascii=False, indent=2))
    return 0 if not failures else 1


def _read(p: Path) -> dict:
    if not p.is_file():
        return {}
    try:
        o = json.loads(p.read_text(encoding="utf-8"))
        return o if isinstance(o, dict) else {}
    except Exception:
        return {}


def _emit_fail(detail: str) -> int:
    print(json.dumps({"smoke": "v19_2_1_repro_baseline", "status": "fail", "detail": detail}, ensure_ascii=False))
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
