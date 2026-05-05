#!/usr/bin/env python3
"""Cross-artifact logical consistency (v18.7): LC01–LC16. Stdlib only; JSON on stdout; rc=1 on violations."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load(p: Path) -> dict | list | None:
    if not p.is_file():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None


def _err(rule_id: str, severity: str, message: str, evidence: list) -> dict:
    return {"rule_id": rule_id, "severity": severity, "message": message, "evidence": evidence}


def _inv_lc01(rd: Path) -> list[dict]:
    out: list[dict] = []
    vt = _load(rd / "validation-transcript.json")
    if not isinstance(vt, dict):
        return out
    st = str(vt.get("status", "")).lower()
    if st != "fail":
        return out
    rs = _load(rd / "runtime-status.json") or {}
    dm = _load(rd / "delivery-manifest.json") or {}
    fg = _load(rd / "final-answer-gate.json") or {}
    if rs.get("state") != "validation_failed":
        out.append(_err("LC01", "critical", "validation fail must set runtime-status to validation_failed", ["runtime-status.json", str(rs.get("state"))]))
    ds = str(dm.get("delivery_status", "")).lower()
    # v19 rollback uses enum value ``validation_failed`` (schema); legacy LC01 expected ``failed`` only.
    if ds not in ("failed", "validation_failed"):
        out.append(
            _err(
                "LC01",
                "critical",
                "validation fail must set delivery-manifest delivery_status failed or validation_failed",
                ["delivery-manifest.json", ds],
            )
        )
    if fg.get("passed") is True:
        out.append(_err("LC01", "critical", "validation fail must set final-answer-gate.passed false", ["final-answer-gate.json"]))
    return out


def _inv_lc02(rd: Path) -> list[dict]:
    out: list[dict] = []
    run = _load(rd / "run.json") or {}
    if str(run.get("provider", "")).lower() != "cli":
        return out
    dm = _load(rd / "delivery-manifest.json") or {}
    if dm.get("real_external_delivery") is True:
        out.append(_err("LC02", "critical", "cli provider must have real_external_delivery false", ["run.json", "delivery-manifest.json"]))
    if dm.get("delivery_claim_allowed") is True:
        out.append(_err("LC02", "critical", "cli provider must have delivery_claim_allowed false", ["delivery-manifest.json"]))
    return out


def _inv_lc03(rd: Path) -> list[dict]:
    out: list[dict] = []
    dm = _load(rd / "delivery-manifest.json") or {}
    if dm.get("stub_delivery") is not True:
        return out
    if dm.get("real_external_delivery") is True:
        out.append(_err("LC03", "critical", "stub_delivery must force real_external_delivery false", ["delivery-manifest.json"]))
    if dm.get("publish_allowed") is True and not dm.get("external_delivery_ack"):
        out.append(_err("LC03", "high", "stub_delivery with publish_allowed true requires external_delivery_ack", ["delivery-manifest.json"]))
    return out


def _inv_lc04(rd: Path) -> list[dict]:
    out: list[dict] = []
    fg = _load(rd / "final-answer-gate.json") or {}
    if not fg.get("passed"):
        return out
    vt = _load(rd / "validation-transcript.json") or {}
    if str(vt.get("status", "")).lower() != "pass":
        out.append(_err("LC04", "critical", "final-answer-gate passed requires validation-transcript status pass", ["validation-transcript.json", "final-answer-gate.json"]))
    return out


def _inv_lc05(rd: Path) -> list[dict]:
    out: list[dict] = []
    wu = _load(rd / "work-queue/work-unit-ledger.json")
    if not isinstance(wu, dict):
        return out
    bad = False
    for row in wu.get("work_units") or []:
        st = str(row.get("status", "")).lower()
        if "timeout" in st or st in ("degraded", "partial_timeout", "failed"):
            bad = True
            break
    if not bad:
        return out
    fg = _load(rd / "final-answer-gate.json") or {}
    if fg.get("passed") is True:
        out.append(_err("LC05", "critical", "timeout/degraded work unit must not coexist with final-answer-gate passed", ["work-queue/work-unit-ledger.json", "final-answer-gate.json"]))
    return out


def _inv_lc06(report_path: Path | None, transcript_path: Path | None) -> list[dict]:
    out: list[dict] = []
    if not report_path or not report_path.is_file():
        return out
    text = report_path.read_text(encoding="utf-8", errors="replace").lower()
    if "pass" not in text and "claims_pass" not in text:
        return out
    if not transcript_path or not transcript_path.is_file():
        out.append(_err("LC06", "critical", "release report implies pass but release-validation-transcript missing", [str(report_path)]))
    return out


def _inv_lc07(transcript_path: Path | None) -> list[dict]:
    out: list[dict] = []
    if not transcript_path or not transcript_path.is_file():
        return out
    raw = json.loads(transcript_path.read_text(encoding="utf-8"))
    body = {k: v for k, v in raw.items() if k != "transcript_sha256"}
    want = hashlib.sha256(json.dumps(body, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()
    got = raw.get("transcript_sha256")
    if got and got != want:
        out.append(_err("LC07", "critical", "release-validation-transcript self-hash mismatch", [str(transcript_path)]))
    return out


def _inv_lc08(transcript_path: Path | None) -> list[dict]:
    out: list[dict] = []
    if not transcript_path or not transcript_path.is_file():
        return out
    raw = json.loads(transcript_path.read_text(encoding="utf-8"))
    seen: set[str] = set()
    dup: list[str] = []
    for step in raw.get("steps") or []:
        rid = step.get("run_id")
        if isinstance(rid, str) and rid:
            if rid in seen:
                dup.append(rid)
            seen.add(rid)
    if dup:
        out.append(_err("LC08", "high", "duplicate run_id in release transcript steps", dup))
    return out


def _inv_lc09(rd: Path) -> list[dict]:
    out: list[dict] = []
    run = _load(rd / "run.json") or {}
    mode = str(run.get("mode", "")).lower()
    req = str(run.get("requested_mode", "")).strip()
    if not req:
        return out
    if mode == req.lower():
        return out
    if "normalized_from" not in run or run.get("normalized_from") is None:
        out.append(_err("LC09", "critical", "mode differs from requested_mode but normalized_from missing", ["run.json"]))
    return out


def _inv_lc10(rd: Path) -> list[dict]:
    out: list[dict] = []
    pat = re.compile(r"(/tmp/|/home/|/opt/|/var/|/usr/|/root/|~/|[A-Z]:\\)", re.I)
    chat = rd / "chat"
    if not chat.is_dir():
        return out
    for p in sorted(chat.glob("message-*.txt")):
        t = p.read_text(encoding="utf-8", errors="replace")
        if pat.search(t):
            out.append(_err("LC10", "high", "chat payload contains forbidden local path prefix", [str(p)]))
    return out


def _inv_lc11(rd: Path) -> list[dict]:
    out: list[dict] = []
    required = [
        ("run.json", 2),
        ("delivery-manifest.json", 2),
        ("feature-truth-matrix.json", 10),
        ("report/full-report.html", 100),
    ]
    for rel, minb in required:
        p = rd / rel
        if not p.is_file():
            out.append(_err("LC11", "critical", "required artifact missing", [rel]))
            continue
        if p.stat().st_size < minb:
            out.append(_err("LC11", "high", "required artifact too small or empty", [rel, str(p.stat().st_size)]))
        if rel.endswith(".json"):
            try:
                o = json.loads(p.read_text(encoding="utf-8"))
                if o == {}:
                    out.append(_err("LC11", "high", "json artifact is empty object", [rel]))
            except Exception:
                out.append(_err("LC11", "critical", "json artifact not parseable", [rel]))
    return out


def _inv_lc12(rd: Path, skill_root: Path) -> list[dict]:
    out: list[dict] = []
    needles = ("without backup", "без backup")
    for p in [skill_root / "SKILL.md", skill_root / "runtime" / "operating-discipline.md"]:
        if p.is_file():
            low = p.read_text(encoding="utf-8", errors="replace").lower()
            for n in needles:
                if n in low:
                    out.append(_err("LC12", "medium", "forbidden legacy update phrase in active doc", [str(p), n]))
    return out


def _inv_lc13(rd: Path) -> list[dict]:
    out: list[dict] = []
    vt = _load(rd / "validation-transcript.json")
    if not isinstance(vt, dict):
        return out
    if str(vt.get("status", "")).lower() != "pass":
        return out
    if "validators_total" not in vt and "errors" not in vt:
        out.append(_err("LC13", "medium", "validation pass transcript lacks validators_total or errors field", ["validation-transcript.json"]))
    return out


def _inv_lc14(rd: Path) -> list[dict]:
    out: list[dict] = []
    html = rd / "report/full-report.html"
    if not html.is_file():
        return out
    txt = html.read_text(encoding="utf-8", errors="replace")
    m = re.search(r"sources_count[\"']?\s*[:=]\s*(\d+)", txt, re.I)
    if not m:
        return out
    declared = int(m.group(1))
    src = _load(rd / "sources/sources.json") or _load(rd / "sources.json")
    n = 0
    if isinstance(src, dict):
        n = len(src.get("sources", src.get("items", [])))
    if isinstance(src, list):
        n = len(src)
    if n and declared != n:
        out.append(_err("LC14", "medium", "report sources_count does not match sources artifact length", [str(declared), str(n)]))
    return out


def _inv_lc16(rd: Path) -> list[dict]:
    """Production runs must not mark critical features stub/missing in feature-truth-matrix (v18.7 F207)."""
    out: list[dict] = []
    run = _load(rd / "run.json") or {}
    if str(run.get("mode", "")).lower() != "production":
        return out
    ftm = _load(rd / "feature-truth-matrix.json")
    if not isinstance(ftm, dict):
        return out
    feats = ftm.get("features") or {}
    for k, v in feats.items():
        st = ""
        if isinstance(v, dict):
            st = str(v.get("status", "")).lower()
        else:
            st = str(v).lower()
        if st in ("stub", "missing", "scaffold"):
            out.append(
                _err(
                    "LC16",
                    "critical",
                    "production mode must not leave feature-truth-matrix features in stub/missing/scaffold",
                    ["feature-truth-matrix.json", str(k), st],
                )
            )
    return out


def _inv_lc15(transcript_path: Path | None) -> list[dict]:
    out: list[dict] = []
    if not transcript_path or not transcript_path.is_file():
        return out
    raw = json.loads(transcript_path.read_text(encoding="utf-8"))
    names = [s.get("name") for s in raw.get("steps") or []]
    if "failure_corpus" not in names:
        out.append(_err("LC15", "medium", "validate_release transcript missing failure_corpus step", [str(transcript_path)]))
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("run_dir_pos", nargs="?", default="", help="Run directory (positional, for validate_impl subprocess)")
    ap.add_argument("--run-dir", default="", help="Run directory (flag form)")
    ap.add_argument("--skill-root", default=str(ROOT))
    ap.add_argument("--release-report", default="")
    ap.add_argument("--transcript", default="")
    args = ap.parse_args()
    rd_s = args.run_dir or args.run_dir_pos
    if not rd_s:
        print(json.dumps({"status": "fail", "reason": "run_dir required"}, ensure_ascii=False), file=sys.stderr)
        return 2
    rd = Path(rd_s)
    skill_root = Path(args.skill_root)
    report = Path(args.release_report) if args.release_report.strip() else None
    transcript = Path(args.transcript) if args.transcript.strip() else None

    violations: list[dict] = []
    checks = [
        _inv_lc01,
        _inv_lc02,
        _inv_lc03,
        _inv_lc04,
        _inv_lc05,
        _inv_lc09,
        _inv_lc10,
        _inv_lc11,
        _inv_lc13,
        _inv_lc14,
        _inv_lc16,
    ]
    for fn in checks:
        violations.extend(fn(rd))
    violations.extend(_inv_lc12(rd, skill_root))
    violations.extend(_inv_lc06(report, transcript))
    violations.extend(_inv_lc07(transcript))
    violations.extend(_inv_lc08(transcript))
    violations.extend(_inv_lc15(transcript))

    payload = {"status": "fail" if violations else "pass", "violations": violations, "run_dir": str(rd)}
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 1 if violations else 0


if __name__ == "__main__":
    raise SystemExit(main())
