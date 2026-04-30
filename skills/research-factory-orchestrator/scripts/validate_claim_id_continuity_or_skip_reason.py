#!/usr/bin/env python3
from pathlib import Path
import argparse, json, re

def resolve(path):
    p=Path(path)
    return p/"report"/"full-report.html" if p.is_dir() else p

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("path"); args=ap.parse_args()
    p=resolve(args.path)
    errors=[]
    if not p.exists():
        errors.append(f"missing {p}")
    else:
        text=p.read_text(encoding="utf-8", errors="replace")
        ids=sorted({int(x) for x in re.findall(r"\bC(\d{3})\b", text)})
        if ids:
            missing=[i for i in range(min(ids), max(ids)+1) if i not in ids]
            if missing:
                # Allow explicit skipped_claims ledger inside HTML JSON.
                has_skip = "skipped_claims" in text and all(f"C{i:03d}" in text for i in missing)
                if not has_skip:
                    errors.append("claim id gaps without skipped_claims reasons: "+", ".join(f"C{i:03d}" for i in missing))
    print(json.dumps({"status":"pass" if not errors else "fail","errors":errors}, ensure_ascii=False, indent=2))
    return 0 if not errors else 1
if __name__=="__main__":
    raise SystemExit(main())
