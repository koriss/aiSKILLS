"""Long-polling bot skeleton (operator host wiring).

Production deployments should use ``webhook_server.py`` behind TLS reverse
proxy; this module documents the stdlib-only baseline expected by ADR-014.
"""
from __future__ import annotations

import json
import os
import sys


def main() -> int:
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    base = os.environ.get("TELEGRAM_API_BASE", "https://api.telegram.org").rstrip("/")
    if not token:
        print(json.dumps({"error": "TELEGRAM_BOT_TOKEN_required"}, ensure_ascii=False))
        return 2
    print(json.dumps({"status": "skeleton", "hint": "use webhook_server or host-specific runner", "api_base": base}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
