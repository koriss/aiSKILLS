#!/usr/bin/env python3
"""Inert webhook delivery adapter (v19.3+). External HTTP delivery removed from skill; gateway owns channel send."""
from __future__ import annotations

import argparse
import datetime
import json
import sys
from pathlib import Path

ap = argparse.ArgumentParser()
ap.add_argument("--run-dir", required=False)
ap.add_argument("--event-id", required=False)
ap.add_argument("--event-json", required=False)
ap.add_argument("--capability-token", required=False)
ap.add_argument("--action", required=False, default="deliver_external:webhook")
args = ap.parse_args()

now = (
    datetime.datetime.now(datetime.timezone.utc)
    .replace(microsecond=0)
    .isoformat()
    .replace("+00:00", "Z")
)
event = {}
if args.event_json and Path(args.event_json).exists():
    event = json.loads(Path(args.event_json).read_text(encoding="utf-8"))

print(
    json.dumps(
        {
            "provider": "webhook",
            "event_id": args.event_id or event.get("event_id"),
            "status": "inert",
            "stub_delivery": True,
            "real_external_delivery": False,
            "note": "v19.3: webhook adapter is inert; use gateway-side delivery for external channels.",
            "acked_at": now,
        },
        ensure_ascii=False,
    )
)
sys.exit(0)
