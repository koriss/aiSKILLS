#!/usr/bin/env python3
from pathlib import Path
import ast, json
root=Path(__file__).resolve().parents[1]
errors=[]
for p in root.rglob('*.py'):
    try: ast.parse(p.read_text(encoding='utf-8'))
    except Exception as e: errors.append({'path':str(p.relative_to(root)),'error':str(e)})
print(json.dumps({'status':'pass' if not errors else 'fail','errors':errors}, ensure_ascii=False, indent=2))
raise SystemExit(1 if errors else 0)
