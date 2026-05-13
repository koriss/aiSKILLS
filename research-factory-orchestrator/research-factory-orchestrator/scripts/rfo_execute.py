#!/usr/bin/env python3
"""
Canonical RFO execute: **source-packet** input only (no JSON relay prefetch).

``scripts/run_rfo_with_web_search.py`` remains the **relay + prefetch** bridge
(preflight, ``--task``, ``--web-search-json-api-base``, …).

Legacy relay flags on this entrypoint → ``RFO_CONTRACT_CHANGED_SOURCE_PACKET_REQUIRED`` (exit **2**).
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

# Legacy relay / bridge flags — must not reach argparse here (use ``run_rfo_with_web_search.py``).
_LEGACY_ARG_PREFIXES = (
    "--task=",
    "--web-search-json-api-base=",
    "--web-search-secondary-json-api-base=",
    "--profile=",
    "--workspace-root=",
    "--num-sources=",
)
_LEGACY_EXACT = frozenset(
    {
        "--task",
        "--web-search-json-api-base",
        "--web-search-secondary-json-api-base",
        "--preflight",
        "--profile",
        "--workspace-root",
        "--num-sources",
    }
)

_CONTRACT_MSG = "RFO_CONTRACT_CHANGED_SOURCE_PACKET_REQUIRED"
_MISSING_MSG = "RFO_INPUT_SOURCE_PACKET_MISSING"
_STALE_MSG = "RFO_INPUT_SOURCE_PACKET_STALE"


def _legacy_flag_in_argv(argv: list[str]) -> bool:
    for a in argv[1:]:
        if a in ("-h", "--help"):
            continue
        if a in _LEGACY_EXACT:
            return True
        low = a.lower()
        for p in _LEGACY_ARG_PREFIXES:
            if low.startswith(p):
                return True
    return False


def _default_packet_path(skill_root: Path) -> Path:
    return skill_root / ".rfo-state" / "input" / "source-packet.json"


def _load_packet(path: Path) -> dict:
    raw = path.read_text(encoding="utf-8")
    return json.loads(raw)


def main() -> int:
    os.environ["RFO_EFFECTIVE_ENTRYPOINT"] = "scripts/rfo_execute.py"

    argv = list(sys.argv)
    if _legacy_flag_in_argv(argv):
        print(
            f"{_CONTRACT_MSG}: use `python3 -S scripts/run_rfo_with_web_search.py` for relay/preflight "
            f"(`--task`, `--web-search-json-api-base`, `--preflight`, …). "
            f"This entrypoint only accepts `--runs-root`, optional `--source-packet`, "
            f"optional `--allow-stale-packet`.",
            file=sys.stderr,
        )
        return 2

    here = Path(__file__).resolve().parent
    skill_root = here.parent
    sys.path.insert(0, str(skill_root))
    sys.path.insert(0, str(here))

    from _rfo_path_guard import enforce_runs_root_argv

    enforce_runs_root_argv(argv)

    from runtime.canonical_env_guard import forbidden_semantic_rfo_env

    bad_env = forbidden_semantic_rfo_env(os.environ)
    if bad_env:
        for k in bad_env:
            print(f"[rfo-config-error] forbidden_env={k}", file=sys.stderr)
        return 2

    parser = argparse.ArgumentParser(
        description="RFO canonical execute — agent-assembled source-packet (no relay prefetch on this binary).",
    )
    parser.add_argument(
        "--runs-root",
        required=True,
        help="Runs root (required). Same path contract as the relay bridge.",
    )
    parser.add_argument(
        "--source-packet",
        default=None,
        help=(
            "Path to source-packet JSON (default: <skill_root>/.rfo-state/input/source-packet.json). "
            "Host/concurrent transport should pass a unique path per request."
        ),
    )
    parser.add_argument(
        "--allow-stale-packet",
        action="store_true",
        help="Allow packet older than RFO_STALE_PACKET_MAX_HOURS (default 72). Intended for tests.",
    )
    args = parser.parse_args()

    runs_root = Path(args.runs_root).expanduser().resolve(strict=False)
    pkt_path = (
        Path(args.source_packet).expanduser().resolve(strict=False)
        if args.source_packet
        else _default_packet_path(skill_root)
    )

    if not pkt_path.is_file():
        print(
            f"{_MISSING_MSG}: no source packet at {pkt_path} "
            f"(write agent-assembled JSON or pass --source-packet).",
            file=sys.stderr,
        )
        return 2

    try:
        packet = _load_packet(pkt_path)
    except Exception as e:
        print(f"[fatal] invalid source packet JSON: {e}", file=sys.stderr)
        return 2

    if not isinstance(packet, dict):
        print("[fatal] source packet must be a JSON object", file=sys.stderr)
        return 2

    if packet.get("blocked") is True:
        print("[fatal] source packet is blocked=true; execute refuses before run allocation.", file=sys.stderr)
        return 2

    topic = str(packet.get("topic") or "").strip()
    created_at = str(packet.get("created_at") or "").strip()
    if not topic or not created_at:
        print("[fatal] source packet requires non-empty topic and created_at (ISO).", file=sys.stderr)
        return 2

    profile = str(packet.get("profile") or "").strip().lower()
    if not profile:
        print("[fatal] source packet requires profile (see contracts/run-profiles.json).", file=sys.stderr)
        return 2

    from runtime.source_packet_run import packet_age_hours, run_source_packet_pipeline, source_packet_sha256

    sha = source_packet_sha256(pkt_path)
    max_h_raw = (os.environ.get("RFO_STALE_PACKET_MAX_HOURS") or "72").strip()
    try:
        max_h = float(max_h_raw)
    except ValueError:
        max_h = 72.0
    age = packet_age_hours(created_at)
    if not args.allow_stale_packet and age > max_h:
        print(
            f"{_STALE_MSG}: packet age {age:.2f}h > max {max_h}h (topic={topic!r}). "
            f"Use --allow-stale-packet for tests or refresh created_at.",
            file=sys.stderr,
        )
        return 2

    sys.stderr.write(f"[rfo-source-packet] topic={topic!r} source_packet_sha256={sha}\n")
    sys.stderr.flush()

    argv_for_snap = [
        sys.executable,
        str(here / "rfo_execute.py"),
        "--runs-root",
        str(runs_root),
        "--source-packet",
        str(pkt_path),
    ]

    return run_source_packet_pipeline(
        skill_root=skill_root,
        runs_root=runs_root,
        task=topic,
        packet=packet,
        packet_path=pkt_path,
        profile=profile,
        argv_for_snapshot=argv_for_snap,
    )


if __name__ == "__main__":
    raise SystemExit(main())
