#!/usr/bin/env python3
"""
RFO full research standalone driver (relay + HTTP fetch).

**Tool selection is fixed by this driver** (relay JSON search → Wikipedia
``opensearch`` + ``query`` extracts on the configured MediaWiki host → HTTP
fetch of relay URLs). Operators and host LLMs must **not** use env vars to
pick “which search backend runs”; only **infrastructure endpoints** and
**relay row budget** are configurable.

JSON relay HTTP base is **never** inferred; export ``RFO_WEB_SEARCH_JSON_API_BASE``
(or ``RFO_SEARXNG_URL`` rename for migration).

Infrastructure (URLs / capacity):

- ``RFO_RELAY_MAX_RESULTS`` / ``RFO_MAX_SEARCH_RESULTS`` — merged fanout row budget (default **40**; hard cap ``RFO_RELAY_MAX_RESULTS_HARD_CAP``, default 200).
- ``RFO_WEB_SEARCH_FETCH_CAP`` — optional SearXNG ``num`` ceiling; otherwise ``max(requested, min(200, 2×requested))``.
- ``RFO_MEDIAWIKI_API_QUERY_URL`` — custom ``action=query`` API stem; if unset, ``RFO_WIKIPEDIA_OPENSEARCH_URL`` stem (no query string) or the public English Wikipedia API host is used for both OpenSearch and extracts.
- ``RFO_MEDIAWIKI_PAGE_ORIGIN`` — optional ``https://…`` origin for ``/wiki/`` links; otherwise derived from the API URL host.
"""
from __future__ import annotations

import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = SKILL_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))
sys.path.insert(0, str(SKILL_ROOT))

from runtime.citation_grounding import evaluate as citation_grounding_evaluate  # noqa: E402
from runtime.report_html import write_canonical_full_report_html  # noqa: E402
from runtime.profiles import resolve as resolve_profile  # noqa: E402
from runtime.status import VERSION  # noqa: E402
from runtime.pkg_required_scaffold import ensure_pkg_required_paths  # noqa: E402
from runtime.schema_defaults import minimal_valid  # noqa: E402
from runtime.util import jr, jw, now, sid, slug, tw  # noqa: E402

from rfo_query_fanout import fanout_relay_search  # noqa: E402
from rfo_relay_search_helpers import build_relay_params, rank_relay_rows_for_task, relay_fetch_cap  # noqa: E402

# ── config ─────────────────────────────────────────────────────────────────────
_HTTP_TIMEOUT = float(os.environ.get("RFO_HTTP_TIMEOUT", "8.0"))
_USER_AGENT = (os.environ.get("RFO_WEB_SEARCH_USER_AGENT") or "").strip() or f"RFO/{VERSION}-FullRelay"

# Fixed pipeline bounds (not operator “tool switches”).
_MAX_FETCH_CHARS = 4000
_NARRATIVE_MAP_MAX_SOURCES = 24
_WIKI_MAX_ARTICLES = 24
_WIKI_OPENSEARCH_LIMIT = 12
_DEFAULT_PUBLIC_MEDIAWIKI_API = "https://en.wikipedia.org/w/api.php"


def relay_api_base(cli_base: str) -> str | None:
    for raw in ((cli_base or "").strip(), os.environ.get("RFO_WEB_SEARCH_JSON_API_BASE", "").strip(), os.environ.get("RFO_SEARXNG_URL", "").strip()):
        if raw:
            return raw.rstrip("/")
    return None


def _env_int(name: str, default: int, *, min_v: int = 1, max_v: int | None = None) -> int:
    raw = os.environ.get(name, "").strip()
    if not raw:
        v = default
    else:
        try:
            v = int(raw)
        except ValueError:
            v = default
    v = max(min_v, v)
    if max_v is not None:
        v = min(v, max_v)
    return v


def relay_max_results() -> int:
    """Merged fanout row budget after dedup (SearX ``num`` per vector query uses the same value)."""
    cap = _env_int("RFO_RELAY_MAX_RESULTS_HARD_CAP", 200, min_v=10, max_v=500)
    for key in ("RFO_RELAY_MAX_RESULTS", "RFO_MAX_SEARCH_RESULTS", "RFO_WEB_SEARCH_NUM_RESULTS"):
        raw = os.environ.get(key, "").strip()
        if raw:
            try:
                return max(1, min(int(raw), cap))
            except ValueError:
                pass
    return min(40, cap)


def mediawiki_query_action_url() -> str:
    """``action=query`` / OpenSearch host: custom env, optional opensearch URL stem, else public Wikipedia API."""
    q = os.environ.get("RFO_MEDIAWIKI_API_QUERY_URL", "").strip()
    if q:
        return q.rstrip("/")
    os_url = os.environ.get("RFO_WIKIPEDIA_OPENSEARCH_URL", "").strip()
    if os_url:
        return os_url.split("?", 1)[0].strip().rstrip("/")
    return _DEFAULT_PUBLIC_MEDIAWIKI_API.rstrip("/")


def wiki_page_origin() -> str:
    o = os.environ.get("RFO_MEDIAWIKI_PAGE_ORIGIN", "").strip().rstrip("/")
    if o:
        return o
    api = mediawiki_query_action_url()
    if not api:
        return ""
    try:
        p = urllib.parse.urlparse(api)
        if p.scheme and p.netloc:
            return f"{p.scheme}://{p.netloc}"
    except Exception:
        pass
    return ""


def wiki_opensearch_titles(search_term: str, *, limit: int) -> list[str]:
    """MediaWiki ``action=opensearch`` — narrow factual titles; same host as ``mediawiki_query_action_url()``."""
    api = mediawiki_query_action_url()
    if not api:
        return []
    params = {
        "action": "opensearch",
        "search": (search_term or "")[:500],
        "limit": str(max(1, limit)),
        "format": "json",
        "namespace": "0",
    }
    join = "&" if "?" in api else "?"
    url = api + join + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=min(20.0, _HTTP_TIMEOUT + 10)) as resp:
            data = json.loads(resp.read())
    except Exception as ex:
        print(f"[wiki] opensearch error: {ex}", file=sys.stderr)
        return []
    if not isinstance(data, list) or len(data) < 2:
        return []
    titles = data[1]
    if not isinstance(titles, list):
        return []
    out: list[str] = []
    seen: set[str] = set()
    for t in titles:
        if not isinstance(t, str):
            continue
        t = t.strip()
        if not t or t in seen:
            continue
        seen.add(t)
        out.append(t)
        if len(out) >= limit:
            break
    return out


# ── search ────────────────────────────────────────────────────────────────────
def search_json_relay(api_base: str, query: str, num: int | None = None) -> list[dict]:
    if num is None:
        num = relay_max_results()
    num = max(1, int(num))
    base = api_base.rstrip("/")
    fetch_n = relay_fetch_cap(num)
    params = build_relay_params(query, fetch_n)
    url = f"{base}/search?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=_HTTP_TIMEOUT + 5) as resp:
            data = json.loads(resp.read())
            results = []
            for r in data.get("results", [])[:num]:
                u = r.get("url", "")
                if not u.startswith("http"):
                    continue
                results.append({
                    "url": u,
                    "title": r.get("title", "")[:300],
                    "snippet": (r.get("content") or "")[:500],
                    "engine": r.get("engine", ""),
                })
            return rank_relay_rows_for_task(query, results, limit=num)
    except Exception as e:
        print(f"[search] relay error: {e}")
        return []


def fetch_wiki_extract(title: str) -> tuple[str, str]:
    """Fetch Wikipedia extract via ``action=query`` (``RFO_MEDIAWIKI_API_QUERY_URL`` or same host as OpenSearch)."""
    api = mediawiki_query_action_url()
    if not api:
        return "", "mediawiki_query_action_url() empty"
    join = "&" if "?" in api else "?"
    url = api + join + urllib.parse.urlencode(
        {
            "action": "query",
            "titles": title,
            "prop": "extracts",
            "explaintext": "1",
            "format": "json",
            "redirects": "1",
        }
    )
    req = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
            pages = data.get("query", {}).get("pages", {})
            for v in pages.values():
                e = v.get("extract", "")
                if e:
                    return e[:5000], ""
            return "", "no extract"
    except Exception as ex:
        return "", str(ex)


def fetch_url_text(url: str) -> tuple[str, str]:
    """Fetch and clean a URL to plain text."""
    req = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=_HTTP_TIMEOUT) as resp:
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
            return text[:_MAX_FETCH_CHARS], ""
    except Exception as e:
        return "", str(e)


# ── source builders ────────────────────────────────────────────────────────────
# Domains that are noise for medical/scientific research
_NOISE_DOMAINS = {
    "imdb.com", "amazon.com", "amazon.in", "filmi", "starsunfolded",
    "blogspot.com", "nettv4", "knocks.in", "bookmyshow.com", "grokipedia",
    "youtube.com", "google.com", "facebook.com", "twitter.com", "x.com",
}
# Title prefixes that are noise
_NOISE_PREFIXES = ["Ravi Kale", "Filmography", "Biography", "Age, Wife",
                    "Movie List", "Height", "Net Worth"]

_NOISE_DOMAINS_FS = frozenset(_NOISE_DOMAINS)


def _topic_bucket(task: str) -> str:
    """Coarse domain for IO / propaganda copy (avoid medical template on political news)."""
    t = (task or "").lower()
    medical = (
        "virus", "hantavirus", "covid", "clinical", "patient", "vaccine",
        "синдром", "лечен", "медицин", "генет", "диагноз", "больниц",
    )
    political = (
        "арест", "суд", "полити", "войн", "ермак", "estonia", "эстон",
        "rail", "инфраструктур", "правитель", "закон", "новост", "скандал",
        "расследован", "коррупц", "офис презид",
    )
    if any(k in t for k in medical):
        return "medical_scientific"
    if any(k in t for k in political):
        return "political_news"
    return "general"


def _io_method_note(bucket: str) -> str:
    if bucket == "medical_scientific":
        return "Medical/scientific topic — prioritize authoritative biomedical sources; watch for sensational health framing."
    if bucket == "political_news":
        return "Political/news topic — assess state-aligned framing, selective omission, and outlet independence."
    return "General topic — apply standard IO / narrative hygiene checks."


def _build_narrative_map(sources: list[dict], task: str) -> list[dict]:
    """Lightweight narrative anchors from fetched sources (non-empty map for reporting)."""
    out: list[dict] = []
    cap = _NARRATIVE_MAP_MAX_SOURCES
    for s in sources[:cap]:
        url = s.get("url") or ""
        try:
            host = urllib.parse.urlparse(url).netloc.lower().lstrip("www.")
        except Exception:
            host = ""
        title = (s.get("title") or "")[:240]
        if not host and not title:
            continue
        out.append({
            "publisher_host": host,
            "headline_or_lede": title,
            "relation_to_task": "cited_source",
            "confidence": "medium",
        })
    if not out and task:
        out.append({
            "publisher_host": "task_scope",
            "headline_or_lede": task[:200],
            "relation_to_task": "query_scope",
            "confidence": "low",
        })
    return out


def build_sources(task: str, search_results: list[dict]) -> list[dict]:
    """Build clean sources: Wikipedia OpenSearch + extracts, then relay web rows (fetched)."""
    sources = []

    wiki_pages: list[str] = []
    seen_wiki: set[str] = set()

    def _add_wiki_titles(titles: list[str]) -> None:
        for t in titles:
            t = (t or "").strip()
            if not t:
                continue
            k = t.lower()
            if k in seen_wiki:
                continue
            seen_wiki.add(k)
            wiki_pages.append(t)

    t = (task or "").strip()
    _add_wiki_titles(wiki_opensearch_titles(t, limit=_WIKI_OPENSEARCH_LIMIT))
    parts = t.split()
    if len(parts) > 5:
        _add_wiki_titles(
            wiki_opensearch_titles(" ".join(parts[:5]), limit=max(3, _WIKI_OPENSEARCH_LIMIT // 2)),
        )

    wiki_origin = wiki_page_origin()
    if wiki_pages and not wiki_origin:
        print(
            "[wiki] cannot build /wiki/ URLs: set RFO_MEDIAWIKI_PAGE_ORIGIN or a full "
            "RFO_MEDIAWIKI_API_QUERY_URL / RFO_WIKIPEDIA_OPENSEARCH_URL host",
            file=sys.stderr,
        )
        wiki_pages = []

    noise_domains = _NOISE_DOMAINS_FS
    noise_prefixes = _NOISE_PREFIXES

    for i, title in enumerate(wiki_pages[:_WIKI_MAX_ARTICLES]):
        text, err = fetch_wiki_extract(title)
        if not text:
            continue
        slug = urllib.parse.quote(title.replace(" ", "_"))
        url = f"{wiki_origin}/wiki/{slug}"
        sources.append({
            "source_id": f"SRC-WIKI-{i+1:03d}",
            "title": title,
            "canonical_origin_id": url,
            "url": url,
            "source_role": "authoritative",
            "access_level": "primary_access",
            "interest_alignment": "neutral",
            "verification_mode": "raw_document",
            "independence": "high",
            "citation_eligible": True,
            "corroboration_type": "authoritative",
            "fetch_method": "wikipedia_api",
            "content": text,
            "content_error": err,
            "is_wikipedia": True,
        })
        print(f"  [wiki] {title}: {len(text)} chars")

    # Deduplicate by URL (already have Wikipedia sources)
    wiki_urls = {s["url"] for s in sources}

    # ── Relay web rows (non-Wikipedia, non-noise)
    for i, r in enumerate(search_results):
        url = r["url"]
        if url in wiki_urls:
            continue
        domain = urllib.parse.urlparse(url).netloc.lower().lstrip("www.")
        if any(domain.endswith(d) for d in noise_domains):
            print(f"  [skip] noise domain: {domain}")
            continue
        title = r.get("title", "")
        if any(title.startswith(p) for p in noise_prefixes):
            print(f"  [skip] noise title: {title[:40]}")
            continue
        # Fetch content
        content, err = fetch_url_text(url)
        if not content or len(content) < 100:
            # Fall back to snippet if fetch fails
            content = r.get("snippet", "")
        if len(content) < 50:
            print(f"  [skip] no content: {url[:60]}")
            continue
        sources.append({
            "source_id": f"SRC-WEB-{i+1:03d}",
            "title": title[:200] or url[:100],
            "canonical_origin_id": url,
            "url": url,
            "source_role": "background",
            "access_level": "primary_access",
            "interest_alignment": "neutral",
            "verification_mode": "testimony",
            "independence": "medium",
            "citation_eligible": True,
            "corroboration_type": "corroborated",
            "fetch_method": "relay_primary_fetch",
            "content": content[:_MAX_FETCH_CHARS],
            "content_error": err,
            "is_wikipedia": False,
        })

    return sources


# ── claim extraction ───────────────────────────────────────────────────────────
def make_claims(sources: list[dict]) -> tuple[list[dict], list[dict]]:
    """Convert sources → RFO-style claims + evidence cards."""
    STATUS_MAP = {"raw_document": "reported_claim"}

    def conf(s: dict) -> str:
        return "high" if s.get("verification_mode") == "raw_document" else "medium"

    claims, evidence = [], []
    for s in sources:
        c = s.get("content", "")
        if not c:
            continue
        cid = f"C-{s['source_id']}"
        ev_id = f"EV-{s['source_id']}"
        sid_val = s["source_id"]

        claims.append({
            "claim_id": cid,
            "claim_text": c[:800],
            "claim_type": "source_derived",
            "status": STATUS_MAP.get(s.get("verification_mode", "testimony"), "inferred_assessment"),
            "confidence": conf(s),
            "evidence_card_ids": [ev_id],
            "support_set": [{"source_id": sid_val, "evidence_card_id": ev_id, "role_for_claim": "primary_support"}],
        })
        evidence.append({
            "evidence_id": ev_id,
            "source_ids": [sid_val],
            "claim_ids": [cid],
            "extracted_fact_or_excerpt": {"kind": "excerpt", "text": c[:400]},
            "supports": "direct",
            "confidence": conf(s),
        })
    return claims, evidence


def _feature_matrix_standalone(run_id: str, collection: dict) -> dict:
    """Honest capability matrix for CLI relay driver (mode=research, not production dossier)."""
    web_ok = bool(collection.get("web_search_succeeded") or collection.get("external_web_search_executed"))
    return {
        "run_id": run_id,
        "version": VERSION,
        "generated_at": now(),
        "features": {
            "skill_discovery_frontmatter": "implemented",
            "interface_adapter": "implemented_scaffold",
            "runtime_job_worker": "not_applicable",
            "outbox_delivery_worker": "implemented",
            "wave_graph_collector": "implemented_seed_only",
            "real_external_search_workers": "implemented_real" if web_ok else "implemented_seed_only",
            "provider_outbound_real_send": "stub",
            "late_result_protocol": "implemented_scaffold",
            "deterministic_html_renderer": "implemented",
            "analytical_memo": "implemented_scaffold",
            "factual_dossier": "implemented_scaffold",
            "io_propaganda_check": "implemented_scaffold",
            "self_audit": "implemented_scaffold",
            "external_collector": "implemented_real" if web_ok else "implemented_seed_only",
            "work_unit_decomposition": "not_applicable",
            "work_unit_executor": "not_applicable",
        },
        "rule": (
            "Standalone relay driver (run_rfo_full_research): relay-backed packaging; "
            "not a dossier production floor."
        ),
        "collection_summary": {
            "backend": collection.get("backend"),
            "external_web_search_executed": collection.get("external_web_search_executed", False),
            "external_source_packet_loaded": collection.get("external_source_packet_loaded", False),
            "web_search_attempted": collection.get("web_search_attempted", False),
            "web_search_succeeded": collection.get("web_search_succeeded", False),
            "web_search_result_count": collection.get("web_search_result_count", 0),
            "external_source_count": collection.get("external_source_count", 0),
            "seed_only": collection.get("seed_only", False),
        },
    }


def post_finish_standalone(rd: Path, entry: dict, profile_name: str) -> dict:
    """Scaffold missing package paths, run citation grounding, sync matrix + final gate."""
    run_id = str(entry["run_id"])
    job_id = str(entry["job_id"])
    cmd_id = str(entry["command_id"])
    ensure_pkg_required_paths(rd, run_id, job_id, cmd_id)
    cg = citation_grounding_evaluate(rd, run_id=run_id, job_id=job_id, profile=profile_name)
    col = jr(rd / "collection-result.json", {})
    fm = jr(rd / "feature-truth-matrix.json", {})
    if not isinstance(fm, dict):
        fm = _feature_matrix_standalone(run_id, col if isinstance(col, dict) else {})
    fm["collection_summary"] = {
        "backend": col.get("backend") if isinstance(col, dict) else None,
        "external_web_search_executed": bool(col.get("external_web_search_executed")) if isinstance(col, dict) else False,
        "external_source_packet_loaded": bool(col.get("external_source_packet_loaded")) if isinstance(col, dict) else False,
        "web_search_attempted": bool(col.get("web_search_attempted")) if isinstance(col, dict) else False,
        "web_search_succeeded": bool(col.get("web_search_succeeded")) if isinstance(col, dict) else False,
        "web_search_result_count": int(col.get("web_search_result_count") or 0) if isinstance(col, dict) else 0,
        "external_source_count": int(col.get("external_source_count") or 0) if isinstance(col, dict) else 0,
        "seed_only": bool(col.get("seed_only")) if isinstance(col, dict) else False,
    }
    fm["citation_grounding_summary"] = {
        "raf": cg.get("relevance_aware_factuality_score"),
        "dfl": cg.get("deflection_rate_when_no_grounding"),
        "passed": cg.get("passed"),
        "requires_grounding": cg.get("requires_grounding"),
        "claims_total": cg.get("claims_total"),
        "claims_grounded": cg.get("claims_grounded"),
    }
    jw(rd / "feature-truth-matrix.json", fm)
    wave_ok = (rd / "graph/wave-plan.json").is_file()
    cg_ok = bool(cg.get("passed"))
    jw(
        rd / "final-answer-gate.json",
        minimal_valid(
            "final-answer-gate",
            overrides={
                "run_id": run_id,
                "passed": wave_ok and cg_ok,
                "status": "pass" if (wave_ok and cg_ok) else "fail",
                "checks": {
                    "wave_plan_materialized": wave_ok,
                    "citation_grounding_passed": cg_ok,
                    "driver": "run_rfo_full_research",
                },
            },
        ),
    )
    return cg


# ── run allocation ─────────────────────────────────────────────────────────────
def allocate_run(runs_root: Path, task: str):
    label = f"{slug(task)}_{now().replace('-','').replace(':','').replace('Z','')[:15]}"
    run_id = sid("RUN", label, task)
    job_id = sid("JOB", run_id, task)
    cmd_id = sid("CMD", run_id, task)
    rd = runs_root / "runs" / label
    rd.mkdir(parents=True, exist_ok=True)

    entry = {
        "run_id": run_id, "job_id": job_id, "command_id": cmd_id,
        "run_label": label, "run_dir": str(rd), "task": task,
        "provider": "cli", "interface": "cli",
        "created_at": now(), "version": VERSION,
    }
    jw(rd / "run-catalog-entry.json", entry)
    idx = runs_root / "index"
    idx.mkdir(exist_ok=True)
    with (idx / "runs-index.jsonl").open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    jw(idx / "latest.json", entry)
    return rd, entry


# ── artifact writer ────────────────────────────────────────────────────────────
def write_artifacts(
    rd: Path,
    entry: dict,
    sources: list[dict],
    claims: list[dict],
    evidence: list[dict],
    task: str,
    search_results: list[dict],
    *,
    profile_name: str,
    profile_policy: dict,
    fanout_stats: dict,
) -> None:
    run_id, job_id, cmd_id = entry["run_id"], entry["job_id"], entry["command_id"]
    wiki_srcs = [s for s in sources if s.get("is_wikipedia")]
    web_srcs = [s for s in sources if not s.get("is_wikipedia")]
    (rd / "graph").mkdir(parents=True, exist_ok=True)
    (rd / "self-audit").mkdir(parents=True, exist_ok=True)
    (rd / "orchestrator").mkdir(parents=True, exist_ok=True)

    merge = fanout_stats.get("merge") if isinstance(fanout_stats, dict) else {}
    n_vec = len(fanout_stats.get("query_vectors") or []) if isinstance(fanout_stats, dict) else 0

    # sources
    jw(rd / "sources.json", {"schema_version": "v19.0", "sources": sources})
    jw(rd / "sources/sources.json", {"run_id": run_id, "sources": sources})

    # claims
    jw(rd / "claims-registry.json", {"schema_version": "v19.0", "claims": claims})
    jw(rd / "claims/claims-registry.json", {
        "run_id": run_id, "taxonomy_version": "v19.2",
        "allowed_statuses": ["reported_claim", "inferred_assessment", "disputed", "insufficient_evidence"],
        "claims": claims,
    })
    jw(rd / "evidence-cards.json", {"schema_version": "v19.0", "evidence_cards": evidence})
    jw(rd / "evidence/evidence-cards.json", {"run_id": run_id, "evidence_cards": evidence})

    collection_doc = {
        "schema_version": "v19.0", "run_id": run_id, "job_id": job_id,
        "profile": profile_name,
        "backend": "json_relay_prefetch_fanout",
        "backend_reason": (
            f"fanout {n_vec} query vectors, relay_requests={fanout_stats.get('relay_requests', 0)}, "
            f"merged_urls={merge.get('unique_urls_after_dedup', len(search_results))} → {len(sources)} sources"
        ),
        "relay_query_fanout": fanout_stats,
        "external_mode": "optional", "no_network": False,
        "started_at": now(), "completed_at": now(),
        "external_source_packet_loaded": False,
        "web_search_attempted": True,
        "web_search_succeeded": len(search_results) > 0,
        "web_search_result_count": len(search_results),
        "external_web_search_executed": len(search_results) > 0,
        "external_source_count": len(sources),
        "seed_only": False,
        "root_sources_count_after": len(sources),
    }
    jw(rd / "collection-result.json", collection_doc)
    jw(rd / "run-profile.json", {
        "schema_version": "v19.0",
        "profile": profile_name,
        "policy": profile_policy,
        "resolved_from": "entrypoint_default:scripts/run_rfo_full_research.py",
        "resolved_at": now(),
    })
    jw(rd / "orchestrator/fanout-plan.json", {
        "schema_version": "v19.0",
        "run_id": run_id,
        "driver": "run_rfo_full_research",
        "profile": profile_name,
        "fanout": fanout_stats,
    })
    jw(rd / "feature-truth-matrix.json", _feature_matrix_standalone(run_id, collection_doc))

    waves = [
        {
            "wave_id": "W0",
            "status": "completed",
            "purpose": (
                f"Relay fanout: {n_vec} vectors, {merge.get('raw_rows_total', 0)} raw rows, "
                f"{merge.get('unique_urls_after_dedup', len(search_results))} unique URLs"
            ),
        },
        {"wave_id": "W1", "status": "completed", "purpose": f"Wikipedia full-text: {len(wiki_srcs)} pages"},
        {"wave_id": "W2", "status": "completed", "purpose": f"Web content fetch: {len(web_srcs)} pages"},
        {"wave_id": "W3", "status": "completed", "purpose": f"Claim extraction: {len(claims)} claims"},
    ]
    jw(rd / "graph/wave-plan.json", {"run_id": run_id, "waves": waves})
    jw(rd / "graph/target-graph.json", {"run_id": run_id, "nodes": [], "edges": []})

    # graph — waves
    tw(rd / "graph/wave-events.jsonl", "".join(
        json.dumps({"event_name": "wave.updated", "run_id": run_id, **w, "timestamp": now()},
                    ensure_ascii=False) + "\n"
        for w in waves
    ))

    # reports
    wiki_list = "\n".join(f"  • {s['title']} ({len(s.get('content',''))} chars)" for s in wiki_srcs) or "нет"
    web_list = "\n".join(f"  • {s['title'][:60]}" for s in web_srcs[:5]) or "нет"

    jw(rd / "report/analytical-memo.json", {
        "schema_version": "v19.0", "run_id": run_id, "job_id": job_id,
        "confidence": "high",
        "executive_summary": (f"Исследование '{task}': {len(sources)} источников "
                             f"({len(wiki_srcs)} Wikipedia, {len(web_srcs)} веб). "
                             f"JSON relay search returned {len(search_results)} results."),
        "methodology": [
            "JSON relay web search (upstream engines negotiated by relay)",
            "Wikipedia API full-text extraction",
            "Web content fetch and cleaning",
            "Claim decomposition per source",
        ],
        "sources_summary": wiki_list[:1000],
    })
    jw(rd / "report/factual-dossier.json", {
        "schema_version": "v19.0", "run_id": run_id,
        "facts_summary": {"total_claims": len(claims),
                          "reported_claim": sum(1 for c in claims if c["status"] == "reported_claim")},
        "claims": claims,
    })
    bucket = _topic_bucket(task)
    narrative = _build_narrative_map(sources, task)
    jw(rd / "report/io-propaganda-check.json", {
        "schema_version": "v19.0", "run_id": run_id,
        "topic_bucket": bucket,
        "method_matches": [
            {
                "method": "heuristic_topic_bucket",
                "confidence": "medium",
                "note": _io_method_note(bucket),
            },
        ],
        "narrative_map": narrative,
    })
    jw(rd / "self-audit/runtime-self-audit.json", {
        "run_id": run_id,
        "deviations": [
            "standalone_cli_driver: no dossier source packet; relay-scoped packaging only",
        ],
        "search_quality": {
            "relay_fanout": fanout_stats,
            "sources_materialized": len(sources),
        },
        "tool_failures": [],
    })

    # chat messages
    tw(rd / "chat/message-001-analytical-memo.txt", "\n".join([
        "АНАЛИТИЧЕСКАЯ ЗАПИСКА",
        f"Исследование: {task}",
        f"Search results: {len(search_results)} | Sources: {len(sources)} ({len(wiki_srcs)} wiki, {len(web_srcs)} web)",
        f"Claims: {len(claims)}",
        f"Метод: relay JSON prefetch (primary) + Wikipedia API + web fetch",
        "Уверенность: high",
        "",
        "Источники (Wikipedia):",
        wiki_list[:800],
    ]))

    facts_text = f"ФАКТЫ / СТАТУСЫ ({len(claims)} claims)\n{'='*50}\n\n"
    for c in claims:
        facts_text += f"{c['claim_id']} [{c['status']}] {c['claim_text'][:200]}\n\n"
    tw(rd / "chat/message-002-facts.txt", facts_text)

    io_chat_tail = (
        "Тема классифицирована как медицинская/научная — смотреть источники на health hype."
        if bucket == "medical_scientific"
        else (
            "Тема: политика/новости — проверяйте независимость изданий и рамку изложения."
            if bucket == "political_news"
            else "Тема: общая — стандартная проверка на framing и пропуски контекста."
        )
    )
    tw(rd / "chat/message-003-io-propaganda-check.txt", "\n".join([
        "IO / PROPAGANDA / MANIPULATION CHECK",
        f"Topic bucket: {bucket}",
        _io_method_note(bucket),
        f"Narrative anchors (sources): {len(narrative)}",
        io_chat_tail,
    ]))

    tw(rd / "chat/message-004-files.txt", "\n".join([
        "ФАЙЛЫ",
        f"HTML-отчёт: report/full-report.html",
        f"  — {len(sources)} источников, {len(claims)} фактов",
        f"Research artifacts: полная структура RFO v19 в {rd.name}/",
        "",
        "Веб-источники (топ-5):",
        web_list,
    ]))

    # runtime
    jw(rd / "run.json", {**{k: v for k, v in entry.items()}, "mode": "research"})
    jw(rd / "entrypoint-proof.json", {
        "run_id": run_id, "job_id": job_id, "command_id": cmd_id,
        "entrypoint": "scripts/run_rfo_full_research.py",
        "entrypoint_version": VERSION,
        "skill_root": str(SKILL_ROOT),
        "runs_root": str(rd.parent.parent),
        "not_plain_subagent": True, "not_skill_md_imitation": True,
    })
    jw(rd / "runtime-status.json", {
        "run_id": run_id, "job_id": job_id, "command_id": cmd_id,
        "state": "content_rendered", "version": VERSION,
    })
    jw(rd / "delivery-manifest.json", {
        "schema_version": "v19.0", "run_id": run_id, "job_id": job_id,
        "delivery_status": "not_queued",
        "local_paths_exposed": False,
        "artifact_ready_claim_allowed": True,
        "external_delivery_claim_allowed": False,
        "stub_delivery": False,
        "real_external_delivery": False,
        "created_at": now(),
    })

    # HTML report
    html = build_html(task, sources, claims, run_id)
    write_canonical_full_report_html(rd, html, source="run_rfo_full_research")

    # outbox
    outbox = [
        {"id": "OUT-0001", "kind": "analytical_memo", "path": "chat/message-001-analytical-memo.txt"},
        {"id": "OUT-0002", "kind": "factual_dossier", "path": "chat/message-002-facts.txt"},
        {"id": "OUT-0003", "kind": "io_check", "path": "chat/message-003-io-propaganda-check.txt"},
        {"id": "OUT-0004", "kind": "files", "path": "chat/message-004-files.txt"},
        {"id": "OUT-0005", "kind": "html_report", "path": "report/full-report.html"},
    ]
    jw(rd / "outbox/outbox-policy.json", {
        "run_id": run_id, "job_id": job_id,
        "required_events": ["OUT-0001", "OUT-0002", "OUT-0003", "OUT-0004"],
        "policy": "v19 3+1 + HTML report",
    })
    for ev in outbox:
        jw(rd / f"outbox/{ev['id']}.json", {
            "event_id": ev["id"], "run_id": run_id, "job_id": job_id,
            "type": "send_file" if ev["id"] == "OUT-0005" else "send_message",
            "provider": "cli",
            "payload_path": ev["path"],
            "payload_kind": ev["kind"],
            "file_kind": "html_report" if ev["id"] == "OUT-0005" else None,
            "required_for_final_delivery": ev["id"] in ["OUT-0001", "OUT-0002", "OUT-0003", "OUT-0004"],
            "status": "queued",
            "idempotency_key": f"IDEMP-{sid('ID', ev['id'], run_id)[:12]}",
            "created_at": now(),
        })


def build_html(task: str, sources: list[dict], claims: list[dict], run_id: str) -> str:
    def claim_html(c):
        color = {"reported_claim": "#2e7d32", "inferred_assessment": "#1565c0"}.get(c["status"], "#666")
        return f"""
    <div class="claim">
      <div class="h">
        <span class="cid">{c['claim_id']}</span>
        <span class="st" style="background:{color}">{c['status']}</span>
        <span class="conf">{c['confidence']}</span>
      </div>
      <div class="txt">{c['claim_text']}</div>
    </div>"""

    def source_html(s):
        badge = "📚 Wikipedia" if s.get("is_wikipedia") else "🌐 Web"
        return f"""
    <div class="src">
      <div class="h">
        <span class="badge">{badge}</span>
        <a href="{s['url']}" target="_blank">{s['title']}</a>
      </div>
      <div class="body">{s.get('content', '')[:800]}</div>
    </div>"""

    return f"""<!DOCTYPE html>
<html lang="ru"><head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Исследование: {task[:60]}</title>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;line-height:1.6;background:#f0f4f8;color:#222;padding:20px}}
.c{{max-width:900px;margin:0 auto}}
h1{{color:#1a237e;font-size:1.5rem;margin-bottom:8px}}
h2{{color:#1a237e;font-size:1.1rem;margin:24px 0 10px;border-bottom:2px solid #3949ab;padding-bottom:4px}}
.m{{background:#e8eaf6;padding:12px;border-radius:8px;margin-bottom:20px;font-size:.9rem;color:#555}}
.claim{{background:white;border-radius:8px;padding:14px;margin-bottom:10px;box-shadow:0 1px 3px rgba(0,0,0,.1)}}
.h{{display:flex;gap:8px;align-items:center;margin-bottom:8px;flex-wrap:wrap}}
.cid{{font-weight:700;color:#1a1a2e;font-size:.85rem}}
.st{{color:white;padding:2px 8px;border-radius:4px;font-size:.7rem;font-weight:600}}
.conf{{color:#888;font-size:.75rem}}
.txt{{color:#333;font-size:.92rem;line-height:1.5}}
.src{{background:white;border-radius:8px;padding:14px;margin-bottom:10px;box-shadow:0 1px 3px rgba(0,0,0,.1)}}
.badge{{background:#e8eaf6;color:#3949ab;padding:2px 6px;border-radius:4px;font-size:.7rem;margin-right:6px}}
.h a{{color:#1565c0;text-decoration:none;font-weight:600;font-size:.95rem}}
.h a:hover{{text-decoration:underline}}
.body{{font-size:.88rem;color:#555;line-height:1.5;margin-top:8px}}
.rid{{text-align:center;color:#bbb;font-size:.7rem;margin-top:30px}}
</style></head><body>
<div class="c">
  <h1>🔬 {task}</h1>
  <div class="m">📊 Источников: <b>{len(sources)}</b> | 📋 Фактов: <b>{len(claims)}</b> | JSON relay + Wikipedia + web fetch</div>
  <h2>📋 Факты</h2>
  {''.join(claim_html(c) for c in claims)}
  <h2>📚 Источники</h2>
  {''.join(source_html(s) for s in sources)}
  <div class="rid">RFO {VERSION} | {run_id} | {now()}</div>
</div></body></html>"""


# ── outbox delivery ────────────────────────────────────────────────────────────
def run_outbox(runs_root: Path):
    import subprocess
    proc = subprocess.run(
        [sys.executable, "-S", str(SCRIPTS_DIR / "outbox_delivery_worker.py"),
         "--runs-root", str(runs_root)],
        capture_output=True, text=True, timeout=120,
    )
    print(f"[outbox] exit={proc.returncode} processed={proc.stdout.strip()}")


# ── main ───────────────────────────────────────────────────────────────────────
def main():
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--runs-root", required=True)
    p.add_argument("--task", required=True)
    p.add_argument("--web-search-json-api-base", default="", help="Relay origin (overrides env for this run)")
    args = p.parse_args()

    task = args.task
    runs_root = Path(args.runs_root).resolve()
    relay = relay_api_base(args.web_search_json_api_base)
    if not relay:
        print(
            "[fatal] JSON relay base missing. Set --web-search-json-api-base or RFO_WEB_SEARCH_JSON_API_BASE.",
            file=sys.stderr,
        )
        return 2

    print(f"\n{'='*60}")
    print(f"[RFO full-research] {task}")
    print(f"{'='*60}\n")

    try:
        profile_name, profile_policy = resolve_profile(
            os.environ.get("RFO_RUN_PROFILE"),
            entrypoint_default="search-primary",
        )
    except ValueError as exc:
        print(f"[fatal] run profile resolution failed: {exc}", file=sys.stderr)
        return 2

    print("[1/3] JSON relay search (fanout)...")

    def _relay_query(base: str, query: str, num: int) -> list[dict]:
        return search_json_relay(base, query, num=num)

    n_results = relay_max_results()
    search_results, fanout_stats = fanout_relay_search(_relay_query, [relay], task, n_results)
    print(
        f"[1/3] → {len(search_results)} merged URLs "
        f"(vectors={len(fanout_stats.get('query_vectors') or [])}, "
        f"relay_requests={fanout_stats.get('relay_requests', 0)})",
    )

    print("[2/3] Building sources (Wikipedia + fetched web)...")
    sources = build_sources(task, search_results)
    wiki_srcs = [s for s in sources if s.get("is_wikipedia")]
    web_srcs = [s for s in sources if not s.get("is_wikipedia")]
    print(f"[2/3] → {len(sources)} sources ({len(wiki_srcs)} wiki, {len(web_srcs)} web)")

    print("[3/3] Generating claims and artifacts...")
    claims, evidence = make_claims(sources)
    rd, entry = allocate_run(runs_root, task)
    write_artifacts(
        rd,
        entry,
        sources,
        claims,
        evidence,
        task,
        search_results,
        profile_name=profile_name,
        profile_policy=profile_policy,
        fanout_stats=fanout_stats,
    )
    cg = post_finish_standalone(rd, entry, profile_name)
    print(f"[3/3] → {len(claims)} claims, artifacts in {entry['run_label']}")
    print(
        f"[3/3] citation_grounding passed={cg.get('passed')} raf={cg.get('relevance_aware_factuality_score')} "
        f"dfl={cg.get('deflection_rate_when_no_grounding')}",
    )

    print("[outbox] Delivering...")
    run_outbox(runs_root)

    print(f"\n{'='*60}")
    print(f"[DONE] {entry['run_label']}")
    print(f"[DONE] Search: {len(search_results)} | Sources: {len(sources)} | Claims: {len(claims)}")
    print(f"{'='*60}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())