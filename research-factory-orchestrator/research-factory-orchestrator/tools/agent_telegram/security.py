"""Operator control-plane security helpers (stdlib-only).

Invariants: fixed argv surfaces, chat allowlist, secret redaction in logs.
"""
from __future__ import annotations

import os
import re
from typing import Iterable


def allowed_chat_ids() -> set[str]:
    raw = os.environ.get("TELEGRAM_ALLOWED_CHAT_IDS", "").strip()
    if not raw:
        return set()
    return {x.strip() for x in raw.split(",") if x.strip()}


def chat_id_allowed(chat_id: str) -> bool:
    allow = allowed_chat_ids()
    if not allow:
        return True
    return str(chat_id).strip() in allow


def redact_secrets(text: str, tokens: Iterable[str] | None = None) -> str:
    out = text
    for name in ("TELEGRAM_BOT_TOKEN", "TELEGRAM_WEBHOOK_SECRET", "TELEGRAM_API_BASE"):
        val = os.environ.get(name, "")
        if val and len(val) > 6:
            out = out.replace(val, f"<{name}_REDACTED>")
    if tokens:
        for t in tokens:
            if t and len(str(t)) > 6:
                out = out.replace(str(t), "<TOKEN_REDACTED>")
    out = re.sub(r"bot\d+:[A-Za-z0-9_-]{20,}", "<BOT_TOKEN_REDACTED>", out)
    return out
