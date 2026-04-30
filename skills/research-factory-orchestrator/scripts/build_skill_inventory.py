#!/usr/bin/env python3
from pathlib import Path
import json, sys, hashlib, re, time
sys.dont_write_bytecode=True

def sha256(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024), b''):
            h.update(chunk)
    return h.hexdigest()

def main():
    root = Path(sys.argv[1]).resolve() if len(sys.argv)>1 else Path(__file__).resolve().parents[1]
    out_dir = Path(sys.argv[2]).resolve() if len(sys.argv)>2 else root/'context'
    out_dir.mkdir(parents=True, exist_ok=True)
    files=[]
    for p in sorted(root.rglob('*')):
        if p.is_file() and '.git' not in p.parts and '__pycache__' not in p.parts:
            rel=str(p.relative_to(root))
            files.append({'file':rel,'bytes':p.stat().st_size,'sha256':sha256(p),'operation':'index','status':'ok'})
    total_bytes=sum(x['bytes'] for x in files)
    result={'root':str(root),'total_files':len(files),'total_bytes':total_bytes,'files':files}
    (out_dir/'file-inventory.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'status':'pass','inventory':str(out_dir/'file-inventory.json'),'total_files':len(files),'total_bytes':total_bytes},ensure_ascii=False))
if __name__=='__main__': main()
