"""Single loader for run-dir JSON/text inputs shared by MD and legacy HTML template renders."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from runtime.util import jr


def _first_existing(rd: Path, candidates: tuple[str, ...]) -> Path | None:
    for rel in candidates:
        p = rd / rel
        if p.is_file():
            return p
    return None


def minimal_report_sources_ready(rd: Path) -> tuple[bool, str]:
    """Return (ok, note) when core JSON exists for canonical dossier rebuild (root or nested layout)."""
    rd = Path(rd).resolve()
    if not (rd / "run.json").is_file():
        return False, "missing:run.json"
    checks = (
        ("claims-registry", ("claims-registry.json", "claims/claims-registry.json")),
        ("sources", ("sources.json", "sources/sources.json")),
        ("evidence-cards", ("evidence-cards.json", "evidence/evidence-cards.json")),
    )
    for label, cands in checks:
        if _first_existing(rd, cands) is None:
            return False, f"missing:{label}"
    return True, "ok"


@dataclass(frozen=True)
class ReportRunInputs:
    """Normalized snapshot of machine artifacts used to build full-report.md / HTML."""

    rd: Path
    run_meta: dict
    memo: dict
    factual: dict
    io: dict
    audit: dict
    claims: list
    sources: list
    evidence: list
    nodes: list
    edges: list
    waves: list
    task: str
    run_id: str
    job_id: str
    cmd_id: str
    provider: str
    user_visible_research: bool
    disclaimer: str

    @classmethod
    def from_run_dir(cls, rd: Path) -> ReportRunInputs:
        rd = Path(rd).resolve()
        run_meta = jr(rd / "run.json", {})
        if not isinstance(run_meta, dict):
            run_meta = {}

        memo = jr(rd / "report/analytical-memo.json", {})
        if not isinstance(memo, dict):
            memo = {}
        factual = jr(rd / "report/factual-dossier.json", {})
        if not isinstance(factual, dict):
            factual = {}
        io = jr(rd / "report/io-propaganda-check.json", {})
        if not isinstance(io, dict):
            io = {}
        audit = jr(rd / "self-audit/runtime-self-audit.json", {})
        if not isinstance(audit, dict):
            audit = {}

        cr_path = _first_existing(rd, ("claims-registry.json", "claims/claims-registry.json"))
        claims_data = jr(cr_path, {}) if cr_path else {}
        claims = claims_data.get("claims") if isinstance(claims_data, dict) else []
        if not isinstance(claims, list):
            claims = []

        src_path = _first_existing(rd, ("sources.json", "sources/sources.json"))
        src_data = jr(src_path, {}) if src_path else {}
        sources = src_data.get("sources") if isinstance(src_data, dict) else []
        if not isinstance(sources, list):
            sources = []

        ev_path = _first_existing(rd, ("evidence-cards.json", "evidence/evidence-cards.json"))
        ev_data = jr(ev_path, {}) if ev_path else {}
        evidence = ev_data.get("evidence_cards") if isinstance(ev_data, dict) else []
        if not isinstance(evidence, list):
            evidence = []

        graph = jr(rd / "graph/target-graph.json", {})
        nodes = graph.get("nodes") if isinstance(graph, dict) else []
        edges = graph.get("edges") if isinstance(graph, dict) else []
        if not isinstance(nodes, list):
            nodes = []
        if not isinstance(edges, list):
            edges = []

        wp = jr(rd / "graph/wave-plan.json", {})
        waves = wp.get("waves") if isinstance(wp, dict) else []
        if not isinstance(waves, list):
            waves = []

        run_id = str(run_meta.get("run_id") or "UNKNOWN")
        job_id = str(run_meta.get("job_id") or "UNKNOWN")
        cmd_id = str(run_meta.get("command_id") or run_meta.get("cmd_id") or "")
        task = str(run_meta.get("task") or "")
        provider = str(run_meta.get("provider") or "")

        external_source_count = sum(
            1
            for s in sources
            if isinstance(s, dict)
            and s.get("source_role") != "seed"
            and not str(s.get("source_id") or "").startswith("stub:")
        )
        user_visible_research = external_source_count > 0
        disclaimer = (
            "No external evidence collected; runtime structure only."
            if not user_visible_research
            else "External evidence present."
        )

        return cls(
            rd=rd,
            run_meta=run_meta,
            memo=memo,
            factual=factual,
            io=io,
            audit=audit,
            claims=claims,
            sources=sources,
            evidence=evidence,
            nodes=nodes,
            edges=edges,
            waves=waves,
            task=task,
            run_id=run_id,
            job_id=job_id,
            cmd_id=cmd_id,
            provider=provider,
            user_visible_research=user_visible_research,
            disclaimer=disclaimer,
        )
