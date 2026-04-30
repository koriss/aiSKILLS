#!/usr/bin/env python3
from pathlib import Path
import argparse,json,sys,hashlib
def sha256(path):
    h=hashlib.sha256(); h.update(Path(path).read_bytes()); return h.hexdigest()
def count_jsonl(path):
    n=0
    with Path(path).open("r",encoding="utf-8",errors="replace") as f:
        for line in f:
            if line.strip(): json.loads(line); n+=1
    return n
def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--skill-dir",default=str(Path(__file__).resolve().parents[1])); args=ap.parse_args()
    root=Path(args.skill_dir); manifest=root/"kb/propaganda-io/embedded-kb-manifest.json"; errors=[]
    if not manifest.exists(): errors.append("embedded-kb-manifest.json missing")
    else:
        data=json.loads(manifest.read_text(encoding="utf-8"))
        if data.get("embedded") is not True or data.get("self_contained") is not True: errors.append("KB manifest does not declare embedded/self_contained true")
        for rel in data.get("required_files",[]):
            p=root/rel
            if not p.exists() or p.stat().st_size==0: errors.append(f"missing/empty required KB file: {rel}")
        raw=root/data.get("raw_archive","")
        if raw.exists() and data.get("raw_archive_sha256") and sha256(raw)!=data.get("raw_archive_sha256"): errors.append("raw archive sha256 mismatch")
        if data.get("normalized",{}).get("canonical_methods",0)<=0: errors.append("normalized canonical_methods empty")
        if data.get("content_diagnostics_summary",{}).get("cross_exact_title_matches_count",0)>0 and not (root/"kb/propaganda-io/normalized/method-crosswalk.json").exists(): errors.append("cross-title overlaps exist but method-crosswalk.json missing")
    for rel in ["kb/propaganda-io/normalized/canonical-records.jsonl","kb/propaganda-io/normalized/canonical-methods.jsonl","kb/propaganda-io/normalized/canonical-sources.jsonl","kb/propaganda-io/normalized/canonical-relations.jsonl"]:
        p=root/rel
        if not p.exists() or count_jsonl(p)<=0: errors.append(f"missing/empty normalized file: {rel}")
    if errors:
        print("\n".join(errors),file=sys.stderr); return 1
    print("OK: embedded IO KB validates"); return 0
if __name__=="__main__": raise SystemExit(main())
