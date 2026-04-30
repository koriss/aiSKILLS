#!/usr/bin/env python3
from pathlib import Path
import argparse, json
from common_runtime import now, jwrite

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run_dir")
    args = ap.parse_args()
    root = Path(args.run_dir)
    run = json.loads((root / "run.json").read_text(encoding="utf-8"))
    manifest = {
        "run_id": run["run_id"],
        "entities": [
            {"entity_id": "report/full-report.html", "type": "report"},
            {"entity_id": "package/research-package.zip", "type": "package"}
        ],
        "activities": [
            {"activity_id": "runtime.init", "type": "init_runtime", "time": now()},
            {"activity_id": "render.report", "type": "render", "time": now()}
        ],
        "agents": [
            {"agent_id": "orchestrator", "type": "runtime"},
            {"agent_id": "validator-dag", "type": "validator"}
        ],
        "relations": [
            {"type": "wasGeneratedBy", "entity": "report/full-report.html", "activity": "render.report"}
        ],
        "created_at": now()
    }
    jwrite(root / "provenance-manifest.json", manifest)
    print(root / "provenance-manifest.json")

if __name__ == "__main__":
    main()
