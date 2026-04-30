#!/usr/bin/env python3
from pathlib import Path
import argparse, json, datetime

def now():
    return datetime.datetime.now(datetime.UTC).replace(microsecond=0).isoformat().replace("+00:00","Z")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--project-dir", required=True)
    args = ap.parse_args()
    root = Path(args.project_dir)
    ledger_path = root / "shard-ledger.json"
    state = {"task_id": root.name, "running": [], "stale": [], "failed_retryable": [], "unmerged": [], "blocked_final_delivery": False, "updated_at": now()}
    if ledger_path.exists():
        ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
        for s in ledger.get("shards", []):
            st = s.get("status")
            wid = s.get("work_unit_id")
            if st == "running":
                state["running"].append(wid)
            if st == "stale":
                state["stale"].append(wid)
            if st == "failed_retryable":
                state["failed_retryable"].append(wid)
            if s.get("merge_status") not in ["merged", "not_applicable"]:
                state["unmerged"].append(wid)
    state["blocked_final_delivery"] = any(state[k] for k in ["running","stale","failed_retryable","unmerged"])
    (root / "watchdog-state.json").write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(state, ensure_ascii=False, indent=2))
if __name__ == "__main__":
    main()
