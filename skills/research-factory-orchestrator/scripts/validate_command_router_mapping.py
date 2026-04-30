#!/usr/bin/env python3
from pathlib import Path
import argparse, json, sys

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("skill_dir")
    args = ap.parse_args()
    path = Path(args.skill_dir) / "contracts" / "command-router-contract.json"
    if not path.exists():
        print("missing command-router-contract.json", file=sys.stderr)
        return 1
    data = json.loads(path.read_text(encoding="utf-8"))
    errors = []
    for cmd in ["/research_factory_orchestrator", "/research"]:
        cfg = data.get("commands", {}).get(cmd)
        if not cfg:
            errors.append(f"missing command mapping: {cmd}")
            continue
        if cfg.get("entrypoint") != "scripts/run_research_factory.py":
            errors.append(f"{cmd}: wrong entrypoint")
        if cfg.get("mode") != "runtime":
            errors.append(f"{cmd}: mode != runtime")
        forbidden = set(cfg.get("forbidden", []))
        for f in ["plain_subagent", "read_skill_md_and_execute", "single_worker"]:
            if f not in forbidden:
                errors.append(f"{cmd}: missing forbidden pattern {f}")
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print("OK: command router mapping validates")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
