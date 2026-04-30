# OpenClaw Research Factory Orchestrator — project handoff

Version of this handoff: `2026-04-30`
Current release artifact in this chat: `18.1.1-full-overlay-from-v17.3-base`
Canonical command: `/research_factory_orchestrator`
Canonical skill name: `research_factory_orchestrator`
Canonical entrypoint: `scripts/interface_runtime_adapter.py`

This document is written for a new agent/session that needs to continue the project without repeating old mistakes. Treat it as project memory plus release-state briefing. Do not treat it as proof by itself: every claim about a release must be verified against the actual archive, manifest, checksums and validation transcript.

---

## 1. One-sentence definition

`research-factory-orchestrator` is intended to be an executable OpenClaw skill/runtime for deep research tasks: it takes a user command, normalizes it, creates a durable runtime job, runs a multi-stage research workflow, records ledgers/provenance/evidence, renders standalone reports and chat summaries, sends outputs through a provider outbox, and only claims success after delivery proof exists.

The central idea is:

```text
Prompt is not runtime.
SKILL.md is not runtime.
A subagent is not orchestration.
Runtime must be executable, explicit, stateful, observable and validated.
```

---

## 2. Why the project exists

The failure mode we are trying to kill is not just bad writing. It is false execution.

Typical bad pattern:

```text
User:
/research_factory_orchestrator <research task>

Bot:
Started full research factory pipeline.

Reality:
- one plain subagent was launched;
- no runtime-status.json;
- no entrypoint-proof.json;
- no ledgers;
- no outbox ack;
- no delivery-manifest;
- final answer claims a pipeline that never ran.
```

Another bad pattern:

```text
Bot:
I will launch a subagent that reads SKILL.md and follows it.
```

This is invalid. `SKILL.md` is a contract/instruction surface. It is not the runtime. A weak model can read SKILL.md and still hallucinate execution. Therefore the skill must create machine-checkable artifacts.

Core anti-cheat rule:

```text
No runtime proof -> no pipeline claim.
No status proof -> no progress claim.
No ledgers -> no research claim.
No outbox ack -> no delivered claim.
No package zip -> no package claim.
```

---

## 3. What the system should do end-to-end

Target pipeline:

```text
User command
  -> interface request
  -> normalized command
  -> runtime job
  -> file queue
  -> runtime job worker
  -> research runtime
  -> work-unit plan
  -> workers/subagents/tool calls
  -> ledgers/search/tool/progress/retry
  -> claims registry
  -> evidence cards
  -> provenance manifest
  -> standalone HTML report
  -> chat message plan
  -> research package zip
  -> outbox events
  -> provider adapter
  -> delivery ack
  -> attachment ledger
  -> delivery manifest
  -> final answer gate
```

Minimal concrete flow for Telegram-like use:

```bash
python3 -S scripts/interface_runtime_adapter.py \
  --runs-root /tmp/rfo-runs \
  --interface telegram \
  --provider telegram \
  --conversation-id test \
  --message-id 1 \
  --user-id me \
  --task "test"

python3 -S scripts/runtime_job_worker.py --runs-root /tmp/rfo-runs --execute-runtime

python3 -S scripts/outbox_delivery_worker.py --runs-root /tmp/rfo-runs

python3 -S scripts/run_validator_dag.py --run-dir /tmp/rfo-runs/runs/<run-label>
```

---

## 4. Current release state: v18.1.1 full overlay

Current good release produced in this chat:

```text
release: openclaw-research-factory-orchestrator-v18.1.1-full-overlay-discovery-execution-integrity-hotfix
version: 18.1.1-full-overlay-from-v17.3-base
status: pass
base: v17.3 full workspace
overlays: v18, then v18.1
workspace files: 700
skill files: 673
workspace zip: 3,005,080 bytes
.skill package: 2,939,083 bytes
```

Important: this release was built specifically because v18/v18.1 were previously tiny scaffold/hotfix packages and must not be installed as full replacements.

v18.1.1 composition:

```text
v17.3 full workspace
  + v18 internal-analysis/audit-runtime overlay
  + v18.1 discovery/execution-integrity hotfix overlay
  + v18.1.1 packaging guards and release metadata
```

v18.1.1 key guards:

```text
- SKILL.md YAML frontmatter includes name: research_factory_orchestrator
- validate_skill.py fails if skill_file_count < 500
- v17.3 failure corpus index preserved
- v18/v18.1 runtime scripts included
- no __pycache__ / .pyc allowed
- package claim requires actual package/research-package.zip
- final gates checked for consistency
- late SA result protocol validated
- runtime artifacts checked after smoke run
```

Generated files in `/mnt/data`:

```text
openclaw-research-factory-orchestrator-v18.1.1-full-overlay-discovery-execution-integrity-hotfix-workspace.zip
research-factory-orchestrator-v18.1.1-full-overlay-discovery-execution-integrity-hotfix.skill
openclaw-research-factory-orchestrator-v18.1.1-full-overlay-discovery-execution-integrity-hotfix-install.md
openclaw-research-factory-orchestrator-v18.1.1-full-overlay-discovery-execution-integrity-hotfix-update-no-backup.md
openclaw-research-factory-orchestrator-v18.1.1-full-overlay-discovery-execution-integrity-hotfix-manifest.json
openclaw-research-factory-orchestrator-v18.1.1-full-overlay-discovery-execution-integrity-hotfix-checksums.txt
openclaw-research-factory-orchestrator-v18.1.1-full-overlay-discovery-execution-integrity-hotfix-validation-transcript.json
openclaw-research-factory-orchestrator-v18.1.1-full-overlay-discovery-execution-integrity-hotfix-release-report.md
```

Validation summary from transcript:

```text
validate_skill_discovery_frontmatter.py: pass
validate_skill.py: pass, skill_file_count=673
validate_all_python_ast.py: pass
validate_no_pycache.py: pass
smoke_test_interface_runtime.py: pass
validate_package_claim_requires_zip.py: pass
validate_gate_consistency.py: pass
validate_late_results_protocol.py: pass
validate_v18_runtime_artifacts.py: pass
```

Smoke test result:

```text
queued: true
package/research-package.zip built
outbox events: 6
processed: OUT-0001 ... OUT-0006
validators_total: 8
smoke_test_passed: true
final_gate_status: stub_only
```

Caveat: `stub_only` means local provider stub acknowledgements were used. It does not prove that external Telegram successfully received a file. It proves local runtime/outbox/provider-stub path.

---

## 5. Release artifact links expected by user

When generating future releases, always provide direct downloadable artifacts in this format:

```text
Скачать:

Workspace zip
.skill package
Install.md
Update без backup
Manifest
Checksums
Validation transcript
Release report
```

Do not merely say “ready”. The user expects files.

Do not invent artifacts. If a file was not produced, say so.

---

## 6. Historical version map

### Early versions: v4/v7/v12

Early prompt/agent attempts. Problems:

```text
- single subagent instead of real orchestration;
- report claims without proof;
- unstable HTML/report shape;
- inconsistent source handling;
- person/social identity confusion;
- Telegram got huge tables;
- local filesystem paths leaked into chat;
- no durable delivery proof;
- no canonical package layout.
```

### v13

Important conceptual line:

```text
runtime contracts
artifact contracts
state machine
durable ledgers
```

But v13 archive/state was not reliable enough to be treated as current base.

### v14

Failure-corpus and regression mindset.

Rule:

```text
A rule must be generated by runtime, enforced by validator, tested by failure corpus, or removed from claims.
```

### v15 — runtime-contract-enforcement

Added or emphasized:

```text
contract registry
artifact-contract.json
validator-dag.json
init_runtime.py
compile_work_units.py
required runtime artifacts
failure-corpus samples
final-answer gate
delivery manifest concept
semantic HTML renderer
Telegram renderer
PROV-like provenance manifest
```

Remaining gap:

```text
v15 could describe/create runtime-like packages,
but did not prove that /research_factory_orchestrator really launches the runtime instead of a plain subagent.
```

### v16 — execution-integrity-lifecycle-hardening

Added:

```text
scripts/run_research_factory.py
entrypoint-proof.json
runtime-status.json
contracts/entrypoint-contract.json
contracts/command-router-contract.json
validate_runtime_entrypoint.py
validate_command_router_mapping.py
validate_no_skill_md_imitation.py
validate_startup_runtime_proof.py
validate_status_claim_consistency.py
validate_worker_required_outputs.py
validate_tool_call_claims.py
validate_summary_no_new_facts.py
```

Closed failure classes:

```text
F021 runtime_entrypoint_confusion
F022 fake_skill_invocation
F023 one_subagent_instead_of_runtime_fanout
F024 read_skill_md_as_runtime
F025 status_claim_mismatch
```

Remaining gap:

```text
entrypoint known but not executed;
entrypoint has no interface return path;
command-runtime adapter missing.
```

### v17 — interface-adapter-outbox-runtime

Major architecture shift:

```text
Not telegram-runtime-adapter.
Use generic interface adapter + provider adapters.
```

Added:

```text
contracts/interface-adapter-contract.json
contracts/provider-contract.json
contracts/runtime-queue-contract.json
contracts/outbox-contract.json
contracts/canonical-package-layout-contract.json

schemas/interface-request.schema.json
schemas/normalized-command.schema.json
schemas/runtime-job.schema.json
schemas/outbox-event.schema.json
schemas/delivery-ack.schema.json
schemas/chat-message-plan.schema.json
schemas/provider-payload.schema.json

scripts/interface_runtime_adapter.py
scripts/runtime_job_worker.py
scripts/outbox_delivery_worker.py

providers/telegram/telegram_delivery_adapter.py
providers/cli/cli_delivery_adapter.py
providers/webhook/webhook_delivery_adapter.py

validate_interface_adapter_contract.py
validate_normalized_command.py
validate_runtime_job_queued.py
validate_outbox_delivery.py
validate_no_direct_interface_response.py
validate_provider_payload.py
validate_canonical_package_layout.py
validate_worker_bundle_not_research_package.py
```

v17 target path:

```text
interface request
-> normalized-command.json
-> runtime-job.json
-> queue/pending/JOB.json
-> runtime_job_worker.py
-> run_research_factory.py
-> chat-message-plan.json
-> outbox events
-> provider adapter
-> delivery-ack.json
```

### v17.3 — current full base for v18.1.1

Known as:

```text
openclaw-research-factory-orchestrator-v17.3-report-proof-integrity-hardening-workspace.zip
```

It was the closest complete base available in this chat. It preserved the large workspace: references, KB, templates, schemas, examples, tests, contracts, failure corpus.

### v18/v18.1 — scaffold/hotfix packages

Problem discovered:

```text
v18 workspace: 26 KB
v18.1 workspace: 34 KB
v18.1 contained ~47 files / ~58 KB unpacked
```

These were not full releases. They were hotfix/scaffold overlays and dangerous to install via `rm -rf TARGET && cp -a ...` because that would erase the large v17.3 workspace.

Useful content from these overlays:

```text
rfo_v18_core.py
wrapper scripts
frontmatter discovery fix
runtime/package/gate validators
new failure cases
late results protocol
package claim guard
```

### v18.1.1 — fixed full overlay

This is the currently correct full release because it starts from v17.3 and overlays v18/v18.1 without deleting the inherited large workspace.

---

## 7. Canonical package layout expected from a real run

A real research package should look like this:

```text
research-package.zip
  run.json
  entrypoint-proof.json
  runtime-status.json
  observability-events.jsonl

  interface/
    interface-request.json
    normalized-command.json

  jobs/
    runtime-job.json

  work-unit-plan.json
  subagent-plan.json
  subagent-ledger.json

  ledgers/
    search-ledger.json
    tool-call-ledger.json
    progress-ledger.json
    retry-ledger.json

  sources/
    sources.json
    source-quality.json
    source-laundering.json

  claims/
    claims-registry.json

  evidence/
    evidence-cards.json

  raw-evidence/
    raw-evidence-vault.json

  graph/
    target-graph.json
    identity-graph.json
    social-profile-binding.json

  provenance-manifest.json
  artifact-manifest.json
  validation-transcript.json
  delivery-manifest.json
  attachment-ledger.json
  final-answer-gate.json

  report/
    semantic-report.json
    full-report.html

  chat/
    chat-message-plan.json
    message-001.txt
    message-002.txt

  outbox/
    outbox-policy.json
    OUT-0001.json
    OUT-0002.json

  delivery-acks/
    OUT-0001.json
    OUT-0002.json
```

Important distinction:

```text
SA-001/
SA-002/
SA-003/
...
```

is a worker bundle, not a full research package. It must not be delivered or labeled as the final research package.

---

## 8. Core architectural layers

### 8.1 Interface adapter

Responsible for converting raw UI/channel command into normalized runtime inputs.

Inputs:

```text
interface/provider/conversation/message/user/task/delivery constraints
```

Outputs:

```text
interface/interface-request.json
interface/normalized-command.json
jobs/runtime-job.json
queue/pending/JOB-*.json
```

Must not perform the research itself.
Must not directly generate final answers.
Must not bypass queue/outbox.

### 8.2 Runtime job queue

Purpose: decouple chat command from long-running research.

Expected state model:

```text
created
queued
claimed
running
workers_running
synthesis_ready
rendered
packaged
delivery_queued
delivered
failed
```

Use a file queue first; do not over-engineer into Kafka/Rabbit/etc unless real pressure appears.

### 8.3 Runtime worker

Claims a pending job, invokes `scripts/run_research_factory.py` or equivalent v18 core, updates runtime-status and workflow-events, builds package, creates outbox events.

Must not claim success if runtime failed.
Must not create delivery success without ack.

### 8.4 Research runtime

Responsible for actual research planning, execution, ledgers and synthesis.

Target responsibilities:

```text
task profiling
dynamic work-unit compilation
source sweep
contrary/adversarial search
entity resolution
identity graph
claim extraction
claim validation
evidence cards
provenance
synthesis
report rendering
```

### 8.5 Renderers

Outputs:

```text
report/full-report.html
report/semantic-report.json
chat/chat-message-plan.json
chat/message-001.txt...
```

HTML must be standalone: embedded CSS, no external theme dependency. Chat messages must be Telegram/mobile safe.

### 8.6 Outbox

Transactional delivery layer.

Do not say “sent” until provider wrote ack.

Event types may include:

```text
send_message
send_file
send_package
send_status
```

### 8.7 Provider adapters

Provider-specific constraints live only here:

```text
providers/telegram/
providers/cli/
providers/webhook/
```

Research runtime must not hardcode Telegram. Telegram is a provider, not the center of the system.

---

## 9. Report requirements

Standalone HTML requirements:

```text
- one .html opens without external CSS/JS;
- usable on mobile and desktop;
- full source URLs in source section;
- inline citation markers: [1], [2], [3];
- clear claim/evidence/provenance mapping;
- embedded proof blocks for machine inspection.
```

Embedded proof blocks should include, where available:

```text
artifact-manifest-json
provenance-manifest-json
validation-transcript-json
delivery-manifest-json
runtime-status-json
entrypoint-proof-json
```

Telegram/chat summary requirements:

```text
- no giant tables;
- split long messages into logical blocks;
- vertical cards are preferred;
- no local paths like /home/node/...;
- no raw sensitive contacts unless explicitly appropriate and safe;
- never say “attached/sent/delivered” without delivery ack;
- include enough information for the user to understand status.
```

---

## 10. Research model and coverage axes

Do not make a hardcoded domain factory like:

```text
if person -> always agents A/B/C
if company -> always agents D/E/F
if game -> always agents G/H/I
```

Use a universal dynamic coverage model:

```text
entity_resolution
primary_origin_sources
broad_sweep
contrary_adversarial_search
source_quality_provenance
timeline_freshness
structured_data
claim_factcheck
strong_tie_pivoting
contact_media_graph
raw_evidence_vault
synthesis_merge
```

Optional domain-specific modules may be activated by task profile, but the core remains generic.

Examples:

```text
person/company -> identity/entity resolution, registry search, social binding, source quality
politics/IO -> narrative analysis, source laundering, actor/method mapping
technology/model -> release notes, benchmarks, hardware constraints, primary docs
game/product -> official release info, user reports, platform stores, patches, performance
legal/entity -> registries, court filings, corporate records, sanctions where relevant
```

---

## 11. INT/OSINT/IO handling

The project borrowed ideas from:

```text
OSINT
SOCMINT
WEBINT
FININT
GEOINT
IMINT
CYBINT/CTI
TECHINT
MEDINT
MASINT
ALL-INT / multi-int fusion
```

But do not turn the skill into a rigid “intelligence discipline switchboard”. Use these as coverage inspiration.

There is also a propaganda/IO knowledge-base line:

```text
Propaganda Library
IO KB UNIFIED
actors.jsonl
methods.jsonl
documents.jsonl
sources.jsonl
relations.jsonl
PROPAGANDA_METHODS_v2.json
Ontology graph.jsonl
query_methods.py
```

This should be optional KB/tooling for narrative/propaganda/media/information-operation tasks, not a hardcoded default for all politics.

Useful optional modules:

```text
IO_KB_matching
narrative_analysis
amplification_chain
source_laundering
actor_method_relation_extraction
language_coverage
```

---

## 12. Person/identity rules

Critical because previous agents confused people with same names/social profiles.

Rules:

```text
- never confirm social profile by name-only match;
- collect same-name candidates;
- maintain identity-confusion-set;
- separate weak/medium/strong bindings;
- weak match cannot be promoted to confirmed;
- negative identity should be “not confirmed in checked sources”, not “does not exist”.
```

Strong binding signals:

```text
- official site cross-link;
- same verified domain/email/username;
- same company/role across primary sources;
- confirmed publication/conference profile;
- company registry records;
- cross-links between confirmed profiles;
- same handle across platforms with context continuity.
```

Photos:

```text
- public photos can be used as report context if sourced;
- do not make biometric face-match claims;
- do not write “model confirmed by face”.
```

Contact/address data:

```text
- may be stored in raw evidence if public and relevant;
- classify sensitivity;
- avoid raw sensitive data in Telegram/chat;
- keep provenance;
- do not facilitate misuse.
```

---

## 13. Claim/evidence discipline

Every factual claim in final report should be one of:

```text
confirmed
partially_supported
contested
unverified
inferred
out_of_scope
```

Never collapse these into a single yes/no if the evidence does not support it.

Avoid scope drift:

```text
verdict_scope:
  user_claims: 5/5 confirmed
  expanded_claims: 15/18 confirmed, 1 partial, 2 contested
```

This prevents reports from seeming contradictory when one report checks only user claims and another expands the scope.

Summaries must not introduce new facts. If a fact appears only in summary and not in claims/evidence, validator should fail.

---

## 14. Known failure classes

### Entry/runtime

```text
F021 runtime_entrypoint_confusion
F022 fake_skill_invocation
F023 one_subagent_instead_of_runtime_fanout
F024 read_skill_md_as_runtime
F025 status_claim_mismatch
F026 command_router_mapping_missing
F027 entrypoint_proof_missing
F028 runtime_status_missing
F029 user_command_override
F035 entrypoint_known_but_not_executed
```

### Interface/adapter/outbox

```text
F044 interface_no_return_path
F045 command_runtime_adapter_missing
F046 job_created_but_not_queued
F047 queued_but_no_worker_claim
F048 worker_finished_but_no_outbox
F049 outbox_pending_not_delivered
F050 delivered_claim_without_outbox_ack
F051 direct_interface_response_bypasses_renderer
F055 provider_specific_logic_leaked_into_runtime
F056 telegram_hardcoded_in_runtime
F057 provider_payload_invalid
F058 message_split_policy_missing
F059 attachment_ack_missing
```

### Package/delivery

```text
F040 canonical_package_layout_missing
F041 worker_bundle_sent_as_research_package
F042 validator_not_in_delivery_path
F043 direct_chat_response_bypasses_renderer
F052 worker_bundle_sent_as_research_package
F053 canonical_package_layout_violation
F150 says_attached_but_not_sent
F152 delivery_status_overclaim
```

### Report/claims

```text
F036 report_claims_runtime_without_embedded_runtime_artifacts
F037 multi_report_scope_drift
F038 claim_set_not_declared
F039 verdict_scope_ambiguity
F120 inference_as_fact
F121 allegation_as_confirmed_fact
F122 self_claim_as_external_fact
F123 no_source_support
F130 premature_synthesis
F136 summary_adds_new_facts
```

### Identity/person

```text
F080 name_only_merge
F081 social_profile_confusion
F082 same_name_candidates_not_collected
F083 weak_binding_promoted_to_confirmed
F084 overconfident_negative_identity
F085 photo_used_as_biometric_proof
F086 contact_data_without_target_relevance
```

---

## 15. Validators that matter

At minimum, a release should pass:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -S scripts/validate_skill_discovery_frontmatter.py
PYTHONDONTWRITEBYTECODE=1 python3 -S scripts/validate_skill.py
PYTHONDONTWRITEBYTECODE=1 python3 -S scripts/validate_all_python_ast.py
PYTHONDONTWRITEBYTECODE=1 python3 -S scripts/validate_no_pycache.py
PYTHONDONTWRITEBYTECODE=1 python3 -S scripts/smoke_test_interface_runtime.py \
  --provider telegram \
  --interface telegram \
  --conversation-id test \
  --message-id 1 \
  --user-id me \
  --task "test release"
```

For a produced run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -S scripts/validate_package_claim_requires_zip.py --run-dir <RUN_DIR>
PYTHONDONTWRITEBYTECODE=1 python3 -S scripts/validate_gate_consistency.py --run-dir <RUN_DIR>
PYTHONDONTWRITEBYTECODE=1 python3 -S scripts/validate_late_results_protocol.py --run-dir <RUN_DIR>
PYTHONDONTWRITEBYTECODE=1 python3 -S scripts/validate_v18_runtime_artifacts.py --run-dir <RUN_DIR>
PYTHONDONTWRITEBYTECODE=1 python3 -S scripts/run_validator_dag.py --run-dir <RUN_DIR>
```

Important: subprocess/smoke checks can hang. If they do, say exactly that and do not claim E2E validation.

---

## 16. Installation/update style

The user does not want backups in update scripts.

Expected update style:

```bash
unzip openclaw-research-factory-orchestrator-v18.1.1-full-overlay-discovery-execution-integrity-hotfix-workspace.zip -d /tmp/rfo-v18.1.1
cd /tmp/rfo-v18.1.1
./update-openclaw-skill.sh /home/node/.openclaw/workspace
docker compose restart gateway
```

Manual equivalent:

```bash
set -euo pipefail
WORKSPACE=/home/node/.openclaw/workspace
TARGET="$WORKSPACE/skills/research-factory-orchestrator"
rm -rf "$TARGET"
mkdir -p "$WORKSPACE/skills"
cp -a skills/research-factory-orchestrator "$TARGET"
```

But only do this with a verified full-overlay release. Never use `rm -rf TARGET` with 26 KB / 34 KB scaffold packages.

After restart in Telegram:

```text
/new
/research_factory_orchestrator test
```

---

## 17. How to audit a new archive

When a new chat/session receives an archive, do this before changing anything:

```bash
set -euo pipefail
ZIP=/path/to/archive.zip
TMP=$(mktemp -d)
unzip "$ZIP" -d "$TMP"
find "$TMP" -maxdepth 3 -type d | sort | sed -n '1,200p'
find "$TMP" -type f | wc -l
du -sh "$TMP"
find "$TMP/skills/research-factory-orchestrator" -type f | wc -l
```

Then check:

```bash
cd "$TMP/skills/research-factory-orchestrator"
head -30 SKILL.md
find references kb templates schemas examples tests contracts failure-corpus -maxdepth 2 -type f | sed -n '1,100p'
PYTHONDONTWRITEBYTECODE=1 python3 -S scripts/validate_skill_discovery_frontmatter.py
PYTHONDONTWRITEBYTECODE=1 python3 -S scripts/validate_skill.py
PYTHONDONTWRITEBYTECODE=1 python3 -S scripts/validate_all_python_ast.py
PYTHONDONTWRITEBYTECODE=1 python3 -S scripts/validate_no_pycache.py
```

Red flags:

```text
- zip is tens of KB, not MB;
- skill file count < 500;
- SKILL.md has no YAML frontmatter;
- name is not research_factory_orchestrator;
- schemas/ is empty;
- kb/ or references/ unexpectedly absent;
- failure-corpus index overwritten by tiny overlay;
- .git included in release;
- __pycache__ or .pyc included;
- Telegram logic in generic runtime layer;
- no manifest/checksums/validation transcript.
```

---

## 18. How to build future releases

Correct full-overlay method:

```text
1. Start from latest verified full workspace.
2. Apply new overlay changes without deleting preserved dirs.
3. Preserve old failure-corpus index before merging.
4. Merge failure cases, do not overwrite blindly.
5. Ensure SKILL.md frontmatter stays valid.
6. Run validators.
7. Run smoke test.
8. Build workspace zip and .skill package.
9. Generate manifest/checksums/validation transcript/release report.
10. Provide links to all artifacts.
```

Suggested naming convention:

```text
openclaw-research-factory-orchestrator-vX.Y.Z-<slug>-workspace.zip
research-factory-orchestrator-vX.Y.Z-<slug>.skill
openclaw-research-factory-orchestrator-vX.Y.Z-<slug>-install.md
openclaw-research-factory-orchestrator-vX.Y.Z-<slug>-update-no-backup.md
openclaw-research-factory-orchestrator-vX.Y.Z-<slug>-manifest.json
openclaw-research-factory-orchestrator-vX.Y.Z-<slug>-checksums.txt
openclaw-research-factory-orchestrator-vX.Y.Z-<slug>-validation-transcript.json
openclaw-research-factory-orchestrator-vX.Y.Z-<slug>-release-report.md
```

Use git internally during build if helpful, but do not include `.git` in final archive.

---

## 19. Next likely roadmap: v18.2

Planned next layer: real search / wave workers.

What v18.2 should improve:

```text
- replace more stub/skeleton behavior with real work-unit execution;
- implement wave-based worker orchestration;
- add search-ledger/tool-call-ledger as real populated artifacts;
- make source collection and evidence cards non-placeholder;
- add stricter claim/evidence validators;
- add report proof blocks from actual runtime artifacts;
- improve retry/quorum logic for empty worker outputs;
- add deterministic handling of late worker results;
- strengthen provider-specific delivery ack handling;
- add real Telegram attachment proof if environment supports it.
```

Do not start by rewriting SKILL.md. Start by adding executable runtime behavior and validators.

---

## 20. Interaction style expected by the user

The user prefers:

```text
- Russian language;
- directness;
- no fake certainty;
- full command blocks for operational tasks;
- large prompts/documents when architecture is involved;
- no useless backup scripts;
- generated downloadable files for releases;
- explicit admission when validation was partial/stub-only.
```

If something breaks, do not handwave. Classify the failure layer:

```text
interface
queue
runtime
worker
source collection
identity/entity resolution
claims/evidence
report rendering
package building
outbox
provider delivery
status/final gate
release packaging
```

Then add one or more of:

```text
runtime artifact
validator
failure-corpus case
contract
smoke/eval
```

Do not merely add prose to SKILL.md unless it is backed by enforcement.

---

## 21. Compact prompt for a new agent

Copy this block into a new agent/session if needed:

```text
You are continuing OpenClaw Research Factory Orchestrator.

Goal: turn research_factory_orchestrator into an executable OpenClaw runtime, not a prompt-only skill. The canonical command is /research_factory_orchestrator. The canonical entrypoint is scripts/interface_runtime_adapter.py. SKILL.md is a contract, not runtime. A plain subagent reading SKILL.md is not acceptable.

Current good release is v18.1.1-full-overlay-from-v17.3-base. It was built from v17.3 full workspace, then v18 overlay, then v18.1 overlay, then v18.1.1 packaging guards. It has about 700 workspace files and 673 skill files. v18/v18.1 alone were tiny scaffold/hotfix packages and must not be installed as full replacements.

Core pipeline:
interface request -> normalized command -> runtime job -> queue -> runtime worker -> research runtime -> ledgers/manifests/evidence -> standalone HTML report -> chat message plan -> research package zip -> outbox -> provider adapter -> delivery ack -> final gate.

Core invariant:
No runtime proof, no pipeline claim. No ledgers, no research claim. No outbox ack, no delivered claim. No package zip, no package claim.

Before changing anything, inspect the actual archive: file count, size, SKILL.md frontmatter, references/kb/templates/schemas/contracts/failure-corpus preservation, Python AST, no pycache. Run validate_skill_discovery_frontmatter.py, validate_skill.py, validate_all_python_ast.py, validate_no_pycache.py and smoke_test_interface_runtime.py. Do not claim E2E Telegram delivery unless there is real provider ack, not only stub_only.

For future releases, provide downloadable artifacts: workspace zip, .skill package, install.md, update-no-backup.md, manifest.json, checksums.txt, validation-transcript.json, release-report.md.

Next likely work is v18.2 real search / wave workers: make source collection, work units, ledgers, evidence cards and report proof blocks real, not placeholders. Add validators and failure-corpus cases for every new claim.
```

---

## 22. Final operational principle

Always ask:

```text
Can a weak model cheat here?
```

If yes, the answer is not “write stronger prompt text”. The answer is one of:

```text
create a runtime artifact;
add a validator;
add a failure-corpus regression;
make a delivery/status gate;
make the package layout machine-checkable;
remove the unsupported claim.
```
