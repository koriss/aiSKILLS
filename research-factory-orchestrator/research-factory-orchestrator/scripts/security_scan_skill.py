#!/usr/bin/env python3
from pathlib import Path
import argparse, sys, re

BAD_PATTERNS = [
    r"curl\s+[^|]*\|\s*(sh|bash)",
    r"wget\s+[^|]*\|\s*(sh|bash)",
    r"base64\s+-d\s*\|",
    r"rm\s+-rf\s+/",
    r"cat\s+.*(\.env|id_rsa|credentials|secret)",
    r"printenv",
    r"curl\s+.*(webhook|discord|telegram|pastebin)"
]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("skill_dir")
    args = ap.parse_args()
    root = Path(args.skill_dir)
    errors = []
    for p in root.rglob("*"):
        if p.is_symlink():
            errors.append(f"symlink rejected: {p}")
            continue
        if p.is_file() and p.suffix in [".md", ".py", ".sh", ".txt"]:
            txt = p.read_text(encoding="utf-8", errors="ignore")
            for pat in BAD_PATTERNS:
                if re.search(pat, txt, re.I):
                    errors.append(f"suspicious pattern {pat!r} in {p}")
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print("OK: basic security scan passed")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
