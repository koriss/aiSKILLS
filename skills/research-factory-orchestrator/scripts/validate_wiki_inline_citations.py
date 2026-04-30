#!/usr/bin/env python3
from pathlib import Path
import argparse, re, sys, json

SUP_RE = re.compile(r'<sup>\s*<a\s+href=["\']#(ref-\d+)["\']>\[(\d+)\]</a>\s*</sup>', re.I)
LI_RE = re.compile(r'<li\s+id=["\'](ref-\d+)["\'][^>]*>(.*?)</li>', re.I | re.S)
URL_RE = re.compile(r'https?://[^\s<>"\']+', re.I)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("html")
    ap.add_argument("--claims", default=None)
    args = ap.parse_args()

    txt = Path(args.html).read_text(encoding="utf-8", errors="replace")
    errors = []

    markers = SUP_RE.findall(txt)
    if not markers:
        errors.append("no wiki-style inline citations found")

    refs = {m.group(1): m.group(2) for m in LI_RE.finditer(txt)}
    for ref_id, n in markers:
        if ref_id not in refs:
            errors.append(f"inline citation points to missing bibliography ref: {ref_id}")

    for ref_id, body in refs.items():
        if not URL_RE.search(body):
            errors.append(f"bibliography ref missing full URL: {ref_id}")

    if args.claims:
        claims = json.loads(Path(args.claims).read_text(encoding="utf-8")).get("claims", [])
        html_lower = txt.lower()
        for c in claims:
            if c.get("verification_status") == "confirmed":
                cid = str(c.get("claim_id", "")).lower()
                if cid and cid not in html_lower:
                    errors.append(f"confirmed claim_id not present in HTML: {c.get('claim_id')}")
                # Allow either claim_id vicinity or claim citation map; this is a structural validator.
                if cid and cid in html_lower:
                    pos = html_lower.find(cid)
                    window = txt[max(0, pos-500):pos+1000]
                    if not SUP_RE.search(window):
                        errors.append(f"confirmed claim lacks nearby inline citation marker: {c.get('claim_id')}")

    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print("OK: wiki-style inline citations validate")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
