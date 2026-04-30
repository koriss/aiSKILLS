#!/usr/bin/env python3
from pathlib import Path
import argparse, json, sys

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run_dir")
    args = ap.parse_args()
    root = Path(args.run_dir)
    proof = root / "entrypoint-proof.json"
    status = root / "runtime-status.json"
    errors = []
    if not proof.exists():
        errors.append("missing entrypoint-proof.json")
    if not status.exists():
        errors.append("missing runtime-status.json")
    if not errors:
        p = json.loads(proof.read_text(encoding="utf-8"))
        s = json.loads(status.read_text(encoding="utf-8"))
        if p.get("run_id") != s.get("run_id"):
            errors.append("run_id mismatch between proof and status")
        if s.get("state") not in ["compiled", "collecting", "subagents_running", "synthesis_ready", "delivery_ready", "delivered", "stub_delivered"]:
            errors.append("startup/runtime state invalid")
        if s.get("workers_planned", 0) <= 1:
            errors.append("workers_planned <= 1")
        if s.get("work_units_total", 0) <= 1:
            errors.append("work_units_total <= 1")
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print("OK: startup runtime proof validates")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
