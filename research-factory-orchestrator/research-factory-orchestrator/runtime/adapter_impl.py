"""Interface adapter: enqueue run from chat/command context."""
from __future__ import annotations

import json
from pathlib import Path

from runtime.render import allocate
from runtime.util import jl, jw, now, sid


def cmd_adapter(a):
    task = (a.task or a.reply_text or "").strip()
    if not task:
        raise SystemExit("task is required; adapter could not extract topic from command/reply context")
    c = allocate(a.runs_root, task, a.provider, a.interface)
    rd = Path(c["run_dir"])
    req_id = sid("REQ", a.interface, a.provider, a.conversation_id, a.message_id, task)
    jw(
        rd / "interface/interface-request.json",
        {
            "request_id": req_id,
            **c,
            "conversation_id": a.conversation_id,
            "message_id": a.message_id,
            "reply_text_available": bool(a.reply_text),
            "delivery_constraints": {"mobile_safe": True, "no_tables": True, "max_message_chars": 3500, "attachments_allowed": True},
            "received_at": now(),
        },
    )
    jw(
        rd / "interface/normalized-command.json",
        {
            "normalized_command_id": c["command_id"],
            **c,
            "request_id": req_id,
            "command": "/research_factory_orchestrator",
            "topic_extracted_from_reply": bool(a.reply_text and not a.task),
            "created_at": now(),
        },
    )
    job = {"job_id": c["job_id"], **c, "request_id": req_id, "created_from_interface": a.interface, "status": "queued", "queued_at": now()}
    jw(rd / "jobs/runtime-job.json", job)
    q = Path(a.runs_root) / "queue/pending"
    q.mkdir(parents=True, exist_ok=True)
    jw(q / (c["job_id"] + ".json"), job)
    jl(rd / "observability-events.jsonl", {"event_name": "interface.job_queued", "status": "ok", "run_id": c["run_id"], "job_id": c["job_id"], "timestamp": now()})
    print(json.dumps({"queued": True, **c}, ensure_ascii=False, indent=2))
