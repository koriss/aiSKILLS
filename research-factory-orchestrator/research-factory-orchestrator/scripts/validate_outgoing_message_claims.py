#!/usr/bin/env python3
"""Pre-send guard: chat vs delivery manifest; tool hallucination classes (Relign / RelyToolBench)."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

DELIVERED = re.compile(
    r"(отправлен|доставлен|sent to Telegram|HTML-отч[её]т.*отправлен)",
    re.I,
)


def _scan_outbox_tool_issues(rd: Path) -> list[dict]:
    issues = []
    ob = rd / "outbox"
    if not ob.is_dir():
        return issues
    for p in sorted(ob.glob("OUT-*.json")):
        ev = json.loads(p.read_text(encoding="utf-8"))
        prov = str(ev.get("provider") or "")
        typ = str(ev.get("type") or "")
        if typ == "send_message" and prov not in ("telegram", "cli", "webhook", ""):
            issues.append({"event_id": ev.get("event_id"), "kind": "tool_selection_hallucination", "detail": "unexpected provider for send_message"})
        if typ == "send_message" and not ev.get("payload_path"):
            issues.append({"event_id": ev.get("event_id"), "kind": "tool_usage_hallucination", "detail": "missing payload_path"})
    return issues


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("run_dir", type=Path)
    args = ap.parse_args()
    rd = args.run_dir
    plan = rd / "chat" / "chat-message-plan.json"
    dm = rd / "delivery-manifest.json"
    tool_issues = _scan_outbox_tool_issues(rd)
    if tool_issues:
        print(json.dumps({"status": "fail", "reason": "tool_hallucination_signals", "issues": tool_issues}, ensure_ascii=False))
        return 1
    if not plan.exists():
        print(json.dumps({"status": "pass", "note": "no chat plan"}, ensure_ascii=False))
        return 0
    text = plan.read_text(encoding="utf-8", errors="replace")
    if not DELIVERED.search(text):
        print(json.dumps({"status": "pass", "note": "no delivery claim in plan"}, ensure_ascii=False))
        return 0
    if not dm.exists():
        print(json.dumps({"status": "fail", "reason": "delivery claimed but no manifest"}, ensure_ascii=False))
        return 1
    data = json.loads(dm.read_text(encoding="utf-8"))
    if not (data.get("publish_allowed") and data.get("delivery_claim_allowed")):
        print(json.dumps({"status": "fail", "reason": "delivery language without publish_allowed"}, ensure_ascii=False))
        return 1
    print(json.dumps({"status": "pass"}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
