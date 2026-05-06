#!/usr/bin/env python3
"""Telegram delivery adapter with optional capability-token verification.

When ``TELEGRAM_API_BASE``, ``TELEGRAM_BOT_TOKEN``, and ``TELEGRAM_CHAT_ID``
are set, performs a real Bot API ``sendMessage`` POST (used by integration
smokes against a local mock server). Otherwise returns the historical stub
result (no external HTTP).
"""
from __future__ import annotations

import argparse
import datetime
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from runtime.capability import verify

ap = argparse.ArgumentParser()
ap.add_argument("--run-dir", required=False)
ap.add_argument("--event-id", required=False)
ap.add_argument("--event-json", required=False)
ap.add_argument("--capability-token", required=False)
ap.add_argument("--action", required=False, default="deliver_external:telegram")
args = ap.parse_args()

now = datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
event: dict = {}
if args.event_json and Path(args.event_json).exists():
    event = json.loads(Path(args.event_json).read_text(encoding="utf-8"))

if args.capability_token:
    tp = Path(args.capability_token)
    token = json.loads(tp.read_text(encoding="utf-8")) if tp.is_file() else {}
    if not verify(token, args.action):
        print(json.dumps({"provider": "telegram", "status": "failed", "reason": "capability_denied"}, ensure_ascii=False))
        raise SystemExit(1)


def _payload_text(run_dir: Path, ev: dict) -> str:
    pp = ev.get("payload_path")
    if not pp:
        return ""
    p = Path(pp) if Path(pp).is_absolute() else run_dir / str(pp)
    if not p.is_file():
        return f"<missing:{pp}>"
    if ev.get("type") == "send_file":
        try:
            sz = p.stat().st_size
        except OSError:
            sz = -1
        return f"[file:{pp} bytes={sz}]"
    return p.read_text(encoding="utf-8", errors="replace")


def _real_send() -> dict | None:
    base = os.environ.get("TELEGRAM_API_BASE", "").strip().rstrip("/")
    bot = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    chat = os.environ.get("TELEGRAM_CHAT_ID", "").strip()
    if not (base and bot and chat):
        return None
    rd = Path(args.run_dir or ".")
    text = _payload_text(rd, event)
    url = f"{base}/bot{bot}/sendMessage"
    body = json.dumps({"chat_id": chat, "text": text[:4090]}, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=45) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="replace") if e.fp else str(e)
        raise RuntimeError(f"telegram_http_error:{e.code}:{detail}") from e
    data = json.loads(raw) if raw else {}
    mid = (data.get("result") or {}).get("message_id")
    return {
        "provider": "telegram",
        "event_id": args.event_id or event.get("event_id"),
        "status": "sent",
        "stub_delivery": False,
        "real_external_delivery": True,
        "provider_message_id": str(mid) if mid is not None else "",
        "acked_at": now,
    }


try:
    real = _real_send()
    if real is not None:
        print(json.dumps(real, ensure_ascii=False))
    else:
        print(
            json.dumps(
                {
                    "provider": "telegram",
                    "event_id": args.event_id or event.get("event_id"),
                    "status": "sent",
                    "stub_delivery": True,
                    "real_external_delivery": False,
                    "acked_at": now,
                },
                ensure_ascii=False,
            )
        )
except Exception as exc:
    print(json.dumps({"provider": "telegram", "status": "failed", "reason": str(exc)}, ensure_ascii=False))
    raise SystemExit(1) from exc
