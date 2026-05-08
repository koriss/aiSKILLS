#!/usr/bin/env python3
"""Prune old RFO run directories under a runs root (retention policy).

v19.3 compute-only workloads write one directory per run under ``rfo-runs/``.
Without garbage collection, disk usage grows without bound.

Usage::

    python3 scripts/gc_old_runs.py --runs-root ~/.openclaw/workspace/rfo-runs --days 7 --dry-run

Deletes only immediate children named ``RUN-*`` whose mtime is older than ``--days``.
"""
from __future__ import annotations

import argparse
import shutil
import sys
import time
from pathlib import Path


def main() -> int:
    p = argparse.ArgumentParser(description="GC old RFO RUN-* directories.")
    p.add_argument("--runs-root", required=True, type=Path, help="Path to rfo-runs (or equivalent).")
    p.add_argument("--days", type=float, default=7.0, help="Delete RUN-* dirs older than this many days.")
    p.add_argument("--dry-run", action="store_true", help="Print actions only; do not delete.")
    args = p.parse_args()

    root: Path = args.runs_root.resolve()
    if not root.is_dir():
        print(f"runs-root not a directory: {root}", file=sys.stderr)
        return 2

    cutoff = time.time() - float(args.days) * 86400.0
    removed = 0
    scanned = 0

    for child in sorted(root.iterdir()):
        if not child.is_dir():
            continue
        if not child.name.startswith("RUN-"):
            continue
        scanned += 1
        try:
            mtime = child.stat().st_mtime
        except OSError:
            continue
        if mtime >= cutoff:
            continue
        rel = child.relative_to(root)
        if args.dry_run:
            print(f"would remove {rel} (mtime age ~{(time.time() - mtime) / 86400:.1f} d)")
        else:
            shutil.rmtree(child)
            print(f"removed {rel}")
        removed += 1

    print(f"scanned_run_dirs={scanned} removed={removed} dry_run={bool(args.dry_run)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
