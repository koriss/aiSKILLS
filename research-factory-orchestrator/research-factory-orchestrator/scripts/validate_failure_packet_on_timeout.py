#!/usr/bin/env python3
from pathlib import Path
import argparse, json, sys
def main():
    ap=argparse.ArgumentParser(); ap.add_argument("subagent_ledger"); ap.add_argument("--failure-dir", required=True); args=ap.parse_args()
    d=json.loads(Path(args.subagent_ledger).read_text(encoding="utf-8")); errors=[]; fd=Path(args.failure_dir)
    for s in d.get("subagents",[]):
        if s.get("status")=="timeout" and not (fd/f"{s.get('subagent_id')}-failure-packet.json").exists():
            errors.append(f"{s.get('subagent_id')}: timeout without failure packet")
    if errors:
        print("\n".join(errors), file=sys.stderr); return 1
    print("OK: timeouts have failure packets"); return 0
if __name__=="__main__": raise SystemExit(main())
