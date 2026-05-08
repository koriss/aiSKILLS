"""Synchronous artifact-only execute path (RFO v19.3 compute-only)."""
from __future__ import annotations

import contextlib
import json
import os
import sys
from pathlib import Path
from types import SimpleNamespace

from runtime.profiles import resolve as _resolve_profile
from runtime.render import allocate
from runtime.status import VERSION
from runtime.schema_defaults import minimal_valid
from runtime.util import jw, jr, now, sha, sid
from runtime.worker_impl import build_package, cmd_run

# Neutral stdout capsule for whoever invoked the skill (LLM gateway, cron, Telegram bridge, …).
HANDOFF_STDOUT_PREFIX = "__RFO_SKILL_AGENT_HANDOFF__="
# Declares result-manifest semantics; invoking host parses stdout + reads artifacts under run_dir.
RESULT_MANIFEST_CONTRACT = "rfo-skill-agent-handoff-v1"

DEFAULT_INSTRUCTIONS_FOR_INVOKING_AGENT = [
    "This process is compute-only: it writes artifacts under run_dir and does not open chat sessions or outbound channels.",
    "Present the substantive answer using final-answer.md or report/full-report.html (and analytical-memo if present).",
    "If your environment can attach files for the human, attach paths listed under result-manifest.json.artifacts;",
    "only claim artifacts were handed off after your layer actually exposes them.",
]


def _seed_interface_and_job(rd: Path, c: dict, task: str) -> None:
    req_id = sid("REQ", "artifact_execute", "cli", "", "", task)
    delivery = {"mode": "agent_handoff_only", "source": "artifact_execute_compute_only"}
    jw(
        rd / "interface/interface-request.json",
        {
            "request_id": req_id,
            **c,
            "conversation_id": "",
            "message_id": "",
            "reply_text_available": False,
            "delivery": delivery,
            "delivery_constraints": {
                "mobile_safe": True,
                "no_tables": True,
                "max_message_chars": 3500,
                "attachments_allowed": True,
            },
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
            "topic_extracted_from_reply": False,
            "delivery": delivery,
            "created_at": now(),
        },
    )
    job = {
        "job_id": c["job_id"],
        **c,
        "request_id": req_id,
        "created_from_interface": "artifact_execute",
        "status": "execute_inline",
        "queued_at": now(),
    }
    jw(rd / "jobs/runtime-job.json", job)


def _write_final_answer(rd: Path, task: str) -> None:
    memo = jr(rd / "report/analytical-memo.json", {})
    summary = str(memo.get("executive_summary") or "").strip()
    lines = [
        "# Final answer (artifact)",
        "",
        f"**Task (excerpt):** {task[:2000]!r}",
        "",
        "## Executive summary",
        "",
        summary or "(no executive_summary in analytical-memo.json)",
        "",
        "---",
        "",
        "Full HTML report and optional research package are separate artifacts per `result-manifest.json`.",
        "",
    ]
    (rd / "final-answer.md").write_text("\n".join(lines), encoding="utf-8")


def _build_manifest(rd: Path, run_id: str, job_id: str, status: str, errors: list) -> dict:
    primary = ""
    if (rd / "final-answer.md").is_file():
        primary = (rd / "final-answer.md").read_text(encoding="utf-8", errors="replace")[:3500]
    arts = []
    for path, role, media, fn, required in (
        ("final-answer.md", "answer", "text/markdown", "final-answer.md", True),
        ("report/full-report.html", "report", "text/html", "report.html", True),
        ("package/research-package.zip", "package", "application/zip", "research-package.zip", False),
    ):
        f = rd / path
        if not f.is_file():
            if required and status == "ok":
                # partial: missing required artifact
                pass
            continue
        arts.append(
            {
                "path": path,
                "role": role,
                "media_type": media,
                "filename": fn,
                "size_bytes": f.stat().st_size,
                "sha256": sha(f),
                "required": required,
            }
        )
    out: dict = {
        "schema_version": "v1",
        "contract": RESULT_MANIFEST_CONTRACT,
        "status": status,
        "primary_format": "markdown",
        "artifacts": arts,
        "errors": errors,
        "metadata": {
            "run_id": run_id,
            "job_id": job_id,
            "skill": "research-factory-orchestrator",
            "skill_version": VERSION,
            "created_at": now(),
        },
    }
    if primary.strip():
        out["primary_text"] = primary
    return out


def _normalize_exit(status: str) -> int:
    return {"ok": 0, "partial": 10, "failed": 20}.get(status, 20)


def emit_agent_skill_handoff(
    rd: Path,
    task: str,
    *,
    status: str | None = None,
    errors: list | None = None,
) -> tuple[str, int]:
    """Persist ``result-manifest.json``, ``marker.json``, and emit the agent handoff line on stdout.

    The invoking agent/gateway parses the single stdout line prefixed with ``HANDOFF_STDOUT_PREFIX``.
    """
    rd = Path(rd).resolve()
    errs = list(errors) if errors else []
    if not (rd / "final-answer.md").is_file():
        _write_final_answer(rd, task)
    run_json = jr(rd / "run.json", {})
    run_id = str(run_json.get("run_id") or rd.name)
    job_id = str(run_json.get("job_id") or "UNKNOWN")
    resolved = status
    if resolved is None:
        resolved = "ok"
        for p in ("report/full-report.html", "final-answer.md"):
            if not (rd / p).is_file():
                resolved = "failed"
                errs.append(
                    {
                        "code": "missing_required_artifact",
                        "message": p,
                        "where": "emit_agent_skill_handoff.verify",
                    },
                )
                break
    manifest = _build_manifest(rd, run_id, job_id, resolved, errs)
    jw(rd / "result-manifest.json", manifest)
    payload = {
        "skill": "research-factory-orchestrator",
        "skill_version": VERSION,
        "run_id": run_id,
        "run_dir": str(rd),
        "manifest": "result-manifest.json",
        "contract": RESULT_MANIFEST_CONTRACT,
        "status": resolved,
        "computes_only": True,
        "instructions_for_invoking_agent": list(DEFAULT_INSTRUCTIONS_FOR_INVOKING_AGENT),
        "task_excerpt": (task[:500] + ("…" if len(task) > 500 else "")),
    }
    jw(rd / "marker.json", payload)
    print(HANDOFF_STDOUT_PREFIX + json.dumps(payload, ensure_ascii=False), flush=True)
    return resolved, _normalize_exit(resolved)


def cmd_execute(a) -> int:
    runs_root = Path(a.runs_root).resolve()
    task = (a.task or "").strip()
    if not task:
        sys.stderr.write("execute: --task required\n")
        return 2
    profile_opt = (getattr(a, "profile", None) or "").strip()
    seeds_opt = (getattr(a, "seed_urls", None) or "").strip()
    if profile_opt:
        low = profile_opt.lower()
        os.environ["RFO_RUN_PROFILE"] = low
        try:
            _name, policy = _resolve_profile(low)
            src_pol = policy.get("source_policy") or {}
            if bool(src_pol.get("external_collection_required")):
                os.environ["RFO_EXTERNAL_COLLECTION"] = "required"
        except ValueError:
            pass
    if seeds_opt:
        os.environ["RFO_SEED_URLS"] = seeds_opt
    c = allocate(str(runs_root), task, "cli", "artifact_execute")
    rd = Path(c["run_dir"]).resolve()
    runs_root_str = str(runs_root)
    _seed_interface_and_job(rd, c, task)
    ns = SimpleNamespace(
        project_dir=str(rd),
        task=task,
        run_id=c["run_id"],
        job_id=c["job_id"],
        command_id=c["command_id"],
        mode=getattr(a, "mode", None) or "research",
        provider="cli",
        interface="artifact_execute",
        runs_root=runs_root_str,
    )
    status = "ok"
    errors: list = []
    try:
        with contextlib.redirect_stdout(sys.stderr):
            cmd_run(ns)
            build_package(rd, allow_stub=True)
        _write_final_answer(rd, task)
        jw(
            rd / "final-answer-gate.json",
            minimal_valid(
                "final-answer-gate",
                overrides={
                    "run_id": c["run_id"],
                    "passed": True,
                    "status": "pass",
                },
            ),
        )
    except SystemExit as se:
        code = se.code
        ec = int(code) if isinstance(code, int) else 20
        status = "partial" if ec == 10 else "failed"
        errors.append({"code": "system_exit", "message": str(se), "where": "artifact_execute.pipeline"})
    except Exception as exc:
        status = "failed"
        errors.append({"code": "execute_exception", "message": repr(exc), "where": "artifact_execute.pipeline"})

    if not (rd / "final-answer.md").is_file():
        (rd / "final-answer.md").write_text(
            "# Execute incomplete or failed\n\nSee `result-manifest.json` errors and stderr.\n",
            encoding="utf-8",
        )
    if status == "ok":
        req_paths = ("report/full-report.html", "final-answer.md")
        miss = [p for p in req_paths if not (rd / p).is_file()]
        if miss:
            status = "failed"
            errors.append(
                {
                    "code": "missing_required_artifact",
                    "message": ", ".join(miss),
                    "where": "artifact_execute.verify",
                }
            )

    manifest = _build_manifest(rd, c["run_id"], c["job_id"], status, errors)
    jw(rd / "result-manifest.json", manifest)
    payload = {
        "skill": "research-factory-orchestrator",
        "skill_version": VERSION,
        "run_id": c["run_id"],
        "run_dir": str(rd),
        "manifest": "result-manifest.json",
        "contract": RESULT_MANIFEST_CONTRACT,
        "status": status,
        "computes_only": True,
        "instructions_for_invoking_agent": list(DEFAULT_INSTRUCTIONS_FOR_INVOKING_AGENT),
        "task_excerpt": (task[:500] + ("…" if len(task) > 500 else "")),
    }
    jw(rd / "marker.json", payload)
    print(HANDOFF_STDOUT_PREFIX + json.dumps(payload, ensure_ascii=False), flush=True)
    return _normalize_exit(status)
