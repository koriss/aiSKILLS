#!/usr/bin/env python3
"""Debug pipeline helper for RFO runtime."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
LATEST_TS_FILE = ROOT / "reports" / "debug-runs" / ".latest_ts"


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _load_ts() -> str:
    if LATEST_TS_FILE.exists():
        ts = LATEST_TS_FILE.read_text(encoding="utf-8").strip()
        if ts:
            return ts
    ts = _utc_now()
    (ROOT / "reports" / "debug-runs").mkdir(parents=True, exist_ok=True)
    LATEST_TS_FILE.write_text(ts + "\n", encoding="utf-8")
    return ts


def _build_env(ts: str, profile: str, seed_urls: str, source_packet: str) -> dict[str, str]:
    env = os.environ.copy()
    env["RFO_ALLOW_TMP_RUNS_ROOT"] = "1"
    if profile:
        env["RFO_RUN_PROFILE"] = profile
    if seed_urls:
        env["RFO_SEED_URLS"] = seed_urls
    if source_packet:
        env["RFO_SOURCE_PACKET"] = source_packet
    env["RFO_DEBUG_TS"] = ts
    return env


def _log_path(ts: str, command: str) -> Path:
    base = ROOT / "reports" / "debug-runs" / ts / "phase0-pipeline"
    base.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%H%M%S-%f")
    return base / f"{command}-{stamp}.json"


def _run_command(cmd: list[str], env: dict[str, str], timeout: int) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=str(ROOT),
        env=env,
        capture_output=True,
        text=True,
        timeout=timeout,
    )


def _extract_json_object(stdout: str) -> dict[str, Any]:
    for line in reversed(stdout.splitlines()):
        line = line.strip()
        if line.startswith("{") and line.endswith("}"):
            try:
                obj = json.loads(line)
                if isinstance(obj, dict):
                    return obj
            except json.JSONDecodeError:
                continue
    return {}


def _write_result(
    out_file: Path,
    *,
    command_name: str,
    args: list[str],
    env: dict[str, str],
    result: subprocess.CompletedProcess[str],
    run_dir: str,
) -> None:
    payload = {
        "command": command_name,
        "args": args,
        "env": {
            "RFO_ALLOW_TMP_RUNS_ROOT": env.get("RFO_ALLOW_TMP_RUNS_ROOT", ""),
            "RFO_RUN_PROFILE": env.get("RFO_RUN_PROFILE", ""),
            "RFO_SEED_URLS": env.get("RFO_SEED_URLS", ""),
            "RFO_SOURCE_PACKET": env.get("RFO_SOURCE_PACKET", ""),
            "RFO_DEBUG_TS": env.get("RFO_DEBUG_TS", ""),
        },
        "exit_code": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "run_dir": run_dir,
        "created_at": _utc_now(),
    }
    out_file.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _execute_runtime(
    *,
    command_name: str,
    task: str,
    mode: str,
    profile: str,
    seed_urls: str,
    source_packet: str,
    timeout: int,
) -> int:
    ts = _load_ts()
    runs_root = ROOT / "reports" / "debug-runs" / ts / "runs"
    runs_root.mkdir(parents=True, exist_ok=True)
    run_id = f"dbg-{command_name}-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}"
    run_dir = runs_root / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    env = _build_env(ts, profile, seed_urls, source_packet)
    cmd = [
        sys.executable,
        "-S",
        "-m",
        "runtime.cli",
        "run",
        "--project-dir",
        str(run_dir),
        "--task",
        task,
        "--mode",
        mode,
        "--provider",
        "cli",
        "--interface",
        "direct_runtime",
        "--runs-root",
        str(runs_root),
    ]
    result = _run_command(cmd, env, timeout)
    out = _log_path(ts, command_name)
    _write_result(out, command_name=command_name, args=cmd, env=env, result=result, run_dir=str(run_dir))
    print(str(out))
    return result.returncode


def _execute_smoke(*, timeout: int) -> int:
    ts = _load_ts()
    runs_root = ROOT / "reports" / "debug-runs" / ts / "runs"
    runs_root.mkdir(parents=True, exist_ok=True)
    env = _build_env(ts, profile="", seed_urls="", source_packet="")
    cmd = [
        sys.executable,
        "-S",
        "scripts/smoke_test_interface_runtime.py",
    ]
    result = _run_command(cmd, env, timeout)
    run_dir = ""
    parsed = _extract_json_object(result.stdout)
    if parsed.get("run_dir"):
        run_dir = str(parsed.get("run_dir"))
    out = _log_path(ts, "smoke")
    _write_result(out, command_name="smoke", args=cmd, env=env, result=result, run_dir=run_dir)
    print(str(out))
    return result.returncode


def _parse() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="RFO debug pipeline runner")
    sub = p.add_subparsers(dest="command", required=True)

    sub.add_parser("smoke")
    for name in ("collect", "search", "full", "diag"):
        sp = sub.add_parser(name)
        sp.add_argument("--task", default=f"debug {name} run")
        sp.add_argument("--profile", default="")
        sp.add_argument("--seed-urls", default="")
        sp.add_argument("--source-packet", default="")
        sp.add_argument("--mode", default="research")
        sp.add_argument("--timeout", type=int, default=240)
    p.add_argument("--timeout", type=int, default=240)
    return p.parse_args()


def main() -> int:
    a = _parse()
    if a.command == "smoke":
        return _execute_smoke(timeout=a.timeout)

    return _execute_runtime(
        command_name=a.command,
        task=a.task,
        mode=a.mode,
        profile=a.profile,
        seed_urls=a.seed_urls,
        source_packet=a.source_packet,
        timeout=a.timeout,
    )


if __name__ == "__main__":
    raise SystemExit(main())
