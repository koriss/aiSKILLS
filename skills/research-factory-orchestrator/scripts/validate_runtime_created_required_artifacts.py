#!/usr/bin/env python3
from pathlib import Path
import argparse, json, sys
def main():
    ap=argparse.ArgumentParser(); ap.add_argument("run_dir"); ap.add_argument("--skill-dir", required=True); args=ap.parse_args()
    contract=json.loads((Path(args.skill_dir)/"contracts"/"artifact-contract.json").read_text(encoding="utf-8"))
    errors=[rel for rel in contract["required_run_artifacts"] if not (Path(args.run_dir)/rel).exists()]
    if errors:
        print("missing required run artifacts:\n"+"\n".join(errors), file=sys.stderr); return 1
    print("OK: runtime created required artifacts"); return 0
if __name__=="__main__": raise SystemExit(main())
