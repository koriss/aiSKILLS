#!/usr/bin/env python3
import json, sys, re
from pathlib import Path

def load_json(path, default=None):
    p=Path(path)
    if not p.exists(): return default
    try: return json.loads(p.read_text(encoding='utf-8'))
    except Exception as e: return {'__invalid_json__': str(e)}

def emit(status='pass', code='OK', **kw):
    print(json.dumps({'status':status,'code':code,**kw}, ensure_ascii=False, indent=2))
    return 0 if status in ('pass','warning') else 1


def main():
    root=Path(sys.argv[1]) if len(sys.argv)>1 else Path('.')
    # Governance: contracts isolate seed-only / harness paths from prod acceptance claims.
    c = load_json(root / "contracts/seed-only-run-contract.json", None) or load_json(
        Path(__file__).resolve().parents[1] / "contracts/seed-only-run-contract.json", {}
    )
    if not c or c.get("harness_is_local_only") is not True:
        return emit("fail", "F351", message="seed-only harness not isolated from prod acceptance")
    return emit('pass','F351')
if __name__=='__main__': raise SystemExit(main())

