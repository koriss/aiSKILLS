"""Outbox delivery worker: invoke provider adapters and reconcile gates."""
from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import zipfile
from pathlib import Path

from runtime.util import REQ_EVENTS, jl, jr, jw, now, sid, skill_root


def _load_provider_caps(provider: str) -> dict:
    root = skill_root()
    p = root / "contracts" / "provider-capabilities.json"
    if not p.is_file():
        p = root / "contracts" / "provider_capabilities.json"
    data = jr(p, {})
    row = (data.get("providers") or {}).get(provider) or {}
    return {
        "stub_delivery": bool(row.get("stub_delivery", provider == "webhook")),
        "external": bool(row.get("external", False)),
        "user_visible_delivery": bool(row.get("user_visible_delivery", row.get("external", False))),
        "requires_provider_ack_id": bool(row.get("requires_provider_ack_id", False)),
    }


def _publish_tuple(rd: Path, external: bool, stub_only: bool, provider_pass: bool, any_failed: bool) -> tuple:
    root = skill_root()
    pol = jr(root / "contracts" / "publish-policy.json", {})
    run = jr(rd / "run.json", {})
    rm_cls = jr(rd / "run-mode-classification.json", {})
    classified = str(rm_cls.get("run_mode") or "").strip()
    effective_mode = classified if classified else str(run.get("mode", "") or "")
    audit = jr(rd / "self-audit" / "runtime-self-audit.json", {})
    manual = bool(audit.get("manual_fallback_presented_as_rfo"))
    cr_coll = jr(rd / "collection-result.json", {})
    seed_only_coll = isinstance(cr_coll, dict) and cr_coll.get("seed_only") is True
    spec = importlib.util.spec_from_file_location("rfo_publish_policy", root / "runtime" / "publish_policy.py")
    if spec and spec.loader:
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod.decide_publish_allowed(
            policy=pol,
            run_mode=effective_mode,
            manual_fallback=manual,
            provider_pass=provider_pass,
            any_failed=any_failed,
            external=external,
            stub_only=stub_only,
            collection_seed_only=seed_only_coll,
        )
    return (False, "publish_policy_module_missing")


def cmd_outbox(a):
    processed = []
    for rd in sorted((Path(a.runs_root) / "runs").glob("*")):
        if not (rd / "outbox").exists():
            continue
        da = rd / "delivery-acks"
        da.mkdir(parents=True, exist_ok=True)
        lockf = None
        try:
            import fcntl

            lockf = open(da / ".outbox-delivery-serial.lock", "a+", encoding="utf-8")
            fcntl.flock(lockf.fileno(), fcntl.LOCK_EX)
        except (ImportError, OSError):
            lockf = None
        try:
            _cmd_outbox_inner(rd, processed)
        finally:
            if lockf is not None:
                import fcntl

                try:
                    fcntl.flock(lockf.fileno(), fcntl.LOCK_UN)
                finally:
                    lockf.close()
    print(json.dumps({"processed": processed}, ensure_ascii=False, indent=2))


def _cmd_outbox_inner(rd: Path, processed: list) -> None:
    for ep in sorted((rd / "outbox").glob("OUT-*.json")):
        ev = jr(ep)
        eid = str(ev.get("event_id") or ep.stem).strip()
        if not eid:
            continue
        ap = rd / "delivery-acks" / f"{eid}.json"
        if ap.exists():
            continue
        caps = _load_provider_caps(str(ev.get("provider", "")))
        stub = caps["stub_delivery"]
        indecisive = ev.get("status") in ("deferred_for_clarification", "tool_switched", "clarification_requested") or ev.get("delivery_outcome") in (
            "deferred_for_clarification",
            "tool_switched",
            "clarification_requested",
        )
        payload_path = (rd / ev["payload_path"]) if ev.get("payload_path") else None
        payload_ok = bool(payload_path and payload_path.is_file())
        if payload_ok and ev.get("type") == "send_message" and payload_path and (
            str(payload_path).endswith(".txt") or str(payload_path).endswith(".md")
        ):
            try:
                from runtime.output_filter import assert_safe_payload

                assert_safe_payload(payload_path.read_text(encoding="utf-8", errors="replace"))
            except Exception:
                payload_ok = False
        adapter_out = {}
        if indecisive:
            status = str(ev.get("status") or ev.get("delivery_outcome") or "deferred_for_clarification")
        else:
            status = "failed"
            if payload_ok and ev.get("type") in ("send_message", "send_file"):
                provider = str(ev.get("provider") or "cli")
                apath = skill_root() / "providers" / provider / f"{provider}_delivery_adapter.py"
                if apath.is_file():
                    try:
                        from runtime.capability import issue, persist_token

                        cap = issue([f"deliver_external:{provider}"])
                        cap_path = persist_token(rd, str(ev.get("event_id") or eid), cap)
                        pr = subprocess.run(
                            [
                                sys.executable,
                                "-S",
                                str(apath),
                                "--run-dir",
                                str(rd),
                                "--event-id",
                                str(ev.get("event_id", "") or eid),
                                "--event-json",
                                str(ep),
                                "--capability-token",
                                str(cap_path),
                                "--action",
                                f"deliver_external:{provider}",
                            ],
                            capture_output=True,
                            text=True,
                            timeout=120,
                            cwd=str(skill_root()),
                            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
                        )
                        # Parse adapter stdout even on non-zero exit: some adapters
                        # intentionally return structured JSON refusal payloads with
                        # exit!=0 and we must preserve reason/aux fields for manifests.
                        try:
                            adapter_out = json.loads(pr.stdout.strip() or "{}")
                            if not isinstance(adapter_out, dict):
                                adapter_out = {}
                        except Exception:
                            adapter_out = {}
                        if pr.returncode != 0:
                            status = str(adapter_out.get("status") or "failed")
                        else:
                            status = str(adapter_out.get("status") or "sent")
                        # CLI stub channel returns status=stub; unknown statuses are normalized.
                        if status not in ("sent", "stub", "failed"):
                            status = "sent" if pr.returncode == 0 else "failed"
                    except Exception:
                        status = "failed"
                else:
                    status = "failed"
                    adapter_out = {
                        "status": "failed",
                        "reason": "PROVIDER-DELIVERY-ADAPTER-MISSING",
                        "delivery_not_proven": True,
                    }
        if adapter_out:
            stub = bool(adapter_out.get("stub_delivery", stub))
            real_ext = bool(adapter_out.get("real_external_delivery", False))
        else:
            ok_delivery = status in ("sent", "stub")
            real_ext = ok_delivery and caps["external"] and (not stub)
        # v19.2.1 honesty hardening: surface explicit refusal reasons and the
        # ``delivery_not_proven`` flag from the provider adapter to the ack.
        adapter_reason = str(adapter_out.get("reason") or "").strip() if adapter_out else ""
        adapter_delivery_not_proven = bool(adapter_out.get("delivery_not_proven")) if adapter_out else False
        adapter_chat_id_source = str(adapter_out.get("chat_id_source") or "").strip() if adapter_out else ""
        adapter_api_base_source = str(adapter_out.get("api_base_source") or "").strip() if adapter_out else ""
        ack_id = f"ACK-{eid}"
        created_ts = now()
        pp_path = rd / "provider-payloads" / f"{eid}.json"
        msg_id = ""
        if status in ("sent", "stub"):
            msg_id = str(adapter_out.get("provider_message_id") or (("stub:" if stub else "local:") + eid))
        ack = {
            "ack_id": ack_id,
            "event_id": ev.get("event_id") or eid,
            "run_id": ev.get("run_id"),
            "job_id": ev.get("job_id"),
            "command_id": ev.get("command_id"),
            "provider": ev.get("provider") or "cli",
            "status": status,
            "provider_message_id": msg_id,
            "idempotency_key": ev.get("idempotency_key") or "",
            "payload_kind": ev.get("payload_kind"),
            "file_kind": ev.get("file_kind"),
            "provider_payload_path": str(pp_path.resolve()) if status in ("sent", "stub") else "",
            "stub_delivery": stub,
            "real_external_delivery": real_ext,
            "delivery_not_proven": adapter_delivery_not_proven,
            "reason": adapter_reason or None,
            "chat_id_source": adapter_chat_id_source or None,
            "api_base_source": adapter_api_base_source or None,
            "created_at": created_ts,
            "acked_at": created_ts,
        }
        jw(ap, ack)
        ev["status"] = status
        jw(ep, ev)
        processed.append(str(ev.get("event_id") or eid))
        try:
            from runtime.event_history import append_side_effect

            append_side_effect(rd, "delivery_ack", {"event_id": ev.get("event_id") or eid, "provider": ev.get("provider"), "idempotency_key": ev.get("idempotency_key")}, {"status": status})
        except Exception:
            pass
    da = rd / "delivery-acks"
    da.mkdir(parents=True, exist_ok=True)
    ack_ids = sorted([p.stem for p in da.glob("OUT-*.json") if p.name != "processed_events.json"])
    jw(
        da / "processed_events.json",
        {"run_id": jr(rd / "run.json", {}).get("run_id"), "events": [{"event_id": e, "processed_at": now()} for e in ack_ids], "dedup_note": "at-least-once consumer dedup table"},
    )
    req = jr(rd / "outbox/outbox-policy.json").get("required_events", REQ_EVENTS)
    acks = [jr(rd / "delivery-acks" / f"{e}.json") for e in req if (rd / "delivery-acks" / f"{e}.json").exists()]
    missing = [e for e in req if not (rd / "delivery-acks" / f"{e}.json").exists()]
    any_stub = any(x.get("stub_delivery") for x in acks)
    any_real = any(x.get("real_external_delivery") for x in acks)
    any_delivery_not_proven = any(bool(x.get("delivery_not_proven")) for x in acks)
    # v19.2.1 honesty hardening: distinguish *delivery_not_proven*
    # (refusal-with-reason) from a real provider/adapter crash. Real
    # failures are acks with status=='failed' but no delivery_not_proven.
    any_failed = any(
        x.get("status") == "failed" and not x.get("delivery_not_proven")
        for x in acks
    )
    delivery_not_proven_reasons = sorted(
        {str(x.get("reason")).strip() for x in acks if x.get("delivery_not_proven") and x.get("reason")}
    )
    # ``provider_pass`` requires ack presence & no real failure. A
    # delivery_not_proven ack is still an ack and still satisfies the
    # provider-ack gate; the missing piece is *external delivery*, which
    # is captured separately below.
    provider_pass = not missing and not any_failed and len(acks) == len(req)
    external = provider_pass and any_real and not any_stub
    stub_only = provider_pass and any_stub and not any_real and not any_delivery_not_proven
    # Citation grounding will be properly produced by validator in Phase 4B/4C.
    # Until then, omit RAF/DFL from artifacts (no magic literals leak into v19 surface).
    citation_grounding_path = rd / "citation-grounding-result.json"
    if citation_grounding_path.is_file():
        cgr = jr(citation_grounding_path, {})
        citation_grounding_gate_pass = bool(cgr.get("passed"))
        cg_extra = {k: cgr[k] for k in ("relevance_aware_factuality_score", "deflection_rate_when_no_grounding") if k in cgr}
    else:
        citation_grounding_gate_pass = False
        cg_extra = {}
    # v19.2.1 honesty hardening: when adapters explicitly refuse to send,
    # classify the gate as ``delivery_not_proven`` and surface reasons.
    if external:
        ext_status = "pass"
    elif any_delivery_not_proven:
        ext_status = "delivery_not_proven"
    elif stub_only:
        ext_status = "stub_only"
    else:
        ext_status = "fail"
    ext_gate = {
        "status": ext_status,
        "passed": external,
        "stub_only": stub_only,
        "delivery_not_proven": any_delivery_not_proven,
    }
    if delivery_not_proven_reasons:
        ext_gate["reasons"] = delivery_not_proven_reasons
    if final_status := (delivery_not_proven_reasons[0] if delivery_not_proven_reasons else None):
        ext_gate["primary_reason"] = final_status
    pkg_zip = rd / "package/research-package.zip"
    zip_ok = False
    if pkg_zip.is_file():
        try:
            with zipfile.ZipFile(pkg_zip) as z:
                names = set(z.namelist())
                zip_ok = "outbox/OUT-0005.json" in names and "outbox/OUT-0006.json" in names
        except Exception:
            zip_ok = False
    checks = {
        "provider_ack_gate": {"status": "pass" if provider_pass else "fail", "passed": provider_pass},
        "external_delivery_gate": ext_gate,
        "final_user_claim_gate": {"status": ext_status, "passed": external, "stub_only": stub_only, "delivery_not_proven": any_delivery_not_proven},
        "content_gate": {"status": "pass", "passed": (rd / "report/full-report.html").exists()},
        "wave_graph_gate": {"status": "pass", "passed": (rd / "graph/wave-plan.json").exists()},
        "io_analysis_gate": {"status": "pass", "passed": (rd / "report/io-propaganda-check.json").exists()},
        "self_audit_gate": {"status": "pass", "passed": (rd / "self-audit/runtime-self-audit.json").exists()},
        "package_gate": {"status": "pass" if zip_ok else "fail", "passed": zip_ok},
        "citation_grounding_gate": {
            "status": "pass" if citation_grounding_gate_pass else "fail",
            "passed": citation_grounding_gate_pass,
            "validator_result_present": citation_grounding_path.is_file(),
            **cg_extra,
        },
    }
    run = jr(rd / "run.json")
    pub_ok, pub_reason = _publish_tuple(rd, external, stub_only, provider_pass, any_failed)
    if any_failed:
        dstat = "failed"
    elif external:
        dstat = "delivered"
    elif any_delivery_not_proven:
        dstat = "delivery_not_proven"
    elif stub_only:
        dstat = "stub_delivered"
    else:
        dstat = "partial_delivery"
    fg_passed = bool(external and pub_ok and not any_failed and citation_grounding_gate_pass)
    if any_failed or not citation_grounding_gate_pass:
        fg_status = "fail"
    elif external:
        fg_status = "pass"
    elif any_delivery_not_proven:
        fg_status = "delivery_not_proven"
    elif stub_only:
        fg_status = "stub_only"
    else:
        fg_status = "fail"
    prev_dm = jr(rd / "delivery-manifest.json", {})
    provider_caps_snapshot = {}
    for e in req:
        ack = jr(rd / "delivery-acks" / f"{e}.json", {})
        prov = ack.get("provider")
        if prov and prov not in provider_caps_snapshot:
            provider_caps_snapshot[prov] = _load_provider_caps(prov)
    jw(
        rd / "delivery-manifest.json",
        {
            "schema_version": "v19.0",
            "run_id": run.get("run_id"),
            "job_id": run.get("job_id"),
            "delivery_status": dstat,
            "required_outbox_events": req,
            "required_acks_missing": missing,
            "stub_delivery": any_stub,
            "real_external_delivery": external,
            "artifact_ready_claim_allowed": (rd / "package/research-package.zip").exists() and not any_failed,
            "external_delivery_claim_allowed": (external and pub_ok) and not any_failed,
            "stub_delivery_disclosure_required": (any_stub or stub_only) and not external,
            "provider_capability_snapshot": provider_caps_snapshot,
            "delivery_claim_allowed": (external and pub_ok) and not any_failed,
            "publish_allowed": pub_ok and not any_failed,
            "publish_reason": pub_reason if not any_failed else "failed_ack_present",
            "attachments": prev_dm.get("attachments") if isinstance(prev_dm.get("attachments"), list) else [],
            "local_paths_exposed": False,
            "created_at": prev_dm.get("created_at") or now(),
            "checks": checks,
            "updated_at": now(),
        },
    )
    jw(
        rd / "attachment-ledger.json",
        {
            "run_id": run.get("run_id"),
            "job_id": run.get("job_id"),
            "attachments": [{"event_id": e, "path": jr(rd / "outbox" / f"{e}.json").get("payload_path")} for e in ["OUT-0005", "OUT-0006"]],
            "all_required_acknowledged": provider_pass,
            "all_required_externally_sent": external,
        },
    )
    prev_fg = jr(rd / "final-answer-gate.json", {})
    contradiction_echo = prev_fg.get("contradiction_echo") if isinstance(prev_fg.get("contradiction_echo"), dict) else {
        "contradiction_level": 0,
        "contradiction_scan_performed": False,
        "scan_scope": "none",
        "high_severity_detected": False,
    }
    overconfidence_risk = prev_fg.get("overconfidence_risk") if isinstance(prev_fg.get("overconfidence_risk"), dict) else {
        "blocking": [],
        "warnings": [],
        "signals": {},
    }
    fag_obj = {
        "schema_version": "v19.0",
        "run_id": run.get("run_id"),
        "passed": fg_passed,
        "status": fg_status,
        "checks": checks,
        "contradiction_echo": contradiction_echo,
        "overconfidence_risk": overconfidence_risk,
        "created_at": prev_fg.get("created_at") or now(),
        "updated_at": now(),
    }
    if delivery_not_proven_reasons:
        fag_obj["delivery_not_proven_reasons"] = delivery_not_proven_reasons
    if fg_status == "delivery_not_proven":
        fag_obj["primary_reason"] = delivery_not_proven_reasons[0] if delivery_not_proven_reasons else "DELIVERY-NOT-PROVEN"
    jw(
        rd / "final-answer-gate.json",
        fag_obj,
    )
    of_obj = {
        "schema_version": "v19.0",
        "run_id": run.get("run_id"),
        "job_id": run.get("job_id"),
        "finalized": True,
        "delivery_status": dstat,
        "publish_allowed": pub_ok and not any_failed,
        "external_delivery": external,
        "stub_only": stub_only,
        "delivery_not_proven": any_delivery_not_proven,
        "any_failed_acks": any_failed,
        "citation_grounding_passed": citation_grounding_gate_pass,
        "finalized_at": now(),
    }
    if delivery_not_proven_reasons:
        of_obj["delivery_not_proven_reasons"] = delivery_not_proven_reasons
    jw(
        rd / "outbox-finalization.json",
        of_obj,
    )
    st = jr(rd / "runtime-status.json")
    st.update({"state": dstat})
    jw(rd / "runtime-status.json", st)
    # Rebuild package after outbox mutates root artifacts so root-vs-zip truth
    # compares the finalized manifest/checks, not stale pre-outbox copies.
    pkg_builder = skill_root() / "scripts" / "build_research_package.py"
    if pkg_builder.is_file():
        try:
            subprocess.run(
                [sys.executable, "-S", str(pkg_builder), "--run-dir", str(rd)],
                capture_output=True,
                text=True,
                timeout=180,
                cwd=str(skill_root()),
                env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
                check=False,
            )
        except Exception as e:
            jl(
                rd / "runtime/errors.jsonl",
                {
                    "timestamp": now(),
                    "error_type": "outbox_package_rebuild_failed",
                    "detail": {"error": str(e)},
                },
            )
