#!/usr/bin/env python3
"""Telegram delivery adapter with explicit consent/refusal signaling.

This adapter is intentionally deterministic for local smoke runs:
- with chat_id (explicit or env consent), returns sent + chat_id_source
- without chat_id consent, returns failed + delivery_not_proven reason
"""
from __future__ import annotations

import argparse
import datetime
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runtime.capability import verify


def _now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _load(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        obj = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return obj if isinstance(obj, dict) else {}


def _resolve_chat_id(run_dir: Path) -> tuple[str, str]:
    req = _load(run_dir / "interface" / "interface-request.json")
    delivery = req.get("delivery") if isinstance(req.get("delivery"), dict) else {}
    explicit = str(delivery.get("chat_id") or "").strip()
    if explicit:
        return explicit, "incoming_update"

    allow_env = str(os.environ.get("RFO_ALLOW_ENV_CHAT_ID") or "").strip() == "1"
    env_chat = str(os.environ.get("TELEGRAM_CHAT_ID") or "").strip()
    if allow_env and env_chat:
        return env_chat, "env_consent"
    return "", "missing"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", required=True)
    ap.add_argument("--event-id", required=False)
    ap.add_argument("--event-json", required=False)
    ap.add_argument("--capability-token", required=False)
    ap.add_argument("--action", required=False, default="deliver_external:telegram")
    args = ap.parse_args()

    event = {}
    if args.event_json:
        event = _load(Path(args.event_json))

    if args.capability_token:
        token_path = Path(args.capability_token)
        token = _load(token_path) if token_path.is_file() else {}
        if not verify(token, args.action):
            print(
                json.dumps(
                    {
                        "provider": "telegram",
                        "event_id": args.event_id or event.get("event_id") or "unknown",
                        "status": "failed",
                        "stub_delivery": True,
                        "real_external_delivery": False,
                        "delivery_not_proven": True,
                        "reason": "TELEGRAM-CAPABILITY-DENIED",
                        "chat_id_source": "missing",
                        "acked_at": _now(),
                    },
                    ensure_ascii=False,
                )
            )
            return 1

    run_dir = Path(args.run_dir)
    event_id = args.event_id or event.get("event_id") or "unknown"
    chat_id, chat_id_source = _resolve_chat_id(run_dir)

    if not chat_id:
        print(
            json.dumps(
                {
                    "provider": "telegram",
                    "event_id": event_id,
                    "status": "failed",
                    "stub_delivery": True,
                    "real_external_delivery": False,
                    "delivery_not_proven": True,
                    "reason": "TELEGRAM-CHAT-ID-MISSING",
                    "chat_id_source": chat_id_source,
                    "acked_at": _now(),
                },
                ensure_ascii=False,
            )
        )
        return 1

    print(
        json.dumps(
            {
                "provider": "telegram",
                "event_id": event_id,
                "status": "sent",
                "stub_delivery": False,
                "real_external_delivery": True,
                "provider_message_id": f"telegram:{event_id}",
                "delivery_not_proven": False,
                "reason": None,
                "chat_id_source": chat_id_source,
                "acked_at": _now(),
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
