#!/usr/bin/env python3
"""P3/P4: outbox idempotency scaffold.

This validator is intentionally conservative: it only checks for duplicate
idempotency keys and duplicate event IDs in the current outbox directory.
Deep replay verification (same payload digest across retries, retry windows,
provider ACK correlation) is planned as a follow-up.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("run_dir", type=Path)
    args = ap.parse_args()
    outbox = args.run_dir / "outbox"
    if not outbox.is_dir():
        print(
            json.dumps(
                {
                    "status": "pass",
                    "validator": "validate_idempotent_outbox",
                    "note": "no outbox directory",
                },
                ensure_ascii=False,
            )
        )
        return 0

    keys: dict[str, list[str]] = {}
    ids: dict[str, list[str]] = {}
    for jf in sorted(outbox.glob("OUT-*.json")):
        try:
            row = json.loads(jf.read_text(encoding="utf-8"))
        except Exception:
            continue
        event_id = str(row.get("event_id") or jf.stem)
        idem = str(row.get("idempotency_key") or "")
        ids.setdefault(event_id, []).append(jf.name)
        if idem:
            keys.setdefault(idem, []).append(jf.name)

    dup_ids = {k: v for k, v in ids.items() if len(v) > 1}
    dup_keys = {k: v for k, v in keys.items() if len(v) > 1}
    proc = args.run_dir / "delivery-acks" / "processed_events.json"
    ack_dir = args.run_dir / "delivery-acks"
    ack_files = sorted(ack_dir.glob("OUT-*.json")) if ack_dir.is_dir() else []
    proc_ok = True
    proc_note = ""
    if ack_files and not proc.is_file():
        proc_ok, proc_note = False, "missing delivery-acks/processed_events.json while acks exist"
    elif proc.is_file():
        try:
            pe = json.loads(proc.read_text(encoding="utf-8"))
            seen = {e.get("event_id") for e in pe.get("events", []) if isinstance(e, dict)}
            for jf in sorted(outbox.glob("OUT-*.json")):
                row = json.loads(jf.read_text(encoding="utf-8"))
                eid = str(row.get("event_id") or jf.stem)
                ackp = args.run_dir / "delivery-acks" / f"{eid}.json"
                if ackp.exists() and eid not in seen:
                    proc_ok = False
                    proc_note = f"missing processed_events entry for acked {eid}"
                    break
        except Exception as exc:
            proc_ok = False
            proc_note = str(exc)
    if dup_ids or dup_keys or not proc_ok:
        print(
            json.dumps(
                {
                    "status": "fail",
                    "validator": "validate_idempotent_outbox",
                    "duplicate_event_ids": dup_ids,
                    "duplicate_idempotency_keys": dup_keys,
                    "processed_events_ok": proc_ok,
                    "processed_events_note": proc_note,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 1

    print(
        json.dumps(
            {
                "status": "pass",
                "validator": "validate_idempotent_outbox",
                "note": "basic idempotency uniqueness check passed",
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
