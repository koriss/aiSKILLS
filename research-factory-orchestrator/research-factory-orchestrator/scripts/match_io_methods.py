#!/usr/bin/env python3
from pathlib import Path
import argparse,json,re,hashlib
def tokenize(s): return set(re.findall(r"[\wА-Яа-яЁё-]{4,}",str(s).lower()))
def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--text-file",required=True); ap.add_argument("--skill-dir",default=str(Path(__file__).resolve().parents[1])); ap.add_argument("--out",default=None); ap.add_argument("--limit",type=int,default=30); args=ap.parse_args()
    text=Path(args.text_file).read_text(encoding="utf-8",errors="replace"); ttok=tokenize(text)
    idx=json.loads((Path(args.skill_dir)/"kb/propaganda-io/io-method-index.json").read_text(encoding="utf-8")); matches=[]
    for r in idx.get("records",[]):
        score=len(ttok & tokenize(" ".join(str(r.get(k,"")) for k in ["title","category","search_text"])))
        if score>=2:
            q=float(r.get("quality_score") or 0.4); conf=round(min(0.95,0.20+score/20+q/3),3)
            matches.append({"match_id":"IOMATCH_"+hashlib.sha1((r["canonical_id"]+str(score)).encode()).hexdigest()[:10],"kb_record_id":r["canonical_id"],"kb_source":r["kb_source"],"matched_claim_id":None,"matched_text":Path(args.text_file).name,"match_reason":f"lexical_overlap_score={score}; quality_score={q}","confidence":conf,"safe_use":"analytic_classification_only","title":r.get("title"),"category":r.get("category")})
    matches=sorted(matches,key=lambda x:-x["confidence"])[:args.limit]; out={"matches":matches,"count":len(matches),"safe_use":"analytic_classification_only"}
    if args.out: Path(args.out).write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(out,ensure_ascii=False,indent=2))
if __name__=="__main__": main()
