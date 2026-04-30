#!/usr/bin/env python3
from pathlib import Path
import json, datetime, hashlib, re

VERSION = "17.1.0-runtime-lifecycle-hardening"

def now():
    return datetime.datetime.now(datetime.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")

def short_hash(text):
    return hashlib.sha1(text.encode("utf-8")).hexdigest()[:10]

def jwrite(path, obj):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)

def jread(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))

def twrite(path, text):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(str(text).rstrip() + "\n", encoding="utf-8")
    tmp.replace(path)

def ensure_queue(root):
    root = Path(root)
    for d in ["queue/pending", "queue/running", "queue/done", "queue/failed"]:
        (root / d).mkdir(parents=True, exist_ok=True)

def atomic_move(src, dst):
    src = Path(src)
    dst = Path(dst)
    dst.parent.mkdir(parents=True, exist_ok=True)
    src.replace(dst)
