#!/usr/bin/env python3
from pathlib import Path
import argparse,json,re
def tokenize(s): return set(re.findall(r"[\wА-Яа-яЁё-]{3,}",str(s).lower()))
def main():
    ap=argparse.ArgumentParser(); ap.add_argument("query"); ap.add_argument("--skill-dir",default=str(Path(__file__).resolve().parents[1])); ap.add_argument("--limit",type=int,default=20); args=ap.parse_args()
    data=json.loads((Path(args.skill_dir)/"kb/propaganda-io/io-method-index.json").read_text(encoding="utf-8")); qtok=tokenize(args.query); results=[]
    for r in data.get("records",[]):
        score=len(qtok & tokenize(" ".join(str(r.get(k,"")) for k in ["title","category","search_text"])))
        if score: results.append({"score":score,**{k:r.get(k) for k in ["canonical_id","record_kind","kb_source","title","category","quality_score","safe_use"]}})
    results=sorted(results,key=lambda x:(-x["score"],-(x.get("quality_score") or 0),x.get("title","")))[:args.limit]
    print(json.dumps({"query":args.query,"count":len(results),"results":results},ensure_ascii=False,indent=2))
if __name__=="__main__": main()
