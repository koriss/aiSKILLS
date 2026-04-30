#!/usr/bin/env python3
from pathlib import Path
import argparse, subprocess, sys, zipfile, hashlib, json, shutil

def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024*1024), b""):
            h.update(chunk)
    return h.hexdigest()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("skill_dir")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    root = Path(args.skill_dir)

    for p in list(root.rglob("__pycache__")):
        shutil.rmtree(p, ignore_errors=True)
    for p in root.rglob("*.pyc"):
        p.unlink(missing_ok=True)

    r = subprocess.run([sys.executable, str(root / "scripts" / "validate_skill.py"), str(root)], capture_output=True, text=True, timeout=120)
    if r.returncode != 0:
        print(r.stdout)
        print(r.stderr, file=sys.stderr)
        return r.returncode

    out = Path(args.out)
    if out.exists():
        out.unlink()
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for p in sorted(root.rglob("*")):
            if p.is_file():
                if p.is_symlink():
                    raise RuntimeError(f"symlink not allowed: {p}")
                z.write(p, (Path("research-factory-orchestrator") / p.relative_to(root)).as_posix())

    manifest = {"package": str(out), "sha256": sha256(out), "size": out.stat().st_size}
    out.with_suffix(out.suffix + ".manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(out)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
