#!/usr/bin/env python3
from __future__ import annotations
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main()->int:
    os.environ.setdefault('RFO_V19_PROFILE','mvr')
    before=set(sys.modules)
    import runtime.validate_impl as _v  # noqa:F401
    after=set(sys.modules)
    bad=[m for m in sorted(after-before) if m.startswith('legacy.subagents') or m.startswith('runtime.subagent')]
    print(json.dumps({'status':'fail' if bad else 'pass','forbidden_loaded':bad},ensure_ascii=False,indent=2))
    return 1 if bad else 0

if __name__=='__main__':
    raise SystemExit(main())
