#!/usr/bin/env python3
from pathlib import Path
import argparse, json, re, sys

CLAIM = re.compile(r'(full pipeline|strict research factory|multi-agent|subagents?|fanout|work-units?|полный pipeline|полный пайплайн|сабагент|субагент|воркер|work[- ]?unit)', re.I)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--status", required=True)
    ap.add_argument("--text", required=True)
    args = ap.parse_args()
    status = json.loads(Path(args.status).read_text(encoding="utf-8"))
    text = Path(args.text).read_text(encoding="utf-8", errors="ignore")
    if not CLAIM.search(text):
        print("OK: no pipeline/status claim in text")
        return 0
    errors = []
    if status.get("entrypoint") != "scripts/run_research_factory.py":
        errors.append("text claims pipeline but status entrypoint is not runtime")
    if status.get("work_units_total", 0) <= 1:
        errors.append("text claims pipeline but work_units_total <= 1")
    if status.get("workers_planned", 0) <= 1:
        errors.append("text claims pipeline but workers_planned <= 1")
    if status.get("state") in ["created", "failed", "cancelled"]:
        errors.append("text claims pipeline but runtime state is not active/compiled")
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print("OK: status claim consistent with runtime-status")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
