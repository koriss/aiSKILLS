#!/usr/bin/env python3
"""V3 — independence + KB boundary (MVR-level)."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from urllib.parse import urlparse


def _emit(passed: bool, blocking: bool, issues: list, warnings: list, summary: str) -> None:
    print(
        json.dumps(
            {
                "validator_id": "validate_source_quality",
                "schema_version": "v19.0",
                "passed": passed,
                "blocking": blocking,
                "issues": issues,
                "warnings": warnings,
                "summary": summary,
            },
            ensure_ascii=False,
        )
    )


def _read_profile_rule(rd: Path, key: str) -> str:
    pup = rd / "validation-profile-used.json"
    if not pup.is_file():
        return "warn"
    try:
        prof = json.loads(pup.read_text(encoding="utf-8"))
    except Exception:
        return "warn"
    if not isinstance(prof, dict):
        return "warn"
    br = prof.get("blocking_rules")
    if not isinstance(br, dict):
        return "warn"
    return str(br.get(key) or "warn").lower()


def _load(p: Path) -> dict | None:
    if not p.is_file():
        return None
    try:
        o = json.loads(p.read_text(encoding="utf-8"))
        return o if isinstance(o, dict) else None
    except Exception:
        return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", required=True)
    args = ap.parse_args()
    rd = Path(args.run_dir)
    issues: list[dict] = []
    warnings: list[dict] = []
    srcp = rd / "sources.json"
    if not srcp.is_file():
        srcp = rd / "sources" / "sources.json"
    src = _load(srcp) or {}
    items = [s for s in (src.get("sources") or src.get("items") or []) if isinstance(s, dict)]
    by_canon: dict[str, list[str]] = {}
    for s in items:
        sid = str(s.get("source_id") or s.get("id") or "")
        canon = str(s.get("canonical_origin_id") or s.get("url_normalized") or sid)
        by_canon.setdefault(canon, []).append(sid)
    sid_to_origin: dict[str, str] = {}
    for s in items:
        sid = str(s.get("source_id") or s.get("id") or "")
        if not sid:
            continue
        sid_to_origin[sid] = str(s.get("canonical_origin_id") or s.get("url_normalized") or sid)
    policy_path = srcp.parent / "source-policy.json"
    if policy_path.is_file():
        pol = _load(policy_path) or {}
        per = pol.get("per_host") if isinstance(pol.get("per_host"), dict) else {}
        mode = _read_profile_rule(rd, "source_policy_unknown")
        sev = "error" if mode == "block" else "warning"
        seen_hosts: set[str] = set()
        for s in items:
            u = str(s.get("url") or "")
            try:
                host = (urlparse(u).hostname or "").lower()
            except Exception:
                host = ""
            if not host or host in seen_hosts:
                continue
            seen_hosts.add(host)
            row = per.get(host)
            if row is None:
                hit = {
                    "code": "SOURCE-POLICY-UNKNOWN",
                    "severity": sev,
                    "path": host,
                    "detail": "host missing from source-policy.json per_host",
                    "artifact": "source-policy.json",
                }
                if sev == "error":
                    issues.append(hit)
                else:
                    warnings.append(hit)
            elif isinstance(row, dict):
                for fld in ("robots_status", "tos_status", "license_status"):
                    if str(row.get(fld) or "").lower() == "unknown":
                        hit = {
                            "code": "SOURCE-POLICY-UNKNOWN",
                            "severity": sev,
                            "path": f"{host}.{fld}",
                            "detail": f"{fld}=unknown",
                            "artifact": "source-policy.json",
                        }
                        if sev == "error":
                            issues.append(hit)
                        else:
                            warnings.append(hit)
                        break

    cr = _load(rd / "claims-registry.json") or {}
    for cl in cr.get("claims") or []:
        if not isinstance(cl, dict):
            continue
        roles = {"primary_support", "corroboration"}
        origins: list[str] = []
        sids: list[str] = []
        for sup in cl.get("support_set") or []:
            if not isinstance(sup, dict):
                continue
            role_fc = str(sup.get("role_for_claim") or "")
            if role_fc not in roles:
                continue
            sid = str(sup.get("source_id") or "")
            if sid and (sid.upper().startswith("KB:") or sid.startswith("kb:")) and role_fc in ("primary_support", "corroboration"):
                issues.append(
                    {
                        "code": "kb_match_used_as_evidence",
                        "severity": "error",
                        "path": sid,
                        "detail": "KB source_id must not appear as primary_support or corroboration in support_set",
                        "artifact": "claims-registry.json",
                    }
                )
            if sid:
                sids.append(sid)
                origins.append(sid_to_origin.get(sid, sid))
        if len(sids) >= 2 and len(set(origins)) == 1:
            issues.append(
                {
                    "code": "duplicate_sources_same_origin",
                    "severity": "error",
                    "path": str(cl.get("claim_id")),
                    "detail": "multiple support sources share one canonical_origin_id",
                    "artifact": "claims-registry.json",
                }
            )
    blocking = bool(issues)
    _emit(not blocking, blocking, issues, warnings, "V3 source quality / policy")
    return 0 if not blocking else 1


if __name__ == "__main__":
    raise SystemExit(main())
