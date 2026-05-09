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
from runtime.report_html import (
    content_profile_for_manifest,
    ensure_canonical_full_report_html,
    sniff_html_document,
)
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
    "Primary human-readable outputs: chat/01-analysis.md (analysis + IO check), chat/02-facts.md (claims with URLs), report/full-report.html.",
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
    primary = rd / "chat/01-analysis.md"
    if primary.is_file():
        body = primary.read_text(encoding="utf-8", errors="replace")[:12000]
        lines = [
            "# Final answer (artifact)",
            "",
            f"**Task (excerpt):** {task[:2000]!r}",
            "",
            "(Derived from `chat/01-analysis.md`.)",
            "",
            body,
            "",
        ]
        (rd / "final-answer.md").write_text("\n".join(lines), encoding="utf-8")
        return
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


def _host_visible_run_dir(rd: Path) -> str | None:
    """Optional host path hint when container prefix map is configured (derivative only)."""
    host_root = (os.environ.get("RFO_HOST_WORKSPACE_ROOT") or "").strip()
    if not host_root:
        return None
    cont = (
        os.environ.get("RFO_CONTAINER_WORKSPACE_PREFIX") or "/home/node/.openclaw/workspace"
    ).strip().rstrip("/")
    rd_s = str(rd.resolve())
    if not rd_s.startswith(cont + "/") and rd_s != cont:
        return None
    suffix = rd_s[len(cont) :].lstrip("/")
    hp = Path(host_root).expanduser().resolve()
    return str(hp / suffix) if suffix else str(hp)


def _build_manifest(rd: Path, run_id: str, job_id: str, status: str, errors: list) -> dict:
    primary_path = rd / "chat/01-analysis.md"
    primary = ""
    if primary_path.is_file():
        primary = primary_path.read_text(encoding="utf-8", errors="replace")[:3500]
    elif (rd / "final-answer.md").is_file():
        primary = (rd / "final-answer.md").read_text(encoding="utf-8", errors="replace")[:3500]
    arts = []
    for path, role, media, fn, required in (
        ("chat/01-analysis.md", "analysis", "text/markdown", "01-analysis.md", True),
        ("chat/02-facts.md", "facts", "text/markdown", "02-facts.md", True),
        ("report/full-report.html", "report", "text/html", "report.html", True),
        ("package/research-package.zip", "package", "application/zip", "research-package.zip", False),
    ):
        f = rd / path
        if not f.is_file():
            if required and status == "ok":
                pass
            continue
        art: dict = {
            "path": path,
            "role": role,
            "media_type": media,
            "filename": fn,
            "size_bytes": f.stat().st_size,
            "sha256": sha(f),
            "required": required,
        }
        if path == "report/full-report.html":
            head = f.read_bytes()[:8192].decode("utf-8", errors="replace")
            sniff = sniff_html_document(head)
            art["report_html_sniff"] = sniff
            art["content_profile"] = content_profile_for_manifest(sniff)
        arts.append(art)
    quality = jr(rd / "report/quality-metadata.json", {})
    meta = {
        "run_id": run_id,
        "job_id": job_id,
        "skill": "research-factory-orchestrator",
        "skill_version": VERSION,
        "created_at": now(),
    }
    host_rd = _host_visible_run_dir(rd)
    if host_rd:
        meta["run_dir_host"] = host_rd
        meta["run_dir_host_disclaimer"] = (
            "Hint only when RFO_HOST_WORKSPACE_ROOT matches actual bind mount; "
            "canonical path is container run_dir / marker.run_dir."
        )

    out: dict = {
        "schema_version": "v1",
        "contract": RESULT_MANIFEST_CONTRACT,
        "status": status,
        "primary_format": "markdown",
        "artifacts": arts,
        "errors": errors,
        "metadata": meta,
    }
    if isinstance(quality, dict) and quality:
        out["quality"] = quality
    if primary.strip():
        out["primary_text"] = primary
    return out


def _write_result_json(rd: Path, manifest: dict) -> None:
    jw(
        rd / "result.json",
        {
            "schema_version": "v1",
            "contract": "rfo-result-json-v1",
            "status": manifest.get("status"),
            "deliverables": [
                {"path": a.get("path"), "role": a.get("role"), "media_type": a.get("media_type")}
                for a in manifest.get("artifacts", [])
                if isinstance(a, dict)
            ],
            "quality": manifest.get("quality") if isinstance(manifest.get("quality"), dict) else {},
        },
    )


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
    if not (rd / "chat/01-analysis.md").is_file():
        _write_final_answer(rd, task)
    run_json = jr(rd / "run.json", {})
    run_id = str(run_json.get("run_id") or rd.name)
    job_id = str(run_json.get("job_id") or "UNKNOWN")
    resolved = status
    if resolved is None:
        resolved = "ok"
        for p in ("report/full-report.html", "chat/01-analysis.md", "chat/02-facts.md"):
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
    if resolved == "ok":
        ok_rep, rep_note = ensure_canonical_full_report_html(rd)
        if not ok_rep:
            resolved = "partial"
            errs.append(
                {
                    "code": "report_html_ensure_failed",
                    "message": rep_note,
                    "where": "emit_agent_skill_handoff.ensure_canonical_full_report_html",
                },
            )
    req_triple = ("report/full-report.html", "chat/01-analysis.md", "chat/02-facts.md")
    missing_after = [p for p in req_triple if not (rd / p).is_file()]
    seen_missing_msgs = {
        e.get("message")
        for e in errs
        if isinstance(e, dict)
        and e.get("code") == "missing_required_artifact"
        and e.get("message")
    }
    if missing_after:
        resolved = "failed"
        for p in missing_after:
            if p in seen_missing_msgs:
                continue
            seen_missing_msgs.add(p)
            errs.append(
                {
                    "code": "missing_required_artifact",
                    "message": p,
                    "where": "emit_agent_skill_handoff.post_ensure",
                },
            )

    manifest = _build_manifest(rd, run_id, job_id, resolved, errs)
    jw(rd / "result-manifest.json", manifest)
    _write_result_json(rd, manifest)
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
    host_vis = _host_visible_run_dir(rd)
    if host_vis:
        payload["run_dir_host"] = host_vis
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
        req_paths = ("report/full-report.html", "chat/01-analysis.md", "chat/02-facts.md")
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
    _write_result_json(rd, manifest)
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
