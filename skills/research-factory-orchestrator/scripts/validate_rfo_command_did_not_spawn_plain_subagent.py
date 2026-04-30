#!/usr/bin/env python3
from pathlib import Path
import argparse, json, re

RFO = re.compile(r"/research_factory_orchestrator|Research Factory Orchestrator|RFO", re.I)
BAD = [
    (re.compile(r"Spawnю\s+subagent|spawn(?:ed)?\s+subagent|субагент выполняет", re.I), "RFO routed to plain/spawned subagent"),
    (re.compile(r"deep-investigation-agent", re.I), "RFO routed/fell back to deep-investigation-agent"),
    (re.compile(r"читаю\s+.*SKILL\.md|прочитал.*SKILL\.md", re.I), "SKILL.md reading used as runtime substitute"),
    (re.compile(r"убиваю.*запускаю заново через deep-investigation-agent", re.I), "wrong restart route through deep-investigation-agent"),
]
GOOD_ENTRY = re.compile(r"interface_runtime_adapter\.py|runtime_job_worker\.py|outbox_delivery_worker\.py|run_research_factory\.py", re.I)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("path"); args=ap.parse_args()
    p=Path(args.path); errors=[]
    text=p.read_text(encoding="utf-8", errors="replace") if p.exists() else str(args.path)
    if RFO.search(text):
        if not GOOD_ENTRY.search(text):
            errors.append("RFO command/log has no approved runtime entrypoint evidence")
        for rx, msg in BAD:
            if rx.search(text):
                errors.append(msg)
    print(json.dumps({"status":"pass" if not errors else "fail","errors":errors}, ensure_ascii=False, indent=2))
    return 0 if not errors else 1
if __name__=="__main__":
    raise SystemExit(main())
