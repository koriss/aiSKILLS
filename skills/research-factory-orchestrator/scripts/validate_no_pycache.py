#!/usr/bin/env python3
from pathlib import Path
import json
root=Path(__file__).resolve().parents[1]
items=[str(p.relative_to(root)) for p in root.rglob('*') if p.name=='__pycache__' or p.suffix=='.pyc']
print(json.dumps({'status':'pass' if not items else 'fail','items':items}, ensure_ascii=False, indent=2))
raise SystemExit(1 if items else 0)
