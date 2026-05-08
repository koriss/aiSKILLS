#!/usr/bin/env python3
"""Render a non-placeholder, artifact-backed standalone HTML report (v19)."""
from pathlib import Path
import argparse
import html
import json
from datetime import datetime, timezone


RENDERER_VERSION = "19.3.0-report-proof-runtime"


def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def jread(path: Path, default=None):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def jwrite(path: Path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def safe_json_for_script(obj):
    return json.dumps(obj if obj is not None else {}, ensure_ascii=False, indent=2).replace("</", "<\\/")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", required=True)
    args = ap.parse_args()
    run_dir = Path(args.run_dir)

    run = jread(run_dir / "run.json", {})
    runtime = jread(run_dir / "runtime-status.json", {})
    entrypoint = jread(run_dir / "entrypoint-proof.json", {})
    artifact = jread(run_dir / "artifact-manifest.json", {})
    provenance = jread(run_dir / "provenance-manifest.json", {})
    validation = jread(run_dir / "validation-transcript.json", {})
    delivery = jread(run_dir / "delivery-manifest.json", {})
    gate = jread(run_dir / "final-answer-gate.json", {})
    claims = jread(run_dir / "claims/claims-registry.json", {})
    evidence = jread(run_dir / "evidence/evidence-cards.json", {})
    sources = jread(run_dir / "sources/sources.json", {"sources": []})

    required = {
        "run.json": bool(run),
        "runtime-status.json": bool(runtime),
        "entrypoint-proof.json": bool(entrypoint),
        "delivery-manifest.json": bool(delivery),
        "final-answer-gate.json": bool(gate),
        "claims/claims-registry.json": (run_dir / "claims/claims-registry.json").exists(),
        "evidence/evidence-cards.json": (run_dir / "evidence/evidence-cards.json").exists(),
    }
    missing = [k for k, v in required.items() if not v]
    if missing:
        raise SystemExit("cannot render HTML; missing required artifacts: " + ", ".join(missing))

    run_id = run.get("run_id") or runtime.get("run_id") or "UNKNOWN-RUN"
    job_id = run.get("job_id") or runtime.get("job_id") or "UNKNOWN-JOB"

    claim_count = len(claims.get("claims", [])) if isinstance(claims, dict) else 0
    evidence_count = len(evidence.get("evidence_cards", [])) if isinstance(evidence, dict) else 0
    source_count = len(sources.get("sources", [])) if isinstance(sources, dict) else 0
    checks = gate.get("checks", {}) if isinstance(gate, dict) and isinstance(gate.get("checks"), dict) else {}

    semantic = {
        "renderer_version": RENDERER_VERSION,
        "report_type": "runtime_proof_integrity_report",
        "run_id": run_id,
        "job_id": job_id,
        "topic": run.get("topic"),
        "claim_count": claim_count,
        "evidence_count": evidence_count,
        "source_count": source_count,
        "generated_at": now(),
        "note": "v19 renderer: artifact-backed runtime proof report.",
    }
    jwrite(run_dir / "report/semantic-report.json", semantic)

    esc = lambda x: html.escape("" if x is None else str(x))
    sections = [
        f"""<section><h2>1. Run metadata</h2>
<table><tr><th>Field</th><th>Value</th></tr>
<tr><td>run_id</td><td>{esc(run_id)}</td></tr>
<tr><td>job_id</td><td>{esc(job_id)}</td></tr>
<tr><td>renderer_version</td><td>{esc(RENDERER_VERSION)}</td></tr></table></section>""",
        f"""<section><h2>2. Content status</h2>
<table><tr><th>Artifact</th><th>Count/state</th></tr>
<tr><td>claims-registry</td><td>{claim_count}</td></tr>
<tr><td>evidence-cards</td><td>{evidence_count}</td></tr>
<tr><td>sources</td><td>{source_count}</td></tr>
<tr><td>validation status</td><td>{esc(validation.get("status"))}</td></tr></table></section>""",
        f"""<section><h2>3. Delivery proof</h2>
<table><tr><th>Field</th><th>Value</th></tr>
<tr><td>delivery_status</td><td>{esc(delivery.get("delivery_status"))}</td></tr>
<tr><td>provider_ack_gate</td><td>{esc((checks.get("provider_ack_gate") or {}).get("status"))}</td></tr>
<tr><td>external_delivery_gate</td><td>{esc((checks.get("external_delivery_gate") or {}).get("status"))}</td></tr>
<tr><td>final_user_claim_gate</td><td>{esc((checks.get("final_user_claim_gate") or {}).get("status"))}</td></tr>
<tr><td>final-answer-gate passed</td><td>{esc(gate.get("passed"))}</td></tr></table></section>""",
    ]

    proof_blocks = {
        "semantic-report-json": semantic,
        "artifact-manifest-json": artifact,
        "provenance-manifest-json": provenance,
        "validation-transcript-json": validation,
        "delivery-manifest-json": delivery,
        "runtime-status-json": runtime,
        "entrypoint-proof-json": entrypoint,
        "final-answer-gate-json": gate,
    }
    scripts = "\n".join(
        f'<script type="application/json" id="{sid}">{safe_json_for_script(obj)}</script>'
        for sid, obj in proof_blocks.items()
    )
    html_doc = f"""<!doctype html>
<html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Research Factory Orchestrator Report - {esc(run_id)}</title></head>
<body><main>
<header><h1>Research Factory Orchestrator Report - {esc(run_id)}</h1><p>Generated at {esc(semantic["generated_at"])}</p></header>
{''.join(sections)}
<section><h2>4. Embedded proof blocks</h2>{scripts}</section>
</main></body></html>"""

    out = run_dir / "report/full-report.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html_doc, encoding="utf-8")
    print(json.dumps({"rendered": True, "run_id": run_id, "path": "report/full-report.html", "renderer_version": RENDERER_VERSION}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
