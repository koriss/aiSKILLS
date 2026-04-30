#!/usr/bin/env python3
from pathlib import Path
import argparse, json, sys
def main():
    ap=argparse.ArgumentParser(); ap.add_argument("run_dir"); args=ap.parse_args()
    root=Path(args.run_dir); strategy=root/"search-strategy.md"; ledger=root/"ledgers"/"search-ledger.json"
    if strategy.exists() and not ledger.exists():
        print("search-strategy.md exists but ledgers/search-ledger.json missing", file=sys.stderr); return 1
    if ledger.exists():
        d=json.loads(ledger.read_text(encoding="utf-8"))
        if strategy.exists() and not d.get("searches"):
            print("search-ledger exists but is empty", file=sys.stderr); return 1
    print("OK: search strategy has execution ledger"); return 0
if __name__=="__main__": raise SystemExit(main())
