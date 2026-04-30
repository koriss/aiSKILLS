#!/usr/bin/env python3
from pathlib import Path
import argparse, json, re

PLACEHOLDER_PATTERNS = [
    r"<h1>\s*Placeholder\s*</h1>",
    r"\bplaceholder-level\b",
    r"\bTODO\b",
    r"\bSTUB REPORT\b",
]

def resolve(path):
    p=Path(path)
    return p/"report"/"full-report.html" if p.is_dir() else p

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("path"); args=ap.parse_args()
    p=resolve(args.path)
    if not p.exists():
        print(json.dumps({"status":"fail","errors":[f"missing html {p}"]}, ensure_ascii=False, indent=2)); return 1
    text=p.read_text(encoding="utf-8", errors="replace")
    errors=[]
    for pat in PLACEHOLDER_PATTERNS:
        if re.search(pat, text, re.I):
            errors.append(f"placeholder pattern matched: {pat}")
    if len(re.sub(r"<[^>]+>", " ", text).strip()) < 400:
        errors.append("html textual content too short for report")
    print(json.dumps({"status":"pass" if not errors else "fail","errors":errors}, ensure_ascii=False, indent=2))
    return 0 if not errors else 1
if __name__=="__main__":
    raise SystemExit(main())
