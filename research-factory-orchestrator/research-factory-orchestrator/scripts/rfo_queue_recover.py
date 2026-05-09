#!/usr/bin/env python3
"""
Recover stuck jobs under ``<runs-root>/queue/running/``.

Typical cases:
  • JSON ``status`` is still ``queued`` while the file sits in ``running/`` (path/content mismatch).
  • ``runtime-status.json`` in the job's ``run_dir`` reports ``state: failed`` — move back to pending for retry.

Skipped if the same ``JOB-*.json`` already exists in ``pending`` (avoid overwrite).

Usage::

    python3 -S scripts/rfo_queue_recover.py --runs-root /path/to/rfo-runs
    python3 -S scripts/rfo_queue_recover.py --runs-root … --dry-run
    python3 -S scripts/rfo_queue_recover.py --runs-root … --dead-letter ~/.openclaw/rfo-queue-dlq
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL_ROOT))

from runtime.util import jw  # noqa: E402


def jr(path: Path, default=None):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def should_recover(job: dict, run_dir: Path) -> tuple[bool, str]:
    inner = str(job.get("status") or "").strip().lower()
    if inner == "queued":
        return True, "status_queued_but_file_in_running"
    st = jr(run_dir / "runtime-status.json", {})
    state = ""
    if isinstance(st, dict):
        state = str(st.get("state") or "").strip().lower()
    if state == "failed":
        return True, "runtime_state_failed"
    return False, ""


def main() -> int:
    ap = argparse.ArgumentParser(description="Move stuck RFO queue jobs from running/ back to pending/.")
    ap.add_argument("--runs-root", type=Path, required=True)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument(
        "--dead-letter",
        type=Path,
        default=None,
        help="Instead of pending, atomically move JSON here (preserve filename).",
    )
    args = ap.parse_args()
    root: Path = args.runs_root.resolve()
    pending = root / "queue" / "pending"
    running = root / "queue" / "running"
    dlq: Path | None = args.dead-letter.resolve() if args.dead_letter else None

    if not running.is_dir():
        print(f"no queue/running dir: {running}", file=sys.stderr)
        return 2

    recovered = 0
    scanned = 0
    if dlq:
        dlq.mkdir(parents=True, exist_ok=True)

    for jf in sorted(running.glob("*.json")):
        scanned += 1
        try:
            job = jr(jf, {})
            if not isinstance(job, dict) or not job.get("job_id"):
                continue
            rd = Path(str(job.get("run_dir") or ""))
            ok, reason = should_recover(job, rd)
            if not ok:
                continue
            dest_parent = dlq if dlq else pending
            dest_parent.mkdir(parents=True, exist_ok=True)
            dest = dest_parent / jf.name
            if dest.exists():
                print(f"skip {jf.name}: target exists at {dest}", file=sys.stderr)
                continue
            payload = dict(job)
            payload["status"] = "queued"
            payload["recovered_from"] = "running"
            payload["recover_reason"] = reason
            for k in ("runtime_executed", "package_built", "outbox_events"):
                payload.pop(k, None)

            label = dlq.name if dlq else "pending"
            if args.dry_run:
                print(f"[dry-run] would move {jf.name} → {label}/ ({reason})")
                recovered += 1
                continue

            jw(dest, payload)
            jf.unlink(missing_ok=True)
            print(f"recovered {jf.name} → {dest} ({reason})")
            recovered += 1
        except OSError as e:
            print(f"error handling {jf}: {e}", file=sys.stderr)

    print(json.dumps({"scanned_running": scanned, "recovered": recovered, "dry_run": bool(args.dry_run)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
