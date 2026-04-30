#!/usr/bin/env python3
from pathlib import Path
import argparse, json, sys

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run_dir")
    args = ap.parse_args()
    root = Path(args.run_dir)
    proof = root / "entrypoint-proof.json"
    if not proof.exists():
        print("missing entrypoint-proof.json", file=sys.stderr)
        return 1
    data = json.loads(proof.read_text(encoding="utf-8"))
    errors = []
    if data.get("entrypoint") != "scripts/run_research_factory.py":
        errors.append("wrong entrypoint")
    if data.get("invocation_mode") != "runtime":
        errors.append("invocation_mode != runtime")
    if data.get("not_plain_subagent") is not True:
        errors.append("plain subagent not excluded")
    if data.get("not_skill_md_imitation") is not True:
        errors.append("SKILL.md imitation not excluded")
    for rel in data.get("created_artifacts", []):
        if not (root / rel).exists():
            errors.append(f"created artifact missing: {rel}")
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print("OK: runtime entrypoint validates")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
