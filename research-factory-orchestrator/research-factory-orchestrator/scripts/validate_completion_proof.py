#!/usr/bin/env python3
from pathlib import Path
import argparse, json, sys, hashlib

def sha256(p):
    h = hashlib.sha256()
    h.update(Path(p).read_bytes())
    return h.hexdigest()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("completion_proof")
    ap.add_argument("--root", default=None)
    args = ap.parse_args()

    proof_path = Path(args.completion_proof)
    root = Path(args.root) if args.root else proof_path.parent
    data = json.loads(proof_path.read_text(encoding="utf-8"))
    errors = []

    if data.get("final_delivery_allowed") is not True:
        errors.append("final_delivery_allowed != true")
    if data.get("stage_count_completed", 0) < data.get("stage_count_required", 999):
        errors.append("stage_count_completed < stage_count_required")
    if not data.get("artifacts"):
        errors.append("no artifacts in completion proof")
    if not data.get("validators"):
        errors.append("no validators in completion proof")

    for art in data.get("artifacts", []):
        rel = art.get("path")
        if not rel:
            errors.append("artifact missing path")
            continue
        p = root / rel
        if not p.exists():
            errors.append(f"artifact missing: {rel}")
            continue
        if p.stat().st_size == 0:
            errors.append(f"artifact empty: {rel}")
        if art.get("sha256") and sha256(p) != art.get("sha256"):
            errors.append(f"sha256 mismatch: {rel}")

    for val in data.get("validators", []):
        if val.get("status") not in ["pass", "blocked"]:
            errors.append(f"validator not pass/blocked: {val.get('name')}={val.get('status')}")

    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print("OK: completion proof validates")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
