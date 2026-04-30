#!/usr/bin/env python3
from pathlib import Path
import ast, json, re, sys
sys.dont_write_bytecode = True
VERSION = "18.3.2-delivery-truth-smoke-runtime-contract-hotfix"
root = Path(__file__).resolve().parents[1]
errors = []
required_dirs = ["contracts","scripts","schemas","references","failure-corpus","providers","kb","templates","examples","tests","case-library","policies","docs"]
required_scripts = [
    "rfo_v18_core.py", "interface_runtime_adapter.py", "runtime_job_worker.py", "outbox_delivery_worker.py",
    "run_research_factory.py", "build_research_package.py", "run_validator_dag.py", "smoke_test_interface_runtime.py",
    "validate_skill_discovery_frontmatter.py", "validate_package_claim_requires_zip.py", "validate_gate_consistency.py",
    "validate_late_results_protocol.py", "validate_v18_runtime_artifacts.py", "validate_all_python_ast.py", "validate_no_pycache.py",
    "validate_startup_runtime_proof.py", "validate_status_claim_consistency.py", "validate_no_skill_md_imitation.py",
    "validate_command_router_mapping.py", "validate_runtime_entrypoint.py", "validate_canonical_package_layout.py",
    "validate_delivery_manifest_requires_ack.py", "validate_provider_specific_logic_not_in_runtime.py", "render_full_html_report.py",
    "source_acquisition_broker.py", "inference_broker.py", "validate_execution_reliability_gate.py", "validate_model_call_ledger.py",
    "validate_partial_output_not_complete.py", "validate_finalize_marker_required.py", "validate_retry_action_required.py",
    "validate_retry_idempotency.py", "validate_late_results_not_merged.py", "validate_timeout_reflected_in_claim_caps.py",
    "validate_worker_lease_lifecycle.py", "validate_heartbeat_required_for_running.py", "validate_context_budget_policy.py",
    "validate_no_large_model_generated_html.py", "validate_no_ambient_context_runtime_override.py", "validate_cron_isolation.py",
    "validate_source_quality_schema.py", "validate_claim_source_fit.py", "validate_political_actor_not_statistics.py",
    "validate_self_claim_not_external_confirmation.py", "validate_source_laundering.py", "validate_snippet_only_not_confirmed.py",
    "validate_source_gap_reflected_in_final_verdict.py", "validate_local_model_circuit_breaker.py", "validate_work_unit_size_limits.py",
    "build_skill_inventory.py", "build_context_budget_analysis.py", "validate_context_claim_gate.py",
    "validate_read_claim_requires_ledger.py", "validate_no_smoke_as_context_proof.py",
    "validate_no_plain_subagent_for_full_workspace_read.py", "validate_no_reasoning_leak_in_chat_payload.py",
    "validate_runtime_contract_current.py", "validate_no_attachment_claim_without_ack.py", "validate_delivery_claim_matches_manifest.py",
    "validate_final_gate_required_for_completion_claim.py", "validate_smoke_run_not_presented_as_research.py",
    "validate_manual_fallback_not_presented_as_rfo.py", "validate_no_local_paths_as_delivery.py",
    "validate_core_modularization_contract.py", "validate_no_html_string_gate_as_primary_contract.py"
]
required_providers = ["providers/telegram/telegram_delivery_adapter.py", "providers/cli/cli_delivery_adapter.py", "providers/webhook/webhook_delivery_adapter.py"]
required_contracts = ["artifact-contract.json", "validator-dag.json", "delivery-contract.json", "interface-adapter-contract.json", "provider-contract.json", "canonical-package-layout-contract.json", "runtime-queue-contract.json", "outbox-contract.json", "source-acquisition-reliability-contract.json", "execution-reliability-contract.json", "context-acquisition-contract.json", "delivery-truth-contract.json", "smoke-run-contract.json", "manual-fallback-contract.json", "runtime-contract-v18.3.2.json", "core-boundary-contract.json"]
required_policies = ["source-quality-policy.json", "source-acquisition-policy.json", "execution-reliability-policy.json", "context-acquisition-policy.json"]
required_schemas = ["claim-source-fit.schema.json", "claim-evidence-weight.schema.json", "source-acquisition-result.schema.json", "source-gap.schema.json", "model-call.schema.json", "worker-lease.schema.json", "execution-reliability-gate.schema.json", "context-load-request.schema.json", "read-ledger.schema.json", "context-claim-gate.schema.json", "active-context-manifest.schema.json", "attachment-ledger.schema.json", "user-visible-delivery.schema.json", "run-mode-classification.schema.json", "manual-fallback-ledger.schema.json"]
for d in required_dirs:
    if not (root/d).is_dir(): errors.append(f"missing_dir:{d}")
for s in required_scripts:
    if not (root/"scripts"/s).is_file(): errors.append(f"missing_script:{s}")
for p in required_providers:
    if not (root/p).is_file(): errors.append(f"missing_provider:{p}")
for c in required_contracts:
    p = root/"contracts"/c
    if not p.exists(): errors.append(f"missing_contract:{c}")
    else:
        try: json.loads(p.read_text(encoding="utf-8"))
        except Exception as e: errors.append(f"bad_contract:{c}:{e}")
for p in required_policies:
    fp=root/"policies"/p
    if not fp.exists(): errors.append(f"missing_policy:{p}")
    else:
        try: json.loads(fp.read_text(encoding="utf-8"))
        except Exception as e: errors.append(f"bad_policy:{p}:{e}")
for s in required_schemas:
    fp=root/"schemas"/s
    if not fp.exists(): errors.append(f"missing_schema:{s}")
    else:
        try: json.loads(fp.read_text(encoding="utf-8"))
        except Exception as e: errors.append(f"bad_schema:{s}:{e}")
skill = root/"SKILL.md"
text = skill.read_text(encoding="utf-8", errors="ignore") if skill.exists() else ""
if not text.startswith("---"): errors.append("SKILL.md_missing_yaml_frontmatter")
else:
    fm = text.split("---",2)[1]
    if not re.search(r"(?m)^name:\s*research_factory_orchestrator\s*$", fm): errors.append("frontmatter_missing_name")
    if VERSION not in fm: errors.append("frontmatter_missing_v18_3_2_version")
for needle in ["HOW TO OPERATE THIS SKILL", "v18.3.1 context integrity invariants", "smoke-test pass is not proof", "v18.3 hard reliability invariants", "ambient-agent context must not override", "Partial model output is not a completed work unit", "Preserved v17.3 Contract Body", "## v17 interface adapter and outbox runtime", "## v12 report delivery system"]:
    if needle not in text: errors.append(f"SKILL.md_missing_section:{needle}")
file_count = sum(1 for p in root.rglob("*") if p.is_file())
if file_count < 650: errors.append(f"skill_file_count_too_low:{file_count}")
for d in ["references", "schemas", "kb", "templates", "examples", "tests"]:
    if not any((root/d).rglob("*")): errors.append(f"empty_or_missing_preserved_dir:{d}")
for py in root.rglob("*.py"):
    try: ast.parse(py.read_text(encoding="utf-8"))
    except Exception as e: errors.append(f"python_ast_error:{py.relative_to(root)}:{e}")
pycache = [str(p.relative_to(root)) for p in root.rglob("*") if p.name == "__pycache__" or p.suffix == ".pyc"]
if pycache: errors.append("pycache_present:"+json.dumps(pycache, ensure_ascii=False))
index = root/"failure-corpus/index.json"
if not index.exists(): errors.append("missing_failure_corpus_index")
else:
    data = json.loads(index.read_text(encoding="utf-8"))
    if not data.get("legacy_v17_cases"): errors.append("failure_corpus_missing_legacy_v17_cases")
    if not data.get("required_failure_classes"): errors.append("failure_corpus_missing_required_classes")
    if not data.get("v18_3_reliability_cases"): errors.append("failure_corpus_missing_v18_3_reliability_cases")
    if not data.get("v18_3_1_context_integrity_cases"): errors.append("failure_corpus_missing_v18_3_1_context_integrity_cases")
    if not data.get("v18_3_2_delivery_truth_cases"): errors.append("failure_corpus_missing_v18_3_2_delivery_truth_cases")
out = {"status":"pass" if not errors else "fail", "validator":"validate_skill", "version":VERSION, "skill_file_count":file_count, "errors":errors}
print(json.dumps(out, ensure_ascii=False, indent=2))
sys.exit(1 if errors else 0)
