#!/usr/bin/env python3
from pathlib import Path
import json, datetime, re, hashlib

VERSION = "18.3.2-delivery-truth-smoke-runtime-contract-hotfix"
STATES = ["created","compiled","collecting","subagents_running","subagent_timeout_detected","recovery_running","quorum_check","coverage_check","partial_ready","synthesis_ready","validating","delivery_ready","delivered","failed","cancelled"]
AXES = ["entity_resolution","primary_origin_sources","broad_sweep","contrary_adversarial_search","source_quality_provenance","timeline_freshness","structured_data","claim_factcheck","strong_tie_pivoting","contact_media_graph","raw_evidence_vault","synthesis_merge"]
SOURCE_FAMILIES = ["primary_or_origin","official_or_institutional","independent_media","registry_or_database","contrary_or_debunking","archive_or_cached"]

def now():
    return datetime.datetime.now(datetime.UTC).replace(microsecond=0).isoformat().replace("+00:00","Z")

def slugify(s):
    s=s.lower()
    tr={"ё":"e","й":"i","ц":"c","у":"u","к":"k","е":"e","н":"n","г":"g","ш":"sh","щ":"sch","з":"z","х":"h","ъ":"","ф":"f","ы":"y","в":"v","а":"a","п":"p","р":"r","о":"o","л":"l","д":"d","ж":"zh","э":"e","я":"ya","ч":"ch","с":"s","м":"m","и":"i","т":"t","ь":"","б":"b","ю":"yu"}
    s="".join(tr.get(ch,ch) for ch in s)
    return re.sub(r"[^a-z0-9]+","-",s).strip("-")[:64] or "research"

def jwrite(path, obj):
    path=Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    tmp.replace(path)

def twrite(path, text):
    path=Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(str(text).rstrip()+"\n", encoding="utf-8")
    tmp.replace(path)

def jread(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))

def event(run_dir, event_name, status="ok", **kw):
    rec={"event_name":event_name,"timestamp":now(),"status":status}
    rec.update(kw)
    p=Path(run_dir)/"observability-events.jsonl"
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False)+"\n")
