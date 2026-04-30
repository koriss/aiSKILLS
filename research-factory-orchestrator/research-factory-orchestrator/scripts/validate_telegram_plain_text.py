#!/usr/bin/env python3
from pathlib import Path
import argparse, re, sys

HTML_TAG = re.compile(r'</?(b|i|u|s|a|code|pre|blockquote|span|div|p|br)\b[^>]*>', re.I)
MD_LINK = re.compile(r'\[[^\]]+\]\([^)]+\)')
MD_TABLE_ROW = re.compile(r'^\s*\|.+\|\s*$', re.M)
MARKDOWN_BOLD = re.compile(r'(\*\*|__)[^*_]+(\*\*|__)')

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("message_file")
    args = ap.parse_args()
    text = Path(args.message_file).read_text(encoding="utf-8", errors="replace")
    errors = []

    if HTML_TAG.search(text):
        errors.append("telegram message contains HTML-like markup")
    if MD_LINK.search(text):
        errors.append("telegram message contains markdown link")
    if MARKDOWN_BOLD.search(text):
        errors.append("telegram message contains markdown bold/underline")
    if MD_TABLE_ROW.search(text):
        errors.append("telegram message contains markdown table row")

    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print("OK: telegram message is plain text")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
