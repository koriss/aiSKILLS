"""LLM-backed research plan → ``research/research-plan.json`` with schema gate + fallback."""
from __future__ import annotations

import hashlib
import json
import os
import re
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from runtime.research_plan_validate import validate_plan_document
from runtime.util import now, skill_root


def default_safety_caps() -> dict[str, int]:
    return {
        "max_waves": int(os.environ.get("RFO_RESEARCH_PLAN_MAX_WAVES", "32")),
        "max_queries_per_wave": int(os.environ.get("RFO_RESEARCH_PLAN_MAX_Q_PER_WAVE", "24")),
        "max_total_relay": int(os.environ.get("RFO_RESEARCH_PLAN_MAX_TOTAL_RELAY", "120")),
    }


def _schema_text() -> str:
    p = skill_root() / "contracts" / "research-plan-v1.schema.json"
    return p.read_text(encoding="utf-8")


def _extract_json_object(raw: str) -> dict[str, Any] | None:
    text = (raw or "").strip()
    if not text:
        return None
    try:
        o = json.loads(text)
        return o if isinstance(o, dict) else None
    except json.JSONDecodeError:
        pass
    m = re.search(r"\{[\s\S]*\}\s*$", text)
    if m:
        try:
            o = json.loads(m.group(0))
            return o if isinstance(o, dict) else None
        except json.JSONDecodeError:
            return None
    return None


def _call_openai_compat_planner(task: str, user_extra: str) -> tuple[dict[str, Any] | None, str]:
    base = (os.environ.get("RFO_RESEARCH_PLANNER_BASE_URL") or "").strip().rstrip("/")
    key = (os.environ.get("RFO_RESEARCH_PLANNER_API_KEY") or "").strip()
    model = (os.environ.get("RFO_RESEARCH_PLANNER_MODEL") or "gpt-4o-mini").strip()
    if not base or not key:
        return None, "planner_unconfigured"
    url = f"{base}/chat/completions"
    schema_snip = _schema_text()[:14000]
    sys_msg = (
        "You are a research planner. Output a single JSON object only (no markdown fences). "
        "The object MUST include schema_version \"research-plan-v1\", metadata, axes, waves, safety. "
        "Waves run sequentially; each wave has a non-empty queries array. "
        "Do not include API keys or instructions to execute code — only search query strings."
    )
    user_msg = f"Task:\n{task}\n\nJSON Schema (excerpt):\n{schema_snip}\n\n{user_extra}".strip()
    body: dict[str, Any] = {
        "model": model,
        "messages": [
            {"role": "system", "content": sys_msg},
            {"role": "user", "content": user_msg},
        ],
        "temperature": float(os.environ.get("RFO_RESEARCH_PLANNER_TEMPERATURE", "0.2") or "0.2"),
    }
    if os.environ.get("RFO_RESEARCH_PLANNER_JSON_OBJECT", "1").strip().lower() not in ("0", "false", "no"):
        body["response_format"] = {"type": "json_object"}
    data = json.dumps(body, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {key}",
        },
        method="POST",
    )
    timeout = float(os.environ.get("RFO_RESEARCH_PLANNER_HTTP_TIMEOUT", "120") or "120")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            payload = json.loads(resp.read().decode("utf-8", errors="replace"))
    except urllib.error.HTTPError as e:
        try:
            detail = e.read().decode("utf-8", errors="replace")[:800]
        except Exception:
            detail = str(e)
        return None, f"http_error:{e.code}:{detail}"
    except Exception as e:
        return None, f"request_failed:{e}"
    try:
        choice0 = (payload.get("choices") or [{}])[0]
        msg = choice0.get("message") or {}
        content = str(msg.get("content") or "").strip()
    except Exception:
        return None, "bad_response_shape"
    doc = _extract_json_object(content)
    if not doc:
        return None, "empty_or_non_json_content"
    return doc, ""


def build_fallback_plan(task: str, *, reason: str, vectors: list[str] | None = None) -> dict[str, Any]:
    from rfo_query_fanout import build_query_vectors  # noqa: WPS433 — scripts dir on sys.path in bridge/worker

    caps = default_safety_caps()
    qs = list(vectors or build_query_vectors(task))
    return {
        "schema_version": "research-plan-v1",
        "metadata": {
            "task": task,
            "plan_version": 1,
            "created_at": now(),
            "mode": "fallback",
            "fallback_reason": reason,
        },
        "axes": [
            {
                "id": "axis-fallback",
                "title": "Template vectors",
                "intent": "Deterministic queries after planner failure or missing provider",
                "priority": 1,
            }
        ],
        "waves": [
            {
                "wave_id": "W0",
                "axis_id": "axis-fallback",
                "purpose": "build_query_vectors / template fanout",
                "queries": qs[: caps["max_queries_per_wave"]],
            }
        ],
        "safety": caps,
        "extensions": {},
        "evidence_policy": None,
        "stop_when": None,
    }


def _enforce_safety_on_plan(doc: dict[str, Any]) -> dict[str, Any]:
    caps = default_safety_caps()
    safety = doc.get("safety")
    if not isinstance(safety, dict):
        safety = {}
    merged = {
        "max_waves": min(int(safety.get("max_waves", caps["max_waves"])), caps["max_waves"]),
        "max_queries_per_wave": min(int(safety.get("max_queries_per_wave", caps["max_queries_per_wave"])), caps["max_queries_per_wave"]),
        "max_total_relay": min(int(safety.get("max_total_relay", caps["max_total_relay"])), caps["max_total_relay"]),
    }
    doc = dict(doc)
    doc["safety"] = merged
    waves_in = doc.get("waves") if isinstance(doc.get("waves"), list) else []
    waves_out: list[dict[str, Any]] = []
    for i, w in enumerate(waves_in[: merged["max_waves"]]):
        if not isinstance(w, dict):
            continue
        w2 = dict(w)
        qraw = w2.get("queries") if isinstance(w2.get("queries"), list) else []
        qclean = [str(q).strip() for q in qraw if str(q).strip()][: merged["max_queries_per_wave"]]
        w2["queries"] = qclean
        if qclean:
            waves_out.append(w2)
    doc["waves"] = waves_out
    return doc


def _atomic_write_plan(rd: Path, doc: dict[str, Any]) -> None:
    rd = Path(rd)
    research = rd / "research"
    research.mkdir(parents=True, exist_ok=True)
    tmp = research / ".research-plan.json.tmp"
    final = research / "research-plan.json"
    tmp.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(final)


def plan_and_write(rd: Path, task: str) -> dict[str, Any]:
    """
    Produce ``research/research-plan.json`` under ``rd``.

    One LLM attempt + optional repair retry on schema errors, then fallback to
    ``build_query_vectors``-style plan.
    """
    rd = Path(rd)
    schema_errors: list[str] = []
    err: str = ""

    doc, err = _call_openai_compat_planner(task, "")
    if doc:
        errs = validate_plan_document(doc)
        if not errs:
            doc_ok = _enforce_safety_on_plan(_doc_with_hashes(doc, task))
            _atomic_write_plan(rd, doc_ok)
            return {
                "ok": True,
                "path": str(rd / "research" / "research-plan.json"),
                "used_fallback": False,
                "repair_attempted": False,
                "schema_errors_before_repair": [],
                "planner_error": "",
            }
        schema_errors = [f"{c}:{m}" for c, m in errs]
        repair_hint = "Fix JSON to satisfy research-plan-v1. Issues:\n" + "\n".join(schema_errors[:40])
        doc2, err2 = _call_openai_compat_planner(task, repair_hint)
        if doc2:
            errs2 = validate_plan_document(doc2)
            if not errs2:
                doc_ok = _enforce_safety_on_plan(_doc_with_hashes(doc2, task))
                _atomic_write_plan(rd, doc_ok)
                return {
                    "ok": True,
                    "path": str(rd / "research" / "research-plan.json"),
                    "used_fallback": False,
                    "repair_attempted": True,
                    "schema_errors_before_repair": schema_errors,
                    "planner_error": "",
                }
        err = err2 or err or "repair_failed"

    fb = build_fallback_plan(task, reason=f"planner:{err or 'schema'}:{';'.join(schema_errors[:3])}")
    fb = _enforce_safety_on_plan(fb)
    _atomic_write_plan(rd, fb)
    return {
        "ok": True,
        "path": str(rd / "research" / "research-plan.json"),
        "used_fallback": True,
        "repair_attempted": bool(schema_errors),
        "schema_errors_before_repair": schema_errors,
        "planner_error": err,
    }


def _doc_with_hashes(doc: dict[str, Any], task: str) -> dict[str, Any]:
    doc = dict(doc)
    meta = dict(doc["metadata"]) if isinstance(doc.get("metadata"), dict) else {}
    raw = json.dumps(doc, ensure_ascii=False, sort_keys=True).encode("utf-8")
    meta["plan_sha256_preview"] = hashlib.sha256(raw).hexdigest()[:16]
    meta.setdefault("task", task)
    meta.setdefault("created_at", now())
    doc["metadata"] = meta
    return _enforce_safety_on_plan(doc)


def flatten_plan_queries(plan: dict[str, Any]) -> list[str]:
    """Ordered de-duplicated queries capped by ``safety.max_total_relay``."""
    safety = plan.get("safety") if isinstance(plan.get("safety"), dict) else {}
    cap = int(safety.get("max_total_relay") or default_safety_caps()["max_total_relay"])
    seen: set[str] = set()
    out: list[str] = []
    for w in plan.get("waves") or []:
        if not isinstance(w, dict):
            continue
        for q in w.get("queries") or []:
            s = str(q).strip()
            if not s or s in seen:
                continue
            seen.add(s)
            out.append(s)
            if len(out) >= cap:
                return out
    return out


def materialize_wave_plan(rd: Path, run_id: str, plan: dict[str, Any], *, relay_note: str) -> None:
    """Write ``graph/wave-plan.json`` aligned with plan waves (completed stubs for gate)."""
    from runtime.util import jw

    waves_out: list[dict[str, Any]] = []
    for i, w in enumerate(plan.get("waves") or []):
        if not isinstance(w, dict):
            continue
        wid = str(w.get("wave_id") or f"W{i}")
        purpose = str(w.get("purpose") or "planned wave")
        nq = len(w.get("queries") or []) if isinstance(w.get("queries"), list) else 0
        waves_out.append({
            "wave_id": wid,
            "status": "completed",
            "purpose": f"{purpose} ({nq} queries) | {relay_note}",
        })
    if not waves_out:
        waves_out = [
            {"wave_id": "W0", "status": "completed", "purpose": relay_note or "relay prefetch"},
        ]
    jw(rd / "graph" / "wave-plan.json", {"run_id": run_id, "waves": waves_out})
