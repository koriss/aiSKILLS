#!/usr/bin/env python3
from pathlib import Path
import argparse, json, re

REQUIRED_IDS = [
    "semantic-report-json",
    "artifact-manifest-json",
    "provenance-manifest-json",
    "validation-transcript-json",
    "delivery-manifest-json",
    "runtime-status-json",
    "entrypoint-proof-json",
    "final-answer-gate-json",
]

def resolve(path):
    p=Path(path)
    return p/"report"/"full-report.html" if p.is_dir() else p

def extract(text):
    out={}
    for m in re.finditer(r'<script[^>]+type=["\']application/json["\'][^>]*id=["\']([^"\']+)["\'][^>]*>(.*?)</script>', text, re.I|re.S):
        out[m.group(1)] = m.group(2).strip()
    return out

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("path"); args=ap.parse_args()
    p=resolve(args.path)
    errors=[]
    if not p.exists():
        errors.append(f"missing html {p}")
    else:
        blocks=extract(p.read_text(encoding="utf-8", errors="replace"))
        for sid in REQUIRED_IDS:
            raw=blocks.get(sid)
            if raw is None:
                errors.append(f"missing proof block {sid}")
                continue
            if raw in ["", "{}"]:
                errors.append(f"empty proof block {sid}")
                continue
            try:
                json.loads(raw)
            except Exception as e:
                errors.append(f"invalid JSON in {sid}: {e}")
    print(json.dumps({"status":"pass" if not errors else "fail","errors":errors}, ensure_ascii=False, indent=2))
    return 0 if not errors else 1
if __name__=="__main__":
    raise SystemExit(main())
