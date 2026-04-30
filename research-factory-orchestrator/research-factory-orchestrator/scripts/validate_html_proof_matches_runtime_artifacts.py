#!/usr/bin/env python3
from pathlib import Path
import argparse, json, re

BLOCK_TO_FILE = {
    "runtime-status-json": "runtime-status.json",
    "entrypoint-proof-json": "entrypoint-proof.json",
    "delivery-manifest-json": "delivery-manifest.json",
    "final-answer-gate-json": "final-answer-gate.json",
    "validation-transcript-json": "validation-transcript.json",
    "artifact-manifest-json": "artifact-manifest.json",
    "provenance-manifest-json": "provenance-manifest.json",
    "semantic-report-json": "report/semantic-report.json",
}

RUNTIME_CLAIM_RE = re.compile(r"Research Factory Orchestrator|runtime_version|runtime-status-json|entrypoint-proof-json|validation_completed|claims_registry_generated|evidence_cards_generated", re.I)

def extract(text):
    out={}
    for m in re.finditer(r'<script[^>]+type=["\']application/json["\'][^>]*id=["\']([^"\']+)["\'][^>]*>(.*?)</script>', text, re.I|re.S):
        try:
            out[m.group(1)] = json.loads(m.group(2).strip() or "{}")
        except Exception as e:
            out[m.group(1)] = {"__parse_error__": str(e)}
    return out

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("path"); args=ap.parse_args()
    p=Path(args.path)
    errors=[]
    if p.is_dir():
        run_dir=p
        html_path=run_dir/"report"/"full-report.html"
        if not html_path.exists():
            errors.append(f"missing HTML {html_path}")
        else:
            text=html_path.read_text(encoding="utf-8", errors="replace")
            blocks=extract(text)
            for sid, rel in BLOCK_TO_FILE.items():
                file_path=run_dir/rel
                if sid not in blocks:
                    errors.append(f"HTML missing proof block {sid}")
                    continue
                if not file_path.exists():
                    errors.append(f"HTML proof block {sid} has no backing artifact {rel}")
                    continue
                try:
                    disk=json.loads(file_path.read_text(encoding="utf-8"))
                except Exception as e:
                    errors.append(f"backing artifact {rel} is invalid JSON: {e}")
                    continue
                if sid == "validation-transcript-json":
                    # The validator DAG writes validation-transcript.json after HTML has already been rendered.
                    # Require backing artifact + parseable non-empty block, but do not require byte-for-byte equality here.
                    if not isinstance(blocks[sid], dict):
                        errors.append(f"HTML proof block {sid} is not an object")
                elif blocks[sid] != disk:
                    errors.append(f"HTML proof block {sid} does not match {rel}")
            runtime = blocks.get("runtime-status-json", {})
            entrypoint = blocks.get("entrypoint-proof-json", {})
            if runtime.get("run_id") and entrypoint.get("run_id") and runtime.get("run_id") != entrypoint.get("run_id"):
                errors.append("runtime-status-json run_id differs from entrypoint-proof-json")
    else:
        if not p.exists():
            errors.append(f"missing file {p}")
        else:
            text=p.read_text(encoding="utf-8", errors="replace")
            blocks=extract(text)
            if RUNTIME_CLAIM_RE.search(text):
                # A standalone HTML may be a useful article, but it cannot self-certify RFO runtime proof.
                # It passes only if it contains no RFO/proof claims.
                errors.append("standalone HTML contains runtime/proof claims but no run-dir artifacts to verify them")
            for sid, obj in blocks.items():
                if isinstance(obj, dict) and obj.get("__parse_error__"):
                    errors.append(f"invalid JSON block {sid}: {obj['__parse_error__']}")
    print(json.dumps({"status":"pass" if not errors else "fail","errors":errors}, ensure_ascii=False, indent=2))
    return 0 if not errors else 1
if __name__=="__main__":
    raise SystemExit(main())
