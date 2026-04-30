#!/usr/bin/env python3
from pathlib import Path
import argparse, json, sys

REQUIRED = [
    "run.json",
    "artifact-manifest.json",
    "provenance-manifest.json",
    "validation-transcript.json",
    "ledgers/search-ledger.json",
    "subagent-ledger.json",
    "delivery-manifest.json"
]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run_dir")
    args = ap.parse_args()
    root = Path(args.run_dir)
    missing = [p for p in REQUIRED if not (root / p).exists()]
    if missing:
        print(json.dumps({
            "confirmed": False,
            "missing_artifacts": missing,
            "text": "Не могу подтвердить pipeline: отсутствуют обязательные ledgers/manifests."
        }, ensure_ascii=False, indent=2))
        return 1
    run = json.loads((root / "run.json").read_text(encoding="utf-8"))
    search = json.loads((root / "ledgers" / "search-ledger.json").read_text(encoding="utf-8"))
    sub = json.loads((root / "subagent-ledger.json").read_text(encoding="utf-8"))
    delivery = json.loads((root / "delivery-manifest.json").read_text(encoding="utf-8"))
    text = [
        f"Pipeline подтверждён артефактами для run_id={run.get('run_id')}.",
        f"Статус run: {run.get('status')}.",
        f"Поисков в search-ledger: {len(search.get('searches', []))}.",
        f"Сабагенты: total={sub.get('subagents_total')}, completed={sub.get('subagents_completed')}, failed={sub.get('subagents_failed')}, quorum_met={sub.get('quorum_met')}.",
        f"Delivery status: {delivery.get('delivery_status')}."
    ]
    print(json.dumps({"confirmed": True, "generated_from_artifacts": REQUIRED, "text": "\n".join(text)}, ensure_ascii=False, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
