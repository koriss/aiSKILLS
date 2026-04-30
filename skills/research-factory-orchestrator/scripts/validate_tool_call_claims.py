#!/usr/bin/env python3
from pathlib import Path
import argparse, json, re, sys

TOOL_CLAIM = re.compile(r'(opened|fetched|browser|web_fetch|ask-search|tool_call|открыл|прочитал страницу|запросил|использовал инструмент)', re.I)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--text", required=True)
    ap.add_argument("--tool-ledger", required=True)
    args = ap.parse_args()
    text = Path(args.text).read_text(encoding="utf-8", errors="ignore")
    ledger = json.loads(Path(args.tool_ledger).read_text(encoding="utf-8"))
    if TOOL_CLAIM.search(text) and not ledger.get("tool_calls"):
        print("tool-use claim present but tool-call-ledger is empty", file=sys.stderr)
        return 1
    print("OK: tool-call claims consistent with ledger")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
