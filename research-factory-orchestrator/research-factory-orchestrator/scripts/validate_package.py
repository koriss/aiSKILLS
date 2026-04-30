#!/usr/bin/env python3
from pathlib import Path
import argparse, zipfile, sys
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("package")
    args=ap.parse_args()
    p=Path(args.package)
    with zipfile.ZipFile(p) as z:
        names=z.namelist()
        errors=[]
        if any(n.startswith("/") or ".." in Path(n).parts for n in names):
            errors.append("unsafe path in package")
        if not any(n.endswith("SKILL.md") for n in names):
            errors.append("missing SKILL.md")
        for info in z.infolist():
            mode=(info.external_attr >> 16) & 0o170000
            if mode == 0o120000:
                errors.append(f"symlink entry rejected: {info.filename}")
        if errors:
            print("\n".join(errors), file=sys.stderr)
            return 1
    print("OK: package validates")
    return 0
if __name__=="__main__":
    raise SystemExit(main())
