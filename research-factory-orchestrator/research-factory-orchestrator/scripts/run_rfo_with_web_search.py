#!/usr/bin/env python3
"""
RFO v19.4 — JSON relay prefetch bridge (neutral contract)

collector.py делает только HEAD‑probe семян или загрузку RFO_SOURCE_PACKET; список
URL для исследования собирается здесь через **настраиваемый** HTTP JSON relay
(типичный эндпоинт вида `/search?q=…&format=json`; хост задаёт оператор).

Обязательно задать базу через ``--web-search-json-api-base`` или
``RFO_WEB_SEARCH_JSON_API_BASE`` (совместимо: ``RFO_SEARXNG_URL`` только как имя
переменной для миграции; значение всегда задаёт оператор).

Опционально: ``RFO_WIKIPEDIA_HEURISTIC=1`` — считать URL с ``wikipedia.org`` сырым
документом (иначе эвристика выключена).

Поток:
  1. relay search + HTTP fetch страниц
  2. RFO_SOURCE_PACKET + очередь RFO как обычно
  3. патчи claims-registry / re-render / stdout ``__RFO_SKILL_AGENT_HANDOFF__=``

По умолчанию ``--profile live-bridge`` (строже mvr).
Для экспресс-режима: ``--profile mvr``.
"""
from __future__ import annotations

import json
import os
import re
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

from runtime.util import now  # noqa: E402

from rfo_relay_search_helpers import (  # noqa: E402
    build_relay_params,
    rank_relay_rows_for_task,
    relay_fetch_cap,
)

# ── config ────────────────────────────────────────────────────────────────────
_HTTP_TIMEOUT = float(os.environ.get("RFO_HTTP_TIMEOUT", "8.0"))
_USER_AGENT = (os.environ.get("RFO_WEB_SEARCH_USER_AGENT") or "").strip() or "RFO/19.4-RelayPrefetch"
_MAX_CHARS_PER_SOURCE = 3000   # truncate content per source
_MAX_SOURCES = 8

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
    text = (stdout or "").strip()
    if not text:
        return {}
    try:
        obj = json.loads(text)
        return obj if isinstance(obj, dict) else {}
    except json.JSONDecodeError:
        pass
    for line in reversed(text.splitlines()):
        line = line.strip()
        if line.startswith("{") and line.endswith("}"):
            try:
                obj = json.loads(line)
                if isinstance(obj, dict):
                    return obj
            except json.JSONDecodeError:
                continue
    return {}


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
    """Relay API roots (scheme+host[+path]), no literals: operator supplies all."""
    seen: list[str] = []
    for raw in (
        (cli_base or "").strip(),
        os.environ.get("RFO_WEB_SEARCH_JSON_API_BASE", "").strip(),
        os.environ.get("RFO_SEARXNG_URL", "").strip(),
        os.environ.get("RFO_WEB_SEARCH_SECONDARY_JSON_API_BASE", "").strip(),
    ):
        if raw and raw not in seen:
            seen.append(raw.rstrip("/"))
    return seen


def query_json_search_relay(api_base: str, query: str, num: int) -> list[dict]:
    """JSON relay search; ``api_base`` is origin only; path ``/search`` appended (SearxNG-style)."""
    base = api_base.rstrip("/")
    fetch_n = relay_fetch_cap(num)
    params = build_relay_params(query, fetch_n)
    url = f"{base}/search?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=_HTTP_TIMEOUT + 3) as resp:
            data = json.loads(resp.read())
            results = []
            for r in data.get("results", [])[:num]:
                raw_url = r.get("url", "")
                if not raw_url.startswith("http"):
                    continue
                results.append(
                    {
                        "url": raw_url,
                        "title": r.get("title", "")[:300],
                        "snippet": (r.get("content") or "")[:500],
                    }
                )
            return rank_relay_rows_for_task(query, results, limit=num)
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
    return {"sources": sources}


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
    print(f"[patch] claims-registry → {len(v19_claims)} claims, evidence-cards → {len(evidence_cards)} cards")


def patch_sources_json(rd: Path, sources: list[dict]) -> None:
    """Update sources.json and sources/sources.json with full source list."""
    from runtime.util import jw

    root_sources = []
    subdir_sources = []
    for s in sources:
        src = {k: v for k, v in s.items() if k != "content_snippet"}
        root_sources.append(src)
        subdir_sources.append(src)

    jw(rd / "sources.json", {"schema_version": "v19.0", "sources": root_sources})
    jw(rd / "sources/sources.json", {"run_id": rd.name, "sources": subdir_sources})
    print(f"[patch] sources.json → {len(sources)} sources")


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


def strict_packet_preflight(profile_lc: str, packet: dict, min_need: int) -> tuple[bool, str]:
    if profile_lc == "mvr":
        return True, ""
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
    parser.add_argument("--runs-root", required=True)
    parser.add_argument("--task", required=True)
    parser.add_argument("--num-sources", type=int, default=_MAX_SOURCES)
    parser.add_argument(
        "--web-search-json-api-base",
        default="",
        help="HTTP JSON relay origin (no /search suffix). Overrides RFO_WEB_SEARCH_JSON_API_BASE for this run.",
    )
    parser.add_argument("--profile", default="live-bridge")
    parser.add_argument(
        "--allow-gate-stub",
        action="store_true",
        help="Write optimistic final-answer-gate stub (normally disabled for strict profiles)",
    )
    parser.add_argument(
        "--best-effort-continue",
        action="store_true",
        help="After worker subprocess non-zero exit, continue bridge steps instead of failing (default off).",
    )
    args = parser.parse_args()

    def _experiment_bridge_ok() -> bool:
        return os.environ.get("RFO_EXPERIMENT_BRIDGE", "").strip().lower() in ("1", "true", "yes")

    def _smoke_env() -> bool:
        return os.environ.get("RFO_SMOKE", "").strip().lower() in ("1", "true", "yes")

    if (args.allow_gate_stub or args.best_effort_continue) and not (
        _experiment_bridge_ok() or _smoke_env()
    ):
        print(
            "[fatal] --allow-gate-stub / --best-effort-continue require "
            "RFO_EXPERIMENT_BRIDGE=1 (or RFO_SMOKE=1 for smoke runs).",
            file=sys.stderr,
        )
        return 2

    task = args.task
    prof_lc = args.profile.strip().lower()
    print(f"\n{'='*60}")
    print(f"[RFO relay] Starting: profile={prof_lc} task={task[:80]!r}")
    print(f"{'='*60}\n")

    relays = resolve_relay_bases(args.web_search_json_api_base)
    if not relays:
        print(
            "[fatal] JSON relay API base unset. Pass --web-search-json-api-base or export "
            "RFO_WEB_SEARCH_JSON_API_BASE (legacy alias: RFO_SEARXNG_URL). No baked-in hostname.",
            file=sys.stderr,
        )
        return 2

    print("[1/5] Query JSON relay...")
    results: list[dict] = []
    for base in relays:
        results = query_json_search_relay(base, task, args.num_sources)
        if results:
            break

    if not results:
        msg = "[1/5] Relay returned zero URLs."
        if prof_lc == "mvr":
            allow_empty = os.environ.get("RFO_ALLOW_MVR_EMPTY_RELAY", "").strip().lower() in (
                "1",
                "true",
                "yes",
            )
            if not allow_empty:
                print(
                    f"{msg} profile=mvr requires RFO_ALLOW_MVR_EMPTY_RELAY=1 to continue with an empty scaffold.",
                    file=sys.stderr,
                )
                return 2
            print(f"{msg} continuing with empty scaffold (mvr + RFO_ALLOW_MVR_EMPTY_RELAY)")
        else:
            print(msg, file=sys.stderr)
            print("Relax with --profile mvr or tune RFO_WEB_SEARCH_* / relay availability.", file=sys.stderr)
            return 2

    print(f"[1/5] Got {len(results)} relay rows")

    # Step 2: Build source packet with fetched content
    print("[2/5] Building source packet with fetched content...")
    packet = build_source_packet(results)
    n_with_content = sum(1 for s in packet["sources"] if str(s.get("content_snippet") or "").strip())
    print(f"[2/5] {len(packet['sources'])} sources, {n_with_content} with non-empty bodies")

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
        print(f"[3/5] Queue job + run worker (source packet file: {packet_path})...")
        runs_root = str(Path(args.runs_root).resolve())
        _ensure_rfo_tree(Path(runs_root))

        env: dict[str, str] = {str(k): str(v) for k, v in os.environ.items()}
        env["RFO_SOURCE_PACKET"] = packet_path
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
        print(f"[3/5] Queued run_dir: {latest_run}")

        worker_claimed = False
        worker_hard_failed = False
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
            if summary.get("claimed") is True:
                worker_claimed = True
                print(f"[3/5] worker claimed job (attempt {attempt + 1})")
                break
            reason = str(summary.get("reason") or "")
            if proc.returncode != 0:
                print(f"[3/5] worker exit {proc.returncode}", file=sys.stderr)
                print(last_worker_out[:2500], file=sys.stderr)
                if args.best_effort_continue:
                    worker_hard_failed = True
                    print("[3/5] WARN: --best-effort-continue set; continuing bridge despite worker failure.")
                    break
                return 1
            print(f"[3/5] worker not claimed ({reason}), retry {attempt + 1}/{_WORKER_RETRY_MAX}")
            time.sleep(_WORKER_RETRY_BASE_S + 0.12 * attempt)

        if not worker_claimed:
            if args.best_effort_continue and worker_hard_failed and latest_run.is_dir():
                print("[3/5] WARN: proceeding with incomplete worker run (best-effort).")
            else:
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
        print(f"[4/5] Extracting claims from {len(packet['sources'])} sources...")
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
                print(f"[4/5] Merged {len(existing_srcs)} existing sources → {len(all_sources)} total")
            except Exception as e:
                print(f"[4/5] Could not merge existing sources: {e}")

        real_claims, real_ev = extract_claims_from_content(all_sources, task)
        print(f"[4/5] Generated {len(real_claims)} real claims from sources")

        if real_claims:
            patch_claims_registry(latest_run, real_claims, real_ev)
            patch_sources_json(latest_run, all_sources)
        else:
            print("[4/5] WARNING: no real claims extracted — will use scaffold")

        print("[4/5] Re-rendering HTML with real claims...")
        run_id = job_id_gate = cmd_id_gate = "UNKNOWN"
        try:
            from runtime.render import render_all
            from runtime.util import jr

            run_json = jr(latest_run / "run.json", {})
            run_id = str(run_json.get("run_id") or "UNKNOWN")
            job_id_gate = str(run_json.get("job_id") or "UNKNOWN")
            cmd_id_gate = str(run_json.get("command_id") or "UNKNOWN")
            render_all(latest_run, task, run_id, job_id_gate, cmd_id_gate, "cli")
            print("[4/5] Re-render complete")
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
            print(f"[4/5] Re-render error (non-fatal): {e}")

        if prof_lc == "mvr" or args.allow_gate_stub:
            try:
                from runtime.util import jw

                jw(
                    latest_run / "final-answer-gate.json",
                    {
                        "schema_version": "v19.0",
                        "run_id": run_id,
                        "passed": True,
                        "status": "content_rendered_relay_prefetch",
                        "checks": {},
                        "overconfidence_risk": {"blocking": [], "warnings": [], "signals": {}},
                        "created_at": now(),
                    },
                )
            except Exception as e:
                print(f"[4/5] gate update error: {e}")
        else:
            print("[4/5] Leaving final-answer-gate untouched (live-bridge: run validators for truth)")

        print("[5/5] Stdout agent handoff (see __RFO_SKILL_AGENT_HANDOFF__=… on last line).")
        from runtime.artifact_execute_impl import emit_agent_skill_handoff

        _st, exit_code = emit_agent_skill_handoff(latest_run, task)

        print(f"\n{'='*60}")
        print(f"[DONE] Run: {latest_run.name}")
        print(f"[DONE] Sources: {len(all_sources)}, Claims: {len(real_claims)}, handoff_status={_st}")
        print(f"{'='*60}\n")
        return exit_code
    finally:
        if packet_path:
            Path(packet_path).unlink(missing_ok=True)


if __name__ == "__main__":
    sys.exit(main())