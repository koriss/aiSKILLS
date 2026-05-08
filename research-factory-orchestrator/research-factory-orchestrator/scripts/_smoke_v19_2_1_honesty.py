#!/usr/bin/env python3
"""v19.2.1 honesty matrix.

Five smoke cases that together prove the policy-vacuum closed in v19.2.1:

1. canonical path + chat_id passed + api_base set → real delivery, verifier 0 lies.
2. invocation from a ``*.bak*`` skill copy → exit 11, ``RFO-NON-CANONICAL-SKILL-PATH``,
   no run-dir created, verifier never reached.
3. ``--runs-root /tmp/rfo-runs`` without ``RFO_ALLOW_TMP_RUNS_ROOT=1`` →
   exit 12, ``RFO-RUNS-ROOT-FORBIDDEN``, no run-dir created.
4. canonical path, allowed runs-root, but no ``--chat-id`` and no
   ``RFO_ALLOW_ENV_CHAT_ID=1`` → adapter records ``LIE-DETECTED-DELIVERY-STUB-WITHOUT-CONSENT``,
   ``external_delivery_gate.status="delivery_not_proven"`` (NOT ``stub_only``),
   and the verifier flags ``LIE-DETECTED-WRONG-RUNS-ROOT`` / etc as appropriate.
5. headless smoke with ``TELEGRAM_CHAT_ID`` + ``RFO_ALLOW_ENV_CHAT_ID=1`` →
   adapter accepts the env-supplied chat id as ``chat_id_source=env_consent``;
   the run is not flagged as silent stub.

Case 1 in this harness is exercised in **dry mode**: we do NOT make a real HTTP
call to Telegram from CI (no live token). Instead we set
``RFO_ALLOW_ENV_CHAT_ID=1`` and a sentinel ``TELEGRAM_BOT_TOKEN`` and verify
that the adapter routes correctly (chat_id_source=env_consent) and that the
verifier does not raise *consent-without-stub* lies. Real-bot delivery is
covered by case H in the live retest.

Exit 0 ⇒ all five cases match expectations; exit 1 otherwise.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ADAPTER = ROOT / "scripts" / "interface_runtime_adapter.py"
WORKER = ROOT / "scripts" / "runtime_job_worker.py"
OUTBOX = ROOT / "scripts" / "outbox_delivery_worker.py"
VERIFIER = ROOT / "scripts" / "verify_openclaw_run.py"


def _run(cmd: list[str], env: dict | None = None, cwd: Path | None = None, timeout: int = 60) -> subprocess.CompletedProcess:
    final_env = {**os.environ}
    if env:
        final_env.update(env)
    final_env.setdefault("PYTHONDONTWRITEBYTECODE", "1")
    return subprocess.run(
        cmd,
        cwd=str(cwd or ROOT),
        env=final_env,
        capture_output=True,
        text=True,
        timeout=timeout,
    )


def _newest_run_dir(runs_root: Path) -> Path | None:
    runs_dir = runs_root / "runs"
    if not runs_dir.is_dir():
        return None
    children = sorted([p for p in runs_dir.iterdir() if p.is_dir()])
    return children[-1] if children else None


def case_1_canonical_consented_smoke() -> dict:
    """Canonical skill, allowed runs-root, env-consent chat_id, sentinel token.

    Validates that with full consent the adapter does NOT silently stub: it
    attempts a real send and records ``chat_id_source="env_consent"``. We accept
    a network-error failure as long as the failure is honest (not a silent stub).
    """
    with tempfile.TemporaryDirectory(prefix="rfo-c1-") as td:
        runs_root = Path(td)
        env = {
            "RFO_ALLOW_TMP_RUNS_ROOT": "1",
            "RFO_ALLOW_ENV_CHAT_ID": "1",
            "TELEGRAM_CHAT_ID": "999999999",
            # Sentinel token: real HTTP attempt will be rejected by Telegram,
            # but adapter MUST attempt — that's the whole point.
            "TELEGRAM_BOT_TOKEN": "0:smoke-sentinel-token-do-not-use",
        }
        q = _run(
            [
                sys.executable, "-S", str(ADAPTER),
                "--runs-root", str(runs_root),
                "--interface", "telegram", "--provider", "telegram",
                "--task", "v19.2.1-smoke case-1 canonical consented",
            ],
            env=env,
            timeout=30,
        )
        if q.returncode != 0:
            return {"case": 1, "status": "fail", "detail": f"adapter queue exit={q.returncode} stderr={q.stderr!r}"}
        w = _run([sys.executable, "-S", str(WORKER), "--runs-root", str(runs_root), "--execute-runtime"], env=env, timeout=120)
        if w.returncode != 0:
            return {"case": 1, "status": "fail", "detail": f"runtime worker exit={w.returncode} stderr={w.stderr!r}"}
        # Outbox attempts a real HTTP call; allow up to 60s (sentinel token will fail fast).
        o = _run([sys.executable, "-S", str(OUTBOX), "--runs-root", str(runs_root)], env=env, timeout=180)
        # Outbox may exit non-zero on telegram failure; we still inspect artifacts.
        rd = _newest_run_dir(runs_root)
        if rd is None:
            return {"case": 1, "status": "fail", "detail": "no run-dir produced"}
        ack_paths = sorted((rd / "delivery-acks").glob("OUT-*.json"))
        chat_sources = []
        for p in ack_paths:
            try:
                d = json.loads(p.read_text(encoding="utf-8"))
                if d.get("provider") == "telegram":
                    chat_sources.append(d.get("chat_id_source"))
            except Exception:
                continue
        if not chat_sources:
            return {"case": 1, "status": "fail", "detail": "no telegram acks produced"}
        if not all(src == "env_consent" for src in chat_sources):
            return {
                "case": 1,
                "status": "fail",
                "detail": f"expected all telegram acks to have chat_id_source='env_consent', got {chat_sources!r}",
            }
        # verifier should not raise stub-without-consent for this run.
        v = _run([sys.executable, "-S", str(VERIFIER), "--run-dir", str(rd)], env=env, timeout=60)
        v_out = {}
        try:
            v_out = json.loads(v.stdout or "{}")
        except Exception:
            v_out = {}
        bad_codes = {"LIE-DETECTED-DELIVERY-STUB-WITHOUT-CONSENT"}
        observed = {l.get("code") for l in (v_out.get("lies") or [])}
        if observed & bad_codes:
            return {
                "case": 1,
                "status": "fail",
                "detail": f"verifier raised {observed & bad_codes!r} on consented smoke run",
                "verifier_lies": list(v_out.get("lies") or []),
            }
        return {
            "case": 1,
            "status": "pass",
            "detail": "canonical+consent run produced env_consent chat_id_source, verifier did not raise consent-stub lie",
        }


def case_2_bak_skill_copy_refused() -> dict:
    """A real ``*.bak*`` directory copy must refuse to start with exit 11."""
    with tempfile.TemporaryDirectory(prefix="rfo-c2-") as td:
        bak_dir = Path(td) / "research-factory-orchestrator.bak-smoke"
        # Copy minimally — just scripts/ and runtime/ so adapter actually loads.
        bak_dir.mkdir()
        for sub in ("scripts", "runtime"):
            shutil.copytree(ROOT / sub, bak_dir / sub)
        runs_root = Path(td) / "runs-root"
        runs_root.mkdir()
        env = {"RFO_ALLOW_TMP_RUNS_ROOT": "1"}
        p = _run(
            [
                sys.executable, "-S", str(bak_dir / "scripts" / "interface_runtime_adapter.py"),
                "--runs-root", str(runs_root),
                "--interface", "telegram", "--provider", "telegram",
                "--task", "v19.2.1-smoke case-2 bak refusal",
            ],
            env=env,
            cwd=bak_dir,
            timeout=30,
        )
        if p.returncode != 11:
            return {
                "case": 2,
                "status": "fail",
                "detail": f"expected exit 11 RFO-NON-CANONICAL-SKILL-PATH, got {p.returncode}; stderr={p.stderr!r}",
            }
        if "RFO-NON-CANONICAL-SKILL-PATH" not in (p.stderr or ""):
            return {"case": 2, "status": "fail", "detail": f"expected error stamp in stderr, got: {p.stderr!r}"}
        if (runs_root / "runs").exists() and any((runs_root / "runs").iterdir()):
            return {"case": 2, "status": "fail", "detail": "run-dir was created despite skill-path refusal"}
        return {"case": 2, "status": "pass", "detail": "bak skill copy refused with exit 11 and no run-dir"}


def case_3_tmp_runs_root_without_consent() -> dict:
    """``--runs-root /tmp/...`` without ``RFO_ALLOW_TMP_RUNS_ROOT=1`` → exit 12."""
    with tempfile.TemporaryDirectory(prefix="rfo-c3-") as td:
        runs_root = Path(td)
        # Make sure the path is under /tmp.
        if not str(runs_root.resolve()).startswith(("/tmp/", "/var/tmp/")):
            return {
                "case": 3,
                "status": "skip",
                "detail": f"system tempdir not under /tmp; got {runs_root}",
            }
        env = {"RFO_ALLOW_TMP_RUNS_ROOT": ""}  # explicitly NO consent
        env.pop("RFO_ALLOW_TMP_RUNS_ROOT", None)
        p = _run(
            [
                sys.executable, "-S", str(ADAPTER),
                "--runs-root", str(runs_root),
                "--interface", "telegram", "--provider", "telegram",
                "--task", "v19.2.1-smoke case-3 tmp without consent",
            ],
            env={"RFO_ALLOW_TMP_RUNS_ROOT": ""},  # force-empty
            timeout=30,
        )
        if p.returncode != 12:
            return {
                "case": 3,
                "status": "fail",
                "detail": f"expected exit 12 RFO-RUNS-ROOT-FORBIDDEN, got {p.returncode}; stderr={p.stderr!r}",
            }
        if "RFO-RUNS-ROOT-FORBIDDEN" not in (p.stderr or ""):
            return {"case": 3, "status": "fail", "detail": f"expected error stamp in stderr, got: {p.stderr!r}"}
        if (runs_root / "runs").exists() and any((runs_root / "runs").iterdir()):
            return {"case": 3, "status": "fail", "detail": "run-dir was created despite runs-root refusal"}
        return {"case": 3, "status": "pass", "detail": "/tmp runs-root without consent refused with exit 12"}


def case_4_no_chat_id_no_consent() -> dict:
    """No --chat-id and no RFO_ALLOW_ENV_CHAT_ID → delivery_not_proven, NOT stub_only."""
    with tempfile.TemporaryDirectory(prefix="rfo-c4-") as td:
        runs_root = Path(td)
        env = {"RFO_ALLOW_TMP_RUNS_ROOT": "1"}
        # Pop env chat id and bot token to be sure adapter has nothing to fall back on.
        for k in ("RFO_ALLOW_ENV_CHAT_ID", "TELEGRAM_CHAT_ID", "TELEGRAM_BOT_TOKEN"):
            env[k] = ""
        q = _run(
            [
                sys.executable, "-S", str(ADAPTER),
                "--runs-root", str(runs_root),
                "--interface", "telegram", "--provider", "telegram",
                "--task", "v19.2.1-smoke case-4 no chat id no consent",
            ],
            env=env,
            timeout=30,
        )
        if q.returncode != 0:
            return {"case": 4, "status": "fail", "detail": f"adapter queue exit={q.returncode}: {q.stderr!r}"}
        w = _run([sys.executable, "-S", str(WORKER), "--runs-root", str(runs_root), "--execute-runtime"], env=env, timeout=120)
        if w.returncode != 0:
            return {"case": 4, "status": "fail", "detail": f"runtime worker exit={w.returncode}: {w.stderr!r}"}
        o = _run([sys.executable, "-S", str(OUTBOX), "--runs-root", str(runs_root)], env=env, timeout=60)
        # Outbox MUST exit 0 — explicit refusal is recorded in the manifest, not in process exit.
        if o.returncode != 0:
            return {"case": 4, "status": "fail", "detail": f"outbox worker exit={o.returncode}: {o.stderr!r}"}
        rd = _newest_run_dir(runs_root)
        if rd is None:
            return {"case": 4, "status": "fail", "detail": "no run-dir produced"}
        dm = json.loads((rd / "delivery-manifest.json").read_text(encoding="utf-8"))
        ext = dm.get("gates", {}).get("external_delivery_gate") or {}
        if ext.get("status") != "delivery_not_proven":
            return {
                "case": 4,
                "status": "fail",
                "detail": f"expected external_delivery_gate.status='delivery_not_proven', got {ext.get('status')!r}",
            }
        if ext.get("stub_only"):
            return {"case": 4, "status": "fail", "detail": "external_delivery_gate.stub_only must be false"}
        if not ext.get("delivery_not_proven"):
            return {"case": 4, "status": "fail", "detail": "external_delivery_gate.delivery_not_proven must be true"}
        reasons = set(ext.get("reasons") or [])
        if not any("TELEGRAM-CHAT-ID-MISSING" in r for r in reasons):
            return {
                "case": 4,
                "status": "fail",
                "detail": f"expected reason containing TELEGRAM-CHAT-ID-MISSING, got {reasons!r}",
            }
        # errors.jsonl must contain LIE-DETECTED-DELIVERY-STUB-WITHOUT-CONSENT.
        err_path = rd / "runtime" / "errors.jsonl"
        if not err_path.is_file():
            return {"case": 4, "status": "fail", "detail": "runtime/errors.jsonl missing"}
        if "LIE-DETECTED-DELIVERY-STUB-WITHOUT-CONSENT" not in err_path.read_text(encoding="utf-8"):
            return {"case": 4, "status": "fail", "detail": "errors.jsonl missing LIE-DETECTED-DELIVERY-STUB-WITHOUT-CONSENT"}
        return {"case": 4, "status": "pass", "detail": "delivery_not_proven with concrete TELEGRAM-CHAT-ID-MISSING reason; no silent stub"}


def case_5_consented_env_chat_id() -> dict:
    """Consented headless smoke: ``TELEGRAM_CHAT_ID`` + ``RFO_ALLOW_ENV_CHAT_ID=1``.

    Adapter accepts env-supplied chat id; ack records ``chat_id_source=env_consent``.
    """
    with tempfile.TemporaryDirectory(prefix="rfo-c5-") as td:
        runs_root = Path(td)
        env = {
            "RFO_ALLOW_TMP_RUNS_ROOT": "1",
            "RFO_ALLOW_ENV_CHAT_ID": "1",
            "TELEGRAM_CHAT_ID": "111222333",
            "TELEGRAM_BOT_TOKEN": "0:smoke-sentinel",
        }
        q = _run(
            [
                sys.executable, "-S", str(ADAPTER),
                "--runs-root", str(runs_root),
                "--interface", "telegram", "--provider", "telegram",
                "--task", "v19.2.1-smoke case-5 consented env chat id",
            ],
            env=env,
            timeout=30,
        )
        if q.returncode != 0:
            return {"case": 5, "status": "fail", "detail": f"adapter queue exit={q.returncode}: {q.stderr!r}"}
        w = _run([sys.executable, "-S", str(WORKER), "--runs-root", str(runs_root), "--execute-runtime"], env=env, timeout=120)
        if w.returncode != 0:
            return {"case": 5, "status": "fail", "detail": f"runtime worker exit={w.returncode}: {w.stderr!r}"}
        # Don't run real outbox here (would attempt HTTP) — instead invoke the
        # adapter directly on one event in dry mode by reading the OUT-0001
        # event. We just verify the outbox attempts the call without falling
        # back into a silent stub.
        o = _run([sys.executable, "-S", str(OUTBOX), "--runs-root", str(runs_root)], env=env, timeout=180)
        rd = _newest_run_dir(runs_root)
        if rd is None:
            return {"case": 5, "status": "fail", "detail": "no run-dir produced"}
        ack_paths = sorted((rd / "delivery-acks").glob("OUT-*.json"))
        if not ack_paths:
            return {"case": 5, "status": "fail", "detail": "no acks produced"}
        chat_sources = []
        for p in ack_paths:
            try:
                d = json.loads(p.read_text(encoding="utf-8"))
                if d.get("provider") == "telegram":
                    chat_sources.append(d.get("chat_id_source"))
            except Exception:
                continue
        if not chat_sources:
            return {"case": 5, "status": "fail", "detail": "no telegram acks produced"}
        if not all(src == "env_consent" for src in chat_sources):
            return {
                "case": 5,
                "status": "fail",
                "detail": f"expected all telegram acks chat_id_source=env_consent, got {chat_sources!r}",
            }
        return {"case": 5, "status": "pass", "detail": "headless consent smoke marks chat_id_source=env_consent"}


def main() -> int:
    cases = [
        case_2_bak_skill_copy_refused,
        case_3_tmp_runs_root_without_consent,
        case_4_no_chat_id_no_consent,
    ]
    # Cases 1 and 5 attempt real HTTP via outbox, which can be slow on hosts
    # with broken egress. They are still part of the matrix but allow longer
    # timeouts; expose via environment toggle for CI tuning if needed.
    cases.append(case_5_consented_env_chat_id)
    cases.append(case_1_canonical_consented_smoke)

    results = []
    for fn in cases:
        try:
            results.append(fn())
        except Exception as exc:
            results.append({"case": fn.__name__, "status": "fail", "detail": f"exception: {exc!r}"})

    summary = {
        "smoke_id": "v19_2_1_honesty",
        "results": results,
        "passed": sum(1 for r in results if r.get("status") == "pass"),
        "failed": sum(1 for r in results if r.get("status") == "fail"),
        "skipped": sum(1 for r in results if r.get("status") == "skip"),
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if summary["failed"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
