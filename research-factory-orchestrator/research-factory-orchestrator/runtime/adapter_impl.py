"""Interface adapter: enqueue run from chat/command context."""
from __future__ import annotations

import json
import os
from pathlib import Path

from runtime.render import allocate
from runtime.util import jl, jr, jw, now, sid


def _opt(value: str | None) -> str | None:
    if value is None:
        return None
    s = str(value).strip()
    return s or None


def cmd_adapter(a):
    task = (a.task or a.reply_text or "").strip()
    if not task:
        raise SystemExit("task is required; adapter could not extract topic from command/reply context")
    pre = (os.environ.get("RFO_PREALLOCATED_RUN_DIR") or "").strip()
    if pre:
        rd = Path(pre).resolve()
        runs_root = Path(a.runs_root).resolve()
        allowed_root = (runs_root / "runs").resolve()
        try:
            rd.relative_to(allowed_root)
        except ValueError as exc:
            raise SystemExit(
                "RFO_PREALLOCATED_RUN_DIR must resolve under <runs-root>/runs "
                f"(got {rd} vs allowed {allowed_root})"
            ) from exc
        if not rd.is_dir():
            raise SystemExit(f"RFO_PREALLOCATED_RUN_DIR is not a directory: {rd}")
        entry_path = rd / "run-catalog-entry.json"
        if not entry_path.is_file():
            raise SystemExit(f"preallocated run_dir missing run-catalog-entry.json: {entry_path}")
        c = jr(entry_path, {})
        if not c.get("run_id") or not c.get("job_id"):
            raise SystemExit("run-catalog-entry.json missing run_id/job_id for preallocated run_dir")
        if str(c.get("run_dir") or "").rstrip("/") != str(rd).rstrip("/"):
            c = {**c, "run_dir": str(rd)}
    else:
        c = allocate(a.runs_root, task, a.provider, a.interface)
        rd = Path(c["run_dir"])
    req_id = sid("REQ", a.interface, a.provider, a.conversation_id, a.message_id, task)
    # Optional delivery routing hints from the invoking host (not used for outbound sends from this repo).
    delivery = {
        "chat_id": _opt(getattr(a, "chat_id", "")),
        "reply_to_message_id": _opt(getattr(a, "reply_to_message_id", "")),
        "api_base": _opt(getattr(a, "api_base", "")),
        "source": "interface_request_argv",
    }
    jw(
        rd / "interface/interface-request.json",
        {
            "request_id": req_id,
            **c,
            "conversation_id": a.conversation_id,
            "message_id": a.message_id,
            "reply_text_available": bool(a.reply_text),
            "delivery": delivery,
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
            "delivery": delivery,
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
