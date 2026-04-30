#!/usr/bin/env python3
from pathlib import Path
import argparse, sys, re

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("html")
    args = ap.parse_args()

    txt = Path(args.html).read_text(encoding="utf-8", errors="replace")
    errors = []
    if "full_url" not in txt:
        errors.append("source table missing full_url column")
    links = re.findall(r'<a\s+[^>]*href=["\'](https?://[^"\']+)["\'][^>]*>(.*?)</a>', txt, flags=re.I|re.S)
    if not links:
        errors.append("no clickable full http(s) source links")
    for href, label in links:
        label_clean = re.sub(r"<[^>]+>", "", label).strip()
        if href not in label_clean and len(label_clean) < 12:
            errors.append(f"link label too vague for full URL: {href}")
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print("OK: HTML full source links validate")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
