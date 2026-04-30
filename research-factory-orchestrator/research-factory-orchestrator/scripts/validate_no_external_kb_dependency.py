#!/usr/bin/env python3
from pathlib import Path
import argparse,re,sys
BAD=[
    r"/home/node/\.openclaw/workspace/research-kb",
    r"/home/node/\.openclaw/workspace/io-kb-unified",
    r"/home/node/cipso",
]

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--skill-dir",default=str(Path(__file__).resolve().parents[1]))
    args=ap.parse_args()
    root=Path(args.skill_dir)
    errors=[]
    for p in root.rglob("*"):
        if not p.is_file() or p.suffix not in [".md",".json",".txt",".html",".yaml",".yml"]:
            continue
        rel=str(p.relative_to(root))
        if rel.startswith("kb/propaganda-io/"):
            continue
        txt=p.read_text(encoding="utf-8",errors="replace")
        for pat in BAD:
            if re.search(pat,txt):
                errors.append(f"external KB dependency pattern {pat} in {rel}")
    if errors:
        print("\n".join(errors),file=sys.stderr)
        return 1
    print("OK: no external KB dependency")
    return 0
if __name__=="__main__":
    raise SystemExit(main())
