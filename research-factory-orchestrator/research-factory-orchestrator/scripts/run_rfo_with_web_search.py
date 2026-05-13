#!/usr/bin/env python3
"""
RFO v19.4 — JSON relay prefetch bridge (neutral contract)

collector.py делает только HEAD‑probe семян или загрузку RFO_SOURCE_PACKET; список
URL для исследования собирается здесь через **настраиваемый** HTTP JSON relay
(типичный эндпоинт вида `/search?q=…&format=json`; хост задаёт оператор).

Обязательно задать базу через ``--web-search-json-api-base`` или
``RFO_WEB_SEARCH_JSON_API_BASE`` (значение всегда задаёт оператор).

Runs root (workspace-first): ``OPENCLAW_WORKSPACE_DIR`` / ``--workspace-root`` →
``<workspace>/rfo-runs``, либо явный ``--runs-root`` / ``RFO_RUNS_ROOT`` (deprecated),
иначе portable цепочка (см. ``runtime/config_resolution.py`` и
``docs/adr/ADR-RFO_PORTABLE.md``).

Опционально: ``RFO_WIKIPEDIA_HEURISTIC=1`` — считать URL с ``wikipedia.org`` сырым
документом (иначе эвристика выключена).

Поток:
  1. **Ранний ``run_dir``:** ``allocate`` + bootstrap ``research/`` / ``graph/`` (см. ``runtime/research_bridge_bootstrap``), затем план ``research/research-plan.json`` (``RFO_RESEARCH_PLAN_MODE``).
  2. **Последовательное** расширение запросов к JSON relay → merge/dedup URL → **последовательный** fetch страниц (шаблоны или плоский список из плана при ``llm_v1``).
  3. ``RFO_SOURCE_PACKET`` + очередь RFO как обычно (адаптер с ``RFO_PREALLOCATED_RUN_DIR``).
  4. патчи claims-registry / re-render / stdout ``__RFO_SKILL_AGENT_HANDOFF__=``

По умолчанию профиль ``dossier`` (единый конвейер «досье»); допустимые имена —
только ключи из ``contracts/run-profiles.json``.

**Конфигурация:** резолв ``runs_root`` / relay / effective-config — только через
``runtime/config_resolution.py`` (без дублирования цепочек приоритетов в этом файле).
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import sys
import time
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import subprocess

# ── paths ────────────────────────────────────────────────────────────────────
SKILL_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = SKILL_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))
sys.path.insert(0, str(SKILL_ROOT))

from runtime.config_resolution import (  # noqa: E402
    build_effective_config_snapshot,
    log_startup_summary,
    relay_chain,
)
from runtime.status import VERSION  # noqa: E402
from runtime.util import jl, now  # noqa: E402

from rfo_query_fanout import (  # noqa: E402
    build_query_vectors,
    fanout_relay_search,
    fanout_relay_search_from_queries,
)
from rfo_relay_search_helpers import (  # noqa: E402
    body_text_signals_seed_garbage,
    rank_relay_rows_for_task,
    relay_fetch_cap,
    relay_json_search,
)
from runtime.source_record_v19 import normalize_source_record_v19  # noqa: E402

# ── config ────────────────────────────────────────────────────────────────────
_HTTP_TIMEOUT = float(os.environ.get("RFO_HTTP_TIMEOUT", "8.0"))
_USER_AGENT = (os.environ.get("RFO_WEB_SEARCH_USER_AGENT") or "").strip() or f"RFO/{VERSION}-RelayPrefetch"
_MAX_CHARS_PER_SOURCE = int(os.environ.get("RFO_MAX_CHARS_PER_SOURCE", "3000"))
_MAX_SOURCES = int(os.environ.get("RFO_MAX_SOURCES", "8"))

_ADAPTER_TIMEOUT = float(os.environ.get("RFO_BRIDGE_ADAPTER_TIMEOUT", "120"))
_WORKER_TIMEOUT = float(os.environ.get("RFO_BRIDGE_WORKER_TIMEOUT", "600"))
_WORKER_RETRY_MAX = int(os.environ.get("RFO_BRIDGE_WORKER_RETRIES", "12"))
_WORKER_RETRY_BASE_S = float(os.environ.get("RFO_BRIDGE_WORKER_BACKOFF", "0.35"))


def _ensure_rfo_tree(runs_root: Path) -> None:
    runs_root = Path(runs_root)
    (runs_root / "runs").mkdir(parents=True, exist_ok=True)
    (runs_root / "index").mkdir(parents=True, exist_ok=True)
    for sub in ("pending", "running", "done"):
        (runs_root / "queue" / sub).mkdir(parents=True, exist_ok=True)


def _parse_stdout_json_object(stdout: str) -> dict[str, Any]:
    """
    Best-effort extraction of the last JSON object from noisy stdout.

    Supports:
      - pure JSON stdout
      - single-line JSON mixed with logs
      - pretty-printed (multiline) JSON blocks mixed with logs
    """
    text = (stdout or "").strip()
    if not text:
        return {}
    try:
        obj = json.loads(text)
        return obj if isinstance(obj, dict) else {}
    except json.JSONDecodeError:
        pass
    # Fast path: line-wise tail scan.
    for line in reversed(text.splitlines()):
        line = line.strip()
        if not (line.startswith("{") and line.endswith("}")):
            continue
        try:
            obj = json.loads(line)
            if isinstance(obj, dict):
                return obj
        except json.JSONDecodeError:
            continue
    # Robust path: incremental JSONDecoder scan to find embedded objects.
    dec = json.JSONDecoder()
    last_obj: dict[str, Any] = {}
    for i, ch in enumerate(text):
        if ch != "{":
            continue
        try:
            parsed, _end = dec.raw_decode(text[i:])
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict):
            last_obj = parsed
    return last_obj


def _apply_profile_env(env: dict[str, str], profile: str) -> None:
    """Align ``RFO_RUN_PROFILE`` / ``RFO_EXTERNAL_COLLECTION`` with execute semantics."""
    profile = (profile or "").strip()
    if not profile:
        return
    low = profile.lower()
    env["RFO_RUN_PROFILE"] = low
    try:
        from runtime.profiles import resolve as _resolve_profile

        _name, policy = _resolve_profile(low)
        src_pol = policy.get("source_policy") or {}
        if bool(src_pol.get("external_collection_required")):
            env["RFO_EXTERNAL_COLLECTION"] = "required"
    except ValueError:
        pass


# ── search ────────────────────────────────────────────────────────────────────
def resolve_relay_bases(cli_base: str) -> list[str]:
    """Relay API roots (scheme+host[+path]); delegates to ``relay_chain``."""
    bases, _, _ = relay_chain(cli_base, os.environ)
    return bases


def query_json_search_relay(api_base: str, query: str, num: int) -> list[dict]:
    """JSON relay search; ``api_base`` is origin only; path ``/search`` (SearxNG-style)."""
    base = api_base.rstrip("/")
    fetch_n = relay_fetch_cap(num)
    try:
        rows, meta = relay_json_search(
            base,
            query,
            fetch_n,
            user_agent=_USER_AGENT,
            timeout=_HTTP_TIMEOUT + 3,
        )
        if meta.get("post_fallback") and not meta.get("post_error"):
            print(
                f"[search] relay used POST JSON fallback ({api_base}) transport={meta.get('transport')!r}",
                file=sys.stderr,
            )
        if not rows and (meta.get("get_error") or meta.get("post_error") or meta.get("post_parse_failed")):
            print(
                f"[search] relay empty ({api_base}): {json.dumps({k: meta[k] for k in meta if k in ('get_error', 'post_error', 'post_parse_failed', 'body_preview')}, ensure_ascii=False)}",
                file=sys.stderr,
            )
        return rank_relay_rows_for_task(query, rows, limit=num)
    except Exception as e:
        print(f"[search] relay error ({api_base}): {e}", file=sys.stderr)
        return []


# ── fetch ─────────────────────────────────────────────────────────────────────
def fetch_text(url: str, timeout: float = None) -> tuple[str, str]:
    """Fetch and clean page text. Returns (cleaned_text, error_message)."""
    if timeout is None:
        timeout = _HTTP_TIMEOUT
    req = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read()
            try:
                text = raw.decode("utf-8", errors="strict")
            except UnicodeDecodeError:
                text = raw.decode("latin-1", errors="replace")
            text = re.sub(r"<script[^>]*>.*?</script>", "", text, flags=re.DOTALL | re.IGNORECASE)
            text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL | re.IGNORECASE)
            text = re.sub(r"<[^>]+>", " ", text)
            text = re.sub(r"&[a-z]+;", " ", text)
            text = re.sub(r"\s+", " ", text).strip()
            return text[:_MAX_CHARS_PER_SOURCE], ""
    except Exception as e:
        return "", str(e)


# ── claim extraction ────────────────────────────────────────────────────────────
def extract_claims_from_content(sources: list[dict], task: str) -> list[dict]:
    """
    Convert source list into RFO-style claims.
    Each source gets 1 claim with its content as the claim text.
    """
    STATUSES = ("confirmed", "probable", "disputed", "doubtful", "false", "unsupported")

    def _conf_to_v19(c: float) -> str:
        if c >= 0.85:
            return "high"
        if c >= 0.6:
            return "medium"
        return "low"

    claims = []
    evidence_cards = []
    for i, src in enumerate(sources):
        content = str(src.get("content_snippet") or src.get("content") or "").strip()
        if content and body_text_signals_seed_garbage(content):
            continue
        if not content:
            title = str(src.get("title") or "").strip()
            url = str(src.get("url") or src.get("canonical_origin_id") or "").strip()
            parts = [p for p in (title, url) if p]
            err = str(src.get("content_fetch_error") or "").strip()
            if err:
                parts.append(f"[fetch: {err[:120]}]")
            content = " ".join(parts).strip()
        if not content:
            continue
        claim_id = f"C-SRCH-{i+1:03d}"
        ev_id = f"EV-C-SRCH-{i+1:03d}"
        src_id = src.get("source_id", f"SRC-RELAY-{i+1:03d}")

        # Derive status from source type
        status = "confirmed" if src.get("verification_mode") == "raw_document" else "probable"
        confidence = 0.88 if src.get("verification_mode") == "raw_document" else 0.72

        claim = {
            "claim_id": claim_id,
            "claim_text": content[:500],
            "status": status,
            "confidence": confidence,
            "source_ids": [src_id],
            "evidence_card_ids": [ev_id],
            "last_checked_at": now(),
            "origin": "relay_prefetch_bridge",
            "sensitive": False,
            "verbatim_supports": [
                {
                    "evidence_card_id": ev_id,
                    "source_id": src_id,
                    "quote_text": content[:200],
                    "quote_offset_start": 0,
                    "quote_offset_end": min(200, len(content)),
                    "nli_label": "entail",
                }
            ],
        }
        claims.append(claim)

        ev = {
            "evidence_id": ev_id,
            "source_ids": [src_id],
            "claim_ids": [claim_id],
            "extracted_fact_or_excerpt": {
                "kind": "excerpt",
                "text": content[:400],
            },
            "supports": "direct",
            "confidence": _conf_to_v19(confidence),
        }
        evidence_cards.append(ev)
    return claims, evidence_cards


# ── source packet ─────────────────────────────────────────────────────────────
def build_source_packet(search_results: list[dict]) -> dict:
    """Build RFO v19 source packet from search results with fetched content."""
    sources = []
    for i, r in enumerate(search_results):
        url = r.get("url", "")
        if not url.startswith("http"):
            continue
        content, err = fetch_text(url)
        snippet = r.get("snippet", "") or content[:300]
        wiki_flag = os.environ.get("RFO_WIKIPEDIA_HEURISTIC", "").strip().lower() in ("1", "true", "yes")
        is_wiki = wiki_flag and "wikipedia.org" in url
        sources.append({
            "source_id": f"SRC-RELAY-{i+1:03d}",
            "title": r.get("title", url)[:200],
            "canonical_origin_id": url,
            "url": url,
            "source_role": "background",
            "access_level": "primary_access",
            "interest_alignment": "neutral",
            "verification_mode": "raw_document" if is_wiki else "testimony",
            "independence": "high" if is_wiki else "medium",
            "citation_eligible": True,
            "corroboration_type": "authoritative" if is_wiki else "corroborated",
            "fetch_method": "relay_prefetch_bridge",
            "content_snippet": content or snippet,
            "content_fetch_error": err,
        })
    return {"schema_version": "v19.4", "relay_prefetch_bridge": True, "sources": sources}


def _persist_bridge_source_packet(rd: Path, packet_path_str: str) -> None:
    """Copy ``RFO_SOURCE_PACKET`` payload into ``<rd>/sources/`` and patch collection-result."""
    from runtime.util import jr, jw

    pkt = Path(packet_path_str)
    if not pkt.is_file():
        return
    rel = Path("sources") / "external-source-packet.bridge.json"
    dst = rd / rel
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(pkt, dst)
    sha = hashlib.sha256(dst.read_bytes()).hexdigest()
    cr = jr(rd / "collection-result.json", {})
    if isinstance(cr, dict):
        cr["external_source_packet_path"] = rel.as_posix()
        jw(rd / "collection-result.json", cr)
    print(
        f"[4/5] persisted source packet → {rel.as_posix()} sha256={sha[:16]}…",
        file=sys.stderr,
    )


def _merge_relay_fanout_into_collection(rd: Path, stats: dict) -> None:
    """Attach relay fanout stats to ``collection-result.json`` for depth evidence."""
    from runtime.util import jr, jw

    cr = jr(rd / "collection-result.json", {})
    if not isinstance(cr, dict):
        cr = {}
    cr["relay_query_fanout"] = stats
    if isinstance(stats, dict):
        cr["query_vectors"] = stats.get("query_vectors")
        mrg = stats.get("merge") or {}
        if isinstance(mrg, dict):
            cr["relay_fanout_unique_urls"] = mrg.get("unique_urls_after_dedup")
            cr["relay_fanout_raw_rows"] = mrg.get("raw_rows_total")
    jw(rd / "collection-result.json", cr)


def _merge_research_plan_bridge_meta(
    rd: Path,
    *,
    plan_mode: str,
    planner_summary: dict[str, Any] | None,
    run_label: str,
) -> None:
    """Record Research Factory plan mode + planner outcome on ``collection-result.json``."""
    from runtime.util import jr, jw

    cr = jr(rd / "collection-result.json", {})
    if not isinstance(cr, dict):
        cr = {}
    cr["research_plan_mode"] = plan_mode
    cr["research_plan_run_label"] = run_label
    cr["research_plan_path"] = "research/research-plan.json"
    if planner_summary:
        cr["research_plan_planner"] = planner_summary
    jw(rd / "collection-result.json", cr)


# ── RFO patch helpers ─────────────────────────────────────────────────────────
def patch_claims_registry(rd: Path, claims: list[dict], evidence_cards: list[dict]) -> None:
    """Overwrite claims-registry with real source-derived claims."""
    from runtime.util import jw

    status_map = {
        "confirmed": "reported_claim",
        "probable": "inferred_assessment",
        "disputed": "disputed",
        "doubtful": "insufficient_evidence",
        "false": "contradicted",
        "unsupported": "lead_only",
    }

    def _conf_to_v19(c: float) -> str:
        if c >= 0.85:
            return "high"
        if c >= 0.6:
            return "medium"
        return "low"

    v19_claims = []
    for c in claims:
        v19_claims.append({
            "claim_id": c["claim_id"],
            "claim_text": c["claim_text"],
            "claim_type": "source_derived",
            "status": status_map.get(c["status"], "reported_claim"),
            "confidence": _conf_to_v19(c.get("confidence", 0.7)),
            "evidence_card_ids": c.get("evidence_card_ids", []),
            "support_set": [
                {
                    "source_id": c["source_ids"][0] if c.get("source_ids") else "SRC-SEED-001",
                    "evidence_card_id": c["evidence_card_ids"][0] if c.get("evidence_card_ids") else "EV-SEED-001",
                    "role_for_claim": "primary_support",
                }
            ],
        })

    jw(rd / "claims-registry.json", {"schema_version": "v19.0", "claims": v19_claims})
    jw(rd / "claims/claims-registry.json", {
        "run_id": rd.name,
        "taxonomy_version": "v19.2",
        "allowed_statuses": ["reported_claim", "inferred_assessment", "disputed", "insufficient_evidence", "contradicted", "lead_only"],
        "claims": v19_claims,
    })
    jw(rd / "evidence-cards.json", {"schema_version": "v19.0", "evidence_cards": evidence_cards})
    jw(rd / "evidence/evidence-cards.json", {"run_id": rd.name, "evidence_cards": evidence_cards})
    print(
        f"[patch] claims-registry → {len(v19_claims)} claims, evidence-cards → {len(evidence_cards)} cards",
        file=sys.stderr,
    )


def patch_sources_json(rd: Path, sources: list[dict]) -> None:
    """Update sources bundles with schema-aligned records; diagnostics under ``reports/``."""
    from runtime.util import jw

    diagnostics: list[dict[str, Any]] = []
    root_sources: list[dict[str, Any]] = []
    for i, s in enumerate(sources):
        norm, diag = normalize_source_record_v19(s, i)
        if norm.get("source_id"):
            root_sources.append(norm)
            diagnostics.append(diag)

    subdir_sources = list(root_sources)

    jw(rd / "sources.json", {"schema_version": "v19.0", "sources": root_sources})
    jw(rd / "sources/sources.json", {"run_id": rd.name, "sources": subdir_sources})
    rep_dir = rd / "reports"
    rep_dir.mkdir(parents=True, exist_ok=True)
    jw(
        rep_dir / "relay-bridge-sources-diagnostics.json",
        {
            "schema_version": "v19.0",
            "run_id": rd.name,
            "generated_at": now(),
            "relay": "prefetch_bridge",
            "sources_count": len(root_sources),
            "per_source": diagnostics,
        },
    )
    print(
        f"[patch] sources.json → {len(root_sources)} schema-aligned sources "
        f"(diagnostics → reports/relay-bridge-sources-diagnostics.json)",
        file=sys.stderr,
    )


def minimum_sources_policy(profile_name: str) -> int:
    """Minimum independent-looking sources from run-profile contract."""
    try:
        from runtime.profiles import resolve as rp

        _, pol = rp(profile_name)
        sp = pol.get("source_policy") if isinstance(pol, dict) else {}
        mi = sp.get("minimum_independent_sources", 1) if isinstance(sp, dict) else 1
        return max(1, int(mi))
    except Exception:
        return 1


def _write_bridge_worker_failure_meta(
    runs_root: Path,
    *,
    attempt: int,
    returncode: int,
    stdout_tail: str,
    stderr_tail: str,
    parsed_summary: dict[str, Any],
) -> None:
    """Operator-visible record when the worker subprocess fails (E1 hardening)."""
    try:
        p = runs_root / "queue" / "bridge-last-worker-failure.json"
        p.parent.mkdir(parents=True, exist_ok=True)
        rec = {
            "schema_version": "v19.4.1",
            "timestamp": now(),
            "attempt": attempt,
            "worker_returncode": returncode,
            "parsed_stdout_summary": parsed_summary,
            "stdout_tail": (stdout_tail or "")[:8000],
            "stderr_tail": (stderr_tail or "")[:8000],
        }
        p.write_text(json.dumps(rec, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass


def _append_bridge_worker_poll_event(
    latest_run: Path,
    *,
    attempt: int,
    proc: subprocess.CompletedProcess[str],
    summary: dict[str, Any],
    runs_root: Path,
) -> None:
    """Structured poll trail for gateway / operators (plan A1)."""
    if not latest_run.is_dir():
        return
    reason = str(summary.get("reason") or "")
    pending_n: int | None = None
    try:
        pending_n = len(list((Path(runs_root) / "queue" / "pending").glob("*.json")))
    except Exception:
        pending_n = None
    lease_path = Path(runs_root) / "queue" / "worker.lease"
    lease_present = lease_path.is_file()
    payload: dict[str, Any] = {
        "event_name": "bridge.worker_poll",
        "timestamp": now(),
        "attempt": attempt,
        "worker_returncode": proc.returncode,
        "claimed": summary.get("claimed"),
        "reason": reason,
        "lease_present": lease_present,
        "queue_pending_count": pending_n,
        "worker_stdout_summary": (proc.stdout or "").strip()[:1200],
    }
    try:
        jl(latest_run / "observability-events.jsonl", payload)
    except Exception:
        pass


def strict_packet_preflight(profile_lc: str, packet: dict, min_need: int) -> tuple[bool, str]:
    _ = profile_lc  # dossier funnel: uniform preflight regardless of legacy CLI aliases
    rows = packet.get("sources") if isinstance(packet.get("sources"), list) else []
    with_body = sum(1 for s in rows if isinstance(s, dict) and str(s.get("content_snippet") or "").strip())
    if len(rows) < min_need:
        return False, f"packet has {len(rows)} URLs < minimum {min_need}"
    if with_body < min_need:
        return False, f"sources_with_body={with_body} < minimum {min_need}"
    return True, ""


# ── main ──────────────────────────────────────────────────────────────────────
def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="RFO relay prefetch bridge (handoff stdout only)")
    parser.add_argument(
        "--runs-root",
        default=None,
        help="Runs root (deprecated; prefer OPENCLAW_WORKSPACE_DIR / --workspace-root → <ws>/rfo-runs).",
    )
    parser.add_argument(
        "--workspace-root",
        default=None,
        help="Workspace directory; runs use <workspace>/rfo-runs when --runs-root is omitted.",
    )
    parser.add_argument("--task", required=True)
    parser.add_argument("--num-sources", type=int, default=_MAX_SOURCES)
    parser.add_argument(
        "--web-search-json-api-base",
        default="",
        help="HTTP JSON relay origin (no /search suffix). Overrides RFO_WEB_SEARCH_JSON_API_BASE for this run.",
    )
    parser.add_argument("--profile", default="dossier")
    parser.add_argument(
        "--preflight",
        action="store_true",
        help="Print effective-config JSON to stdout and exit (no run allocation).",
    )
    args = parser.parse_args()
    argv = list(sys.argv)

    from _rfo_path_guard import enforce_runs_root_argv

    enforce_runs_root_argv(argv)

    snap = build_effective_config_snapshot(
        skill_root=SKILL_ROOT,
        argv=argv,
        env=os.environ,
        cli_relay_base=args.web_search_json_api_base,
        profile=args.profile.strip().lower(),
        entrypoint="scripts/run_rfo_with_web_search.py",
    )
    if args.preflight:
        print(json.dumps(snap, ensure_ascii=False, indent=2, sort_keys=True))
        errs_pf = snap.get("errors") or []
        if errs_pf or not snap.get("relay"):
            return 2
        return 0

    log_startup_summary(snap)
    errs = snap.get("errors") or []
    if errs or not snap.get("runs_root") or not snap.get("relay"):
        print(
            "[fatal] invalid configuration (see stderr [rfo-config-error] lines; "
            "run with --preflight for effective-config JSON).",
            file=sys.stderr,
        )
        return 2

    runs_root_p = Path(str(snap["runs_root"])).expanduser().resolve(strict=False)
    runs_root = str(runs_root_p)

    task = args.task
    prof_lc = args.profile.strip().lower()
    print(f"\n{'='*60}", file=sys.stderr)
    print(f"[RFO relay] Starting: profile={prof_lc} task={task[:80]!r}", file=sys.stderr)
    print(f"{'='*60}\n", file=sys.stderr)

    relays = list(snap.get("relay_chain") or [])
    if not relays:
        print(
            "[fatal] JSON relay API base unset. Pass --web-search-json-api-base or export "
            "RFO_WEB_SEARCH_JSON_API_BASE.",
            file=sys.stderr,
        )
        return 2

    _ensure_rfo_tree(runs_root_p)

    from runtime.render import allocate
    from runtime.research_bridge_bootstrap import (
        append_bridge_phase,
        bootstrap_early_run_dir,
        write_off_mode_research_plan,
    )
    from runtime.research_plan_planner import (
        default_safety_caps,
        flatten_plan_queries,
        materialize_wave_plan,
        plan_and_write,
    )

    entry = allocate(runs_root, task, "cli", "cli")
    rd_early = Path(entry["run_dir"]).resolve()
    bootstrap_early_run_dir(
        rd_early,
        run_id=str(entry["run_id"]),
        task=task,
        label=str(entry.get("run_label") or "bridge"),
    )
    append_bridge_phase(rd_early, "bridge.allocated", {"run_dir": str(rd_early)})
    try:
        (rd_early / "effective-config.json").write_text(
            json.dumps(snap, ensure_ascii=False, indent=2, sort_keys=True),
            encoding="utf-8",
        )
    except Exception as e:
        print(f"[warn] could not write effective-config.json: {e}", file=sys.stderr)

    plan_mode = (os.environ.get("RFO_RESEARCH_PLAN_MODE") or "off").strip().lower()
    if plan_mode not in ("off", "llm_v1"):
        print(f"[warn] RFO_RESEARCH_PLAN_MODE={plan_mode!r} unknown; using off", file=sys.stderr)
        plan_mode = "off"

    planner_summary: dict[str, Any] | None = None
    fan_stats: dict[str, Any] = {}
    print("[1/5] Sequential relay query expansion (JSON templates → merge/dedup)...", file=sys.stderr)
    min_need_bootstrap = minimum_sources_policy(args.profile)
    slice_cap = max(relay_fetch_cap(args.num_sources) * 4, min_need_bootstrap + 8, 24)
    caps = default_safety_caps()

    if plan_mode == "llm_v1":
        append_bridge_phase(rd_early, "bridge.planner_start", {"mode": plan_mode})
        summary = plan_and_write(rd_early, task)
        planner_summary = summary if isinstance(summary, dict) else {"result": summary}
        append_bridge_phase(rd_early, "bridge.planner_done", dict(planner_summary))
        from runtime.util import jr as _jr_plan

        plan_doc = _jr_plan(rd_early / "research" / "research-plan.json", {})
        q_flat = flatten_plan_queries(plan_doc) if isinstance(plan_doc, dict) else []
        if not q_flat:
            print("[1/5] plan produced zero queries; using template vectors", file=sys.stderr)
            q_flat = build_query_vectors(task)
        fan_rows, fan_stats = fanout_relay_search_from_queries(
            query_json_search_relay,
            relays,
            q_flat,
            args.num_sources,
        )
        fb = bool(planner_summary.get("used_fallback")) if planner_summary else False
        relay_note = f"relay_rows={len(fan_rows)} mode=llm_v1 fallback={fb}"
        materialize_wave_plan(
            rd_early,
            str(entry["run_id"]),
            plan_doc if isinstance(plan_doc, dict) else {},
            relay_note=relay_note,
        )
    else:
        vectors = build_query_vectors(task)
        write_off_mode_research_plan(rd_early, task, queries=vectors, safety=caps)
        fan_rows, fan_stats = fanout_relay_search(
            query_json_search_relay,
            relays,
            task,
            args.num_sources,
        )
        from runtime.util import jr as _jr_plan

        plan_doc = _jr_plan(rd_early / "research" / "research-plan.json", {})
        relay_note = f"relay_rows={len(fan_rows)} mode=off"
        materialize_wave_plan(
            rd_early,
            str(entry["run_id"]),
            plan_doc if isinstance(plan_doc, dict) else {},
            relay_note=relay_note,
        )
        planner_summary = {"mode": "off"}

    ranked = rank_relay_rows_for_task(task, fan_rows, limit=slice_cap)
    results = ranked[:slice_cap]

    if not results:
        msg = "[1/5] Relay fanout returned zero URLs after merge/dedup."
        print(msg, file=sys.stderr)
        print(
            "Tune RFO_WEB_SEARCH_* / relay availability or broaden "
            "`contracts/query-fanout-config.json` templates.",
            file=sys.stderr,
        )
        return 2

    print(
        f"[1/5] Fanout relay rows (post-dedup, pre-rank)={len(fan_rows)}; ranked slice={len(results)}",
        file=sys.stderr,
    )

    # Step 2: Build source packet with fetched content
    print("[2/5] Building source packet with fetched content...", file=sys.stderr)
    packet = build_source_packet(results)
    n_with_content = sum(1 for s in packet["sources"] if str(s.get("content_snippet") or "").strip())
    print(
        f"[2/5] {len(packet['sources'])} sources, {n_with_content} with non-empty bodies",
        file=sys.stderr,
    )

    min_need = minimum_sources_policy(args.profile)
    ok_pf, pf_detail = strict_packet_preflight(prof_lc, packet, min_need)
    if not ok_pf:
        print(f"[2/5] packet preflight fail: {pf_detail}", file=sys.stderr)
        return 2

    packet_path: str | None = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(packet, f, ensure_ascii=False, indent=2)
            packet_path = f.name

        # Step 3: adapter (queue) → worker (runtime), deterministic run_dir from adapter
        print(
            f"[3/5] Queue job + run worker (source packet file: {packet_path})...",
            file=sys.stderr,
        )

        env: dict[str, str] = {str(k): str(v) for k, v in os.environ.items()}
        env["RFO_SOURCE_PACKET"] = packet_path
        env["RFO_PREALLOCATED_RUN_DIR"] = str(rd_early)
        _apply_profile_env(env, args.profile)

        adapter_script = SKILL_ROOT / "scripts" / "interface_runtime_adapter.py"
        worker_script = SCRIPTS_DIR / "runtime_job_worker.py"

        adapter_cmd: list[str] = [
            sys.executable,
            "-S",
            str(adapter_script),
            "adapter",
            "--runs-root",
            runs_root,
            "--interface",
            "cli",
            "--provider",
            "cli",
            "--task",
            task,
        ]

        ad = subprocess.run(
            adapter_cmd,
            cwd=str(SKILL_ROOT),
            capture_output=True,
            text=True,
            env=env,
            timeout=_ADAPTER_TIMEOUT,
        )
        if ad.returncode != 0:
            print(f"[3/5] adapter exit {ad.returncode}", file=sys.stderr)
            if ad.stderr:
                print(ad.stderr[:2000], file=sys.stderr)
            if ad.stdout:
                print(ad.stdout[:2000], file=sys.stderr)
            return 1

        queued = _parse_stdout_json_object(ad.stdout)
        if not queued.get("queued"):
            print("[3/5] ERROR: adapter did not queue a job", file=sys.stderr)
            print(ad.stdout[:2000] if ad.stdout else "(no stdout)", file=sys.stderr)
            return 1

        run_dir_raw = queued.get("run_dir")
        if not run_dir_raw:
            print("[3/5] ERROR: adapter stdout missing run_dir", file=sys.stderr)
            return 1
        latest_run = Path(str(run_dir_raw)).resolve()
        print(f"[3/5] Queued run_dir: {latest_run}", file=sys.stderr)
        if latest_run != rd_early:
            print(
                f"[3/5] ERROR: adapter run_dir mismatch (expected {rd_early}, got {latest_run})",
                file=sys.stderr,
            )
            return 1

        worker_claimed = False
        last_worker_out = ""
        for attempt in range(_WORKER_RETRY_MAX):
            proc = subprocess.run(
                [
                    sys.executable,
                    "-S",
                    str(worker_script),
                    "--runs-root",
                    runs_root,
                    "--execute-runtime",
                ],
                cwd=str(SKILL_ROOT),
                capture_output=True,
                text=True,
                env=env,
                timeout=_WORKER_TIMEOUT,
            )
            last_worker_out = (proc.stdout or "") + "\n" + (proc.stderr or "")
            summary = _parse_stdout_json_object(proc.stdout or "")
            _append_bridge_worker_poll_event(
                latest_run,
                attempt=attempt + 1,
                proc=proc,
                summary=summary,
                runs_root=runs_root,
            )
            claimed_ok = summary.get("claimed") is True and (proc.returncode == 0)
            if claimed_ok:
                worker_claimed = True
                print(f"[3/5] worker claimed job (attempt {attempt + 1})", file=sys.stderr)
                break
            reason = str(summary.get("reason") or "")
            # E1: stdout may claim success while subprocess failed — never treat as claimed.
            if summary.get("claimed") is True and proc.returncode != 0:
                print(
                    f"[3/5] worker stdout claimed=true but process exit {proc.returncode} "
                    "(treating as failure; see queue/bridge-last-worker-failure.json)",
                    file=sys.stderr,
                )
                print(last_worker_out[:2500], file=sys.stderr)
                _write_bridge_worker_failure_meta(
                    runs_root,
                    attempt=attempt + 1,
                    returncode=int(proc.returncode or -1),
                    stdout_tail=(proc.stdout or "")[-8000:],
                    stderr_tail=(proc.stderr or "")[-8000:],
                    parsed_summary=summary,
                )
                return 1
            if proc.returncode != 0:
                print(f"[3/5] worker exit {proc.returncode}", file=sys.stderr)
                print(last_worker_out[:2500], file=sys.stderr)
                _write_bridge_worker_failure_meta(
                    runs_root,
                    attempt=attempt + 1,
                    returncode=int(proc.returncode or -1),
                    stdout_tail=(proc.stdout or "")[-8000:],
                    stderr_tail=(proc.stderr or "")[-8000:],
                    parsed_summary=summary,
                )
                return 1
            print(
                f"[3/5] worker not claimed ({reason}), retry {attempt + 1}/{_WORKER_RETRY_MAX}",
                file=sys.stderr,
            )
            time.sleep(_WORKER_RETRY_BASE_S + 0.12 * attempt)

        if not worker_claimed:
            print(
                "[3/5] ERROR: worker did not claim a pending job after retries — "
                "check queue/pending and queue/worker.lease "
                "(canonical: <runs-root>/queue/worker.lease). "
                "If lease is stale, set RFO_WORKER_LEASE_STALE_SECONDS or remove the file after verifying no worker holds it.",
                file=sys.stderr,
            )
            print(last_worker_out[:2500], file=sys.stderr)
            return 1

        if not latest_run.is_dir():
            print(f"[3/5] ERROR: run dir missing: {latest_run}", file=sys.stderr)
            return 1

        # Step 4: Extract real claims from source packet → patch artifacts
        print(f"[4/5] Extracting claims from {len(packet['sources'])} sources...", file=sys.stderr)
        all_sources = list(packet["sources"])
        existing_sources_path = latest_run / "sources.json"
        if existing_sources_path.exists():
            try:
                existing = json.loads(existing_sources_path.read_text())
                existing_srcs = existing.get("sources", [])
                seen = {s.get("source_id") for s in all_sources}
                for es in existing_srcs:
                    if es.get("source_id") not in seen:
                        all_sources.append(es)
                print(
                    f"[4/5] Merged {len(existing_srcs)} existing sources → {len(all_sources)} total",
                    file=sys.stderr,
                )
            except Exception as e:
                print(f"[4/5] Could not merge existing sources: {e}", file=sys.stderr)

        real_claims, real_ev = extract_claims_from_content(all_sources, task)
        print(f"[4/5] Generated {len(real_claims)} real claims from sources", file=sys.stderr)

        if real_claims:
            patch_claims_registry(latest_run, real_claims, real_ev)
        else:
            print("[4/5] WARNING: no real claims extracted — will use scaffold", file=sys.stderr)
        # Always align sources.json with v19 schema (relay enums / collector extras),
        # independent of claim extraction (empty claims must not skip normalization).
        patch_sources_json(latest_run, all_sources)

        if packet_path:
            _persist_bridge_source_packet(latest_run, packet_path)
        _merge_relay_fanout_into_collection(latest_run, fan_stats)
        _merge_research_plan_bridge_meta(
            latest_run,
            plan_mode=plan_mode,
            planner_summary=planner_summary,
            run_label=str(entry.get("run_label") or ""),
        )

        print("[4/5] Re-rendering HTML with real claims...", file=sys.stderr)
        run_id = job_id_gate = cmd_id_gate = "UNKNOWN"
        try:
            from runtime.render import render_all
            from runtime.util import jr

            run_json = jr(latest_run / "run.json", {})
            run_id = str(run_json.get("run_id") or "UNKNOWN")
            job_id_gate = str(run_json.get("job_id") or "UNKNOWN")
            cmd_id_gate = str(run_json.get("command_id") or "UNKNOWN")
            render_all(latest_run, task, run_id, job_id_gate, cmd_id_gate, "cli")
            print("[4/5] Re-render complete", file=sys.stderr)
        except Exception as e:
            strict = (
                os.environ.get("RFO_BRIDGE_RENDER_STRICT", "").strip().lower()
                in ("1", "true", "yes")
            )
            msg = f"[4/5] Re-render error: {e}"
            if strict:
                print(msg, file=sys.stderr)
                print(
                    "[4/5] RFO_BRIDGE_RENDER_STRICT enabled — aborting before handoff (exit 21). "
                    "Unset or set RFO_BRIDGE_RENDER_STRICT=0 for non-fatal bridge behavior.",
                    file=sys.stderr,
                )
                return 21
            print(f"[4/5] Re-render error (non-fatal): {e}", file=sys.stderr)

        try:
            from runtime.worker_impl import _build_package_allow_stub, build_package as _bridge_build_package

            _bridge_build_package(
                latest_run,
                allow_stub=_build_package_allow_stub(latest_run),
                quiet=True,
            )
            print("[4/5] Package rebuilt after bridge render (quiet)", file=sys.stderr)
        except Exception as e:
            print(f"[4/5] Package rebuild error (non-fatal): {e}", file=sys.stderr)

        try:
            from runtime.citation_grounding import evaluate as _evaluate_citation_grounding_bridge
            from runtime.util import jr as _jr_b, jw as _jw_b

            rp_doc = _jr_b(latest_run / "run-profile.json", {})
            pname = str(rp_doc.get("profile") or prof_lc or "dossier")
            cg = _evaluate_citation_grounding_bridge(
                latest_run,
                run_id=run_id,
                job_id=job_id_gate,
                profile=pname,
            )
            fm = _jr_b(latest_run / "feature-truth-matrix.json", {})
            if isinstance(fm, dict):
                fm["citation_grounding_summary"] = {
                    "raf": cg.get("relevance_aware_factuality_score"),
                    "dfl": cg.get("deflection_rate_when_no_grounding"),
                    "passed": cg.get("passed"),
                    "requires_grounding": cg.get("requires_grounding"),
                    "claims_total": cg.get("claims_total"),
                    "claims_grounded": cg.get("claims_grounded"),
                }
                _jw_b(latest_run / "feature-truth-matrix.json", fm)
                print("[4/5] citation-grounding + feature-truth-matrix citation block resynced", file=sys.stderr)
        except Exception as e:
            print(f"[4/5] citation/matrix resync error (non-fatal): {e}", file=sys.stderr)

        print(
            "[4/5] Leaving final-answer-gate untouched (dossier: run validators for truth)",
            file=sys.stderr,
        )

        print(
            "[5/5] Agent handoff (__RFO_SKILL_AGENT_HANDOFF__=… emitted to stdout as single line)",
            file=sys.stderr,
        )
        from runtime.artifact_execute_impl import emit_agent_skill_handoff

        _st, exit_code = emit_agent_skill_handoff(latest_run, task)

        print(f"\n{'='*60}", file=sys.stderr)
        print(f"[DONE] Run: {latest_run.name}", file=sys.stderr)
        print(
            f"[DONE] Sources: {len(all_sources)}, Claims: {len(real_claims)}, handoff_status={_st}",
            file=sys.stderr,
        )
        print(f"{'='*60}\n", file=sys.stderr)
        return exit_code
    finally:
        if packet_path:
            Path(packet_path).unlink(missing_ok=True)


if __name__ == "__main__":
    sys.exit(main())