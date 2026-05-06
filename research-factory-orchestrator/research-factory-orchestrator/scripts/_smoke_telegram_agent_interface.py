#!/usr/bin/env python3
"""Contract smoke: operator Telegram tools import + fixed-argv runner wiring."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    sys.path.insert(0, str(ROOT))
    from tools.agent_telegram import security  # noqa: PLC0415

    if not security.chat_id_allowed("1") and security.allowed_chat_ids():
        print(json.dumps({"status": "fail", "error": "allowlist_logic"}, ensure_ascii=False))
        return 1
    sec = security.redact_secrets("prefix bot123:abcdefghijklmnopqrst token suffix", tokens=())
    if "bot123:" in sec and "REDACTED" not in sec:
        print(json.dumps({"status": "fail", "error": "redaction_pattern"}, ensure_ascii=False))
        return 1
    need = [
        ROOT / "tools" / "agent_telegram" / "README.md",
        ROOT / "tools" / "agent_telegram" / "security.py",
        ROOT / "tools" / "agent_telegram" / "runner.py",
        ROOT / "tools" / "agent_telegram" / "webhook_server.py",
    ]
    missing = [str(p.relative_to(ROOT)) for p in need if not p.is_file()]
    if missing:
        print(json.dumps({"status": "fail", "missing": missing}, ensure_ascii=False))
        return 1
    print(json.dumps({"status": "pass", "smoke_id": "_smoke_telegram_agent_interface"}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
