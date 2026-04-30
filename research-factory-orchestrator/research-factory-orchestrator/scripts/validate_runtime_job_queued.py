#!/usr/bin/env python3
from pathlib import Path
import argparse, json, sys

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs-root", required=True)
    ap.add_argument("--job", required=True)
    args = ap.parse_args()
    root = Path(args.runs_root)
    job = json.loads(Path(args.job).read_text(encoding="utf-8"))
    errors = []
    if job.get("runtime_entrypoint") != "scripts/run_research_factory.py":
        errors.append("runtime_entrypoint invalid")
    if job.get("status") != "queued":
        errors.append("job status is not queued")
    q = root / "queue" / "pending" / f"{job.get('job_id')}.json"
    if not q.exists():
        errors.append("job not present in queue/pending")
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print("OK: runtime job queued")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
