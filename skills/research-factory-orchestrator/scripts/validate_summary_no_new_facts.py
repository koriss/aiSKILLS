#!/usr/bin/env python3
from pathlib import Path
import argparse, json, re, sys

def words(text):
    return set(re.findall(r'[A-Za-zА-Яа-яЁё0-9]{4,}', text.lower()))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--summary", required=True)
    ap.add_argument("--claims", required=True)
    args = ap.parse_args()
    summary = Path(args.summary).read_text(encoding="utf-8", errors="ignore")
    claims = json.loads(Path(args.claims).read_text(encoding="utf-8"))
    claim_text = " ".join(str(c.get("text") or c.get("claim") or "") for c in claims.get("claims", []))
    # Soft lexical smoke test: catches completely unrelated summaries, not a proof of faithfulness.
    s_words = words(summary)
    c_words = words(claim_text)
    if len(s_words) >= 20 and len(c_words) >= 20:
        overlap = len(s_words & c_words) / max(1, len(s_words))
        if overlap < 0.12:
            print(f"summary appears weakly grounded in claims, lexical overlap={overlap:.3f}", file=sys.stderr)
            return 1
    print("OK: summary smoke-check passes against claims")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
