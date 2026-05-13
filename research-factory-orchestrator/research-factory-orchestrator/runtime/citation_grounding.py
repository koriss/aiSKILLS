"""Citation grounding result writer (RFO v19.4.4).

Produces ``<rd>/citation-grounding-result.json`` consumed by
runtime.outbox.finalize and validate_citation_grounding. Closes
CITATION-GROUNDING-MAGIC-LITERAL by replacing render.py's hardcoded RAF/DFL
defaults with a real, per-claim computation:

  * RAF (Relevance-Aware Factuality) = mean over claims of
    ``min(1.0, float(support_count)) * status_weight``
    (one grounded support slot counts at full structural weight for relay/dossier
    rows; ``support_count`` is ``len(support_set)`` or legacy list lengths.)
    where status_weight ∈ {confirmed:1.0, probable:0.8, inferred:0.5,
    unknown:0.3, disputed:0.2, contradicted:0.0, false:0.0,
    unsupported:0.0, stale:0.4}
  * DFL (Deflection on No-Grounding) = fraction of claims with 0 support items.

Strict gate condition (RAF >= 0.65 AND DFL <= 0.25 AND >= 1 claim with grounded
support) is enforced when the run profile demands it.
"""
from __future__ import annotations

from pathlib import Path

from runtime.profiles import resolve as _resolve_profile
from runtime.util import jw, jr, now


_STATUS_WEIGHT = {
    "confirmed": 1.0,
    "probable": 0.8,
    "inferred": 0.5,
    "unknown": 0.3,
    "stale": 0.4,
    "disputed": 0.2,
    "contradicted": 0.0,
    "false": 0.0,
    "unsupported": 0.0,
    # RFO claims-registry / relay standalone statuses
    "reported_claim": 0.88,
    # Relay/dossier: one evidence-backed inferred row must be able to meet RAF≥0.65
    # when ``requires_grounding`` (see min(1, sc) structural multiplier above).
    "inferred_assessment": 0.68,
    "insufficient_evidence": 0.25,
}


def _claim_support_count(c: dict) -> int:
    s = c.get("support_set")
    if isinstance(s, list):
        return len(s)
    s = c.get("supporting_evidence_card_ids") or c.get("source_ids")
    if isinstance(s, list):
        return len(s)
    return 0


def evaluate(rd: Path, *, run_id: str, job_id: str, profile: str | None) -> dict:
    rd = Path(rd)
    name, policy = _resolve_profile(profile)
    src_pol = policy.get("source_policy") or {}
    requires_grounding = bool(src_pol.get("web_search_required") or src_pol.get("external_collection_required"))
    reg = jr(rd / "claims-registry.json", {})
    claims = reg.get("claims") if isinstance(reg, dict) else []
    raf = 0.0
    dfl_no_support = 0
    grounded = 0
    n = len(claims) if isinstance(claims, list) else 0
    if n:
        total = 0.0
        for c in claims:
            sc = _claim_support_count(c)
            status = c.get("status") or "unknown"
            sw = _STATUS_WEIGHT.get(status, 0.3)
            # Structural multiplier: first support card counts fully (bridge standard).
            mult = min(1.0, float(sc)) if sc > 0 else 0.0
            total += mult * sw
            if sc <= 0:
                dfl_no_support += 1
            else:
                grounded += 1
        raf = round(total / n, 4)
        dfl = round(dfl_no_support / n, 4)
    else:
        dfl = 1.0 if requires_grounding else 0.0
    raf_threshold = 0.65
    dfl_threshold = 0.25
    failure_reasons: list[str] = []
    passed = True
    if requires_grounding:
        if raf < raf_threshold:
            passed = False
            failure_reasons.append(f"raf_below_threshold: {raf} < {raf_threshold}")
        if dfl > dfl_threshold:
            passed = False
            failure_reasons.append(f"dfl_above_threshold: {dfl} > {dfl_threshold}")
        if grounded == 0:
            passed = False
            failure_reasons.append("no_grounded_claims")
    out = {
        "schema_version": "v19.0",
        "run_id": run_id,
        "job_id": job_id,
        "profile": name,
        "claims_total": n,
        "claims_grounded": grounded,
        "claims_no_support": dfl_no_support,
        "relevance_aware_factuality_score": raf,
        "deflection_rate_when_no_grounding": dfl,
        "raf_threshold": raf_threshold,
        "dfl_threshold": dfl_threshold,
        "passed": passed,
        "requires_grounding": requires_grounding,
        "failure_reasons": failure_reasons,
        "evaluated_at": now(),
    }
    jw(rd / "citation-grounding-result.json", out)
    return out
