# OpenClaw RFO v18.3 — Stability Hardening Analysis

## 0. Input baseline

User-provided operational statistics:

```text
all history:
  success: 282
  error: 43
  total: 325
  error_rate: 13.23%
  timedOut=true: 38

promptError top:
  LLM idle timeout (120s): 29
  aborted | cron: job execution timed out: 5
  request timed out | request timed out: 4

last 24h:
  completions: 90
  success: 83
  error: 7
  error_rate: 7.78%
  LLM idle timeout: 5
  request timed out: 2
```

Interpretation:

```text
88.4% of all errors are timeout-related: 38 / 43.
67.4% of all errors are explicit LLM idle timeout: 29 / 43.
71.4% of last-24h errors are explicit LLM idle timeout: 5 / 7.
```

This is not primarily a source-quality problem and not primarily a single skill logic bug. The dominant failure mode is execution reliability: model/provider idle, runtime request timeout, cron timeout, and subagent lifecycle instability.

---

## 1. Archive inspection findings

Archive inspected:

```text
openclaw-mm27-agent-md-2026-04-30.tar.gz
```

Relevant files found:

```text
AGENTS.md
SOUL.md
USER.md
CAPABILITIES.md
HEARTBEAT.md
TOOLS.md
69.md
self-improving/retry-logic.md
self-improving/error-handling-framework.md
self-improving/multi-agent-protocol.md
proactivity/subagent-timeout-log.md
memory/search-tools.md
memory/2026-04-24.md
memory/2026-04-30.md
```

### 1.1 Contradictory orchestration instructions

The agent memory says:

```text
проверь / анализ / исследуй / фактчекинг → immediately spawn subagent
```

But the same knowledge base also says:

```text
Subagents stop after 30–90 seconds.
Do not rely on subagent for long tasks.
Subagent timeout is a known primary reliability issue.
```

This creates a bad default:

```text
large research task → immediate subagent → long prompt/output → 120s idle timeout / 30–90s subagent timeout
```

For RFO, this is hostile ambient context. The skill must not inherit this behavior.

### 1.2 “Do not economize tokens” increases idle timeout risk

The agent profile repeatedly says:

```text
не экономить токены
minimum 3800 chars
subagent outputs long answer
HTML report + Telegram delivery
```

That is useful as a user preference for final reports, but dangerous inside runtime execution. It encourages huge prompts and huge completions, which increases:

```text
LLM idle timeout
provider request timeout
context overflow
partial output without finalize
late result after retry
```

RFO must convert this into:

```text
rich final artifact, but small bounded model calls
```

Not:

```text
one huge model call that writes everything
```

### 1.3 Timeout handling is currently unsafe

`self-improving/retry-logic.md` has useful ideas, but the current partial salvage rule is unsafe for RFO:

```text
if char_count > 500 → use salvaged content
```

For a research runtime, 500 characters are not proof of a completed work-unit. Completion requires:

```text
structured output
schema validation
finalize marker
claim/evidence/source/gap ledgers
```

Otherwise timeout can silently become fake completion.

### 1.4 Retry logic treats timeout as “not an error”

The file says:

```text
After Timeout (NOT retry — timeout ≠ error)
```

But user stats show timeout is the dominant operational failure class. For RFO, timeout must be a first-class error state:

```text
timeout is not necessarily fatal,
but it is absolutely an execution event that must be recorded, classified, gated, retried/degraded, and reflected in final verdicts.
```

### 1.5 Multi-agent barrier is too brittle

`multi-agent-protocol.md` includes “Parallel with Barrier”: wait for all agents before synthesis.

This is correct only for tasks where full coverage is mandatory. In current environment, wait-all barriers turn one idle timeout into a whole-run delay/failure.

RFO needs:

```text
barrier modes:
  wait_all_required
  quorum_required
  deadline_then_degrade
  independent_sections
  critical_path_only
```

### 1.6 Agent fallback can violate RFO proof model

`proactivity/subagent-timeout-log.md` lists:

```text
Main Agent Fallback: Do the task directly without subagent
```

That may be acceptable for ordinary assistant behavior, but it violates RFO runtime integrity. RFO must not allow:

```text
subagent failed → main agent handwrites report → claim completed
```

Correct RFO behavior:

```text
subagent failed → failure packet → retry/resume/degrade → final gate caps claims → report states gaps
```

### 1.7 Cron tasks can contend with interactive work

Memory shows cron jobs and auto-commit jobs timing out. A scheduled heartbeat/digest/autocommit should not consume the same high-level model execution budget as a user-triggered RFO run.

Needed:

```text
cron isolation
job priority
concurrency caps
no-LLM shell-only cron where possible
cron time budget separate from interactive RFO
```

---

## 2. Core diagnosis

The current environment behaves like this:

```text
model/provider calls are not reliably available for >120s idle windows
subagents are short-lived and may stop in 30–90s
web acquisition is unreliable
cron jobs sometimes hit execution limits
the agent memory encourages immediate subagent use and long outputs
```

Therefore RFO must be designed as:

```text
bounded, resumable, checkpointed, idempotent workflow
```

Not as:

```text
large autonomous agent prompt that tries to finish the whole research in one go
```

---

## 3. Required new subsystem: Execution Reliability Layer

Add to RFO:

```text
Execution Reliability Layer
```

It sits between runtime jobs and workers/model/tool calls:

```text
interface adapter
→ runtime job
→ execution reliability layer
→ work-unit scheduler
→ source acquisition broker
→ inference broker
→ result spool
→ synthesis
→ renderer
→ outbox
```

Its job:

```text
1. prevent giant unbounded model calls;
2. record all timeouts and disconnects;
3. preserve partial structured output;
4. resume/degrade instead of fake-completing;
5. route around bad model/tool backends;
6. enforce final-answer gates.
```

---

## 4. Protect RFO from hostile ambient agent context

The agent archive shows a lot of useful memory, but also instructions that are dangerous for this skill.

RFO needs a prompt/context firewall:

```text
ambient agent memory is not runtime authority
SKILL.md is contract, not execution engine
only normalized-command.json + runtime-job.json control execution
```

### 4.1 Add `ambient-context-risk-ledger.json`

Example:

```json
{
  "detected_risks": [
    {
      "risk_code": "A001_IMMEDIATE_SUBAGENT_TRIGGER",
      "source": "AGENTS.md/USER.md",
      "risk": "Host agent prefers direct subagent instead of RFO runtime.",
      "rfo_action": "ignored; runtime uses interface adapter and job queue"
    },
    {
      "risk_code": "A002_UNBOUNDED_TOKEN_PREFERENCE",
      "source": "USER.md/CAPABILITIES.md",
      "risk": "Do not economize tokens can create large model calls.",
      "rfo_action": "converted to rich final artifact requirement, not unbounded model-call permission"
    },
    {
      "risk_code": "A003_MAIN_AGENT_FALLBACK",
      "source": "proactivity/subagent-timeout-log.md",
      "risk": "Main agent fallback may bypass ledgers and proof.",
      "rfo_action": "forbidden inside RFO; failure packet required"
    }
  ]
}
```

### 4.2 Add validator

```text
validate_no_ambient_context_runtime_override.py
```

Fails if report/runtime claims completion while execution path shows:

```text
plain subagent
main-agent fallback
handwritten report after subagent failure
missing runtime artifacts
```

Failure codes:

```text
F230 ambient_agent_instruction_overrode_runtime
F231 direct_subagent_used_instead_of_runtime_worker
F232 main_agent_fallback_used_as_rfo_completion
F233 unbounded_token_instruction_reached_model_call
```

---

## 5. Model idle timeout strategy

Given the dominant failure:

```text
LLM idle timeout (120s): no response from model
```

RFO should not wait for 120 seconds and then discover the call is dead.

### 5.1 Soft idle watchdog

Use shorter internal thresholds:

```text
first-token soft timeout: 20–35s
no-progress soft timeout: 45–60s
provider hard timeout: 110s, below platform 120s
```

If no first token by soft threshold:

```text
cancel if possible
record model_idle_soft_timeout
retry smaller prompt or alternate backend
```

### 5.2 No monolithic output

Ban huge single responses:

```text
strict_json_single_blob_forbidden: true
large_html_generation_by_model: forbidden
large_zip/package generation_by_model: forbidden
```

Use:

```text
JSONL partial commits
small claim batches
deterministic renderers for HTML/package
```

### 5.3 Expected first output contract

Each model call should be asked to emit a tiny first record quickly:

```jsonl
{"type":"start","model_call_id":"MC-001","work_unit_id":"WU-004"}
```

If no `start` within first-token timeout, the call is unhealthy and should be retried elsewhere.

---

## 6. Inference Broker

Local/remote model calls should go through:

```text
scripts/inference_broker.py
```

Input:

```json
{
  "model_call_id": "MC-00042",
  "work_unit_id": "WU-004",
  "model_profile": "local_extractor",
  "prompt_ref": "prompts/WU-004.prompt.md",
  "expected_output": "jsonl_claim_cards",
  "first_token_timeout_sec": 30,
  "idle_timeout_sec": 60,
  "hard_timeout_sec": 110,
  "idempotency_key": "JOB-123:WU-004:analysis:v1"
}
```

Output:

```json
{
  "model_call_id": "MC-00042",
  "status": "complete|partial|timeout|disconnect|overflow|backend_error",
  "output_ref": "execution/model-outputs/MC-00042.jsonl",
  "partial_ref": "execution/partials/MC-00042.partial.jsonl",
  "finalize_seen": false,
  "retry_recommendation": "shrink_prompt|alternate_backend|split_work_unit|degrade"
}
```

---

## 7. Partial output protocol

A work-unit output is complete only if it contains:

```jsonl
{"type":"finalize","status":"complete","work_unit_id":"WU-004"}
```

Without this marker:

```text
output status = partial
claim verdict cap = partial/unverified
cannot be used as completed WU
```

Valid JSONL records:

```text
start
source_candidate
source_acquisition_result
source_gap
claim_card
source_binding
claim_source_fit
contradiction
checkpoint
error
finalize
```

This replaces char-count salvage.

---

## 8. Work-unit sizing policy

Do not ask a model to do a whole investigation.

Limits:

```json
{
  "max_claims_per_wu": 5,
  "max_sources_per_acquisition_wu": 5,
  "max_input_chars_per_model_call": 60000,
  "max_expected_model_runtime_sec": 90,
  "max_output_records_per_call": 50,
  "strict_json_single_blob_forbidden": true,
  "html_generation_by_model_forbidden": true
}
```

If a task is larger:

```text
compile more WUs, not bigger WUs
```

---

## 9. Worker leases and heartbeats

Every worker/subagent/model call must be observable.

Files:

```text
execution/worker-leases.json
execution/worker-heartbeats.jsonl
execution/model-call-ledger.jsonl
execution/model-timeout-ledger.jsonl
execution/partial-output-ledger.jsonl
execution/lifecycle-events.jsonl
```

Lifecycle states:

```text
job_created
job_queued
worker_claimed
worker_heartbeat_seen
work_units_compiled
work_units_queued
wu_claimed
model_call_started
model_first_output_seen
model_checkpoint_seen
model_finalize_seen
wu_completed
wu_degraded
synthesis_started
rendered
outbox_created
delivery_ack_received
```

New failure codes:

```text
F240 job_queued_but_no_worker_claimed
F241 worker_claimed_but_no_heartbeat
F242 work_units_compiled_but_not_queued
F243 wu_queued_but_not_claimed
F244 model_call_started_but_no_first_output
F245 model_call_partial_without_finalize
F246 partial_output_used_as_complete
F247 timeout_not_reflected_in_final_gate
```

---

## 10. Local model circuit breaker

Local neural backends can hang, disconnect, OOM, or slow down. Treat each backend as a service with health state.

```json
{
  "backend_id": "local-llama-cpp-qwen",
  "window": "30m",
  "success_rate": 0.64,
  "idle_timeout_rate": 0.22,
  "disconnect_rate": 0.05,
  "context_overflow_rate": 0.11,
  "p95_latency_sec": 118,
  "circuit_state": "half_open",
  "recommended_max_context": 32768,
  "recommended_max_output_tokens": 1536,
  "avoid_for": ["long_context_synthesis", "strict_json_blob"],
  "preferred_for": ["classification", "short_extraction"]
}
```

Circuit states:

```text
closed: use normally
half_open: only small probes / small WUs
open: do not use except health probe
```

Open circuit if:

```text
idle_timeout_rate > 20% over last N calls
or 3 consecutive idle timeouts
or OOM/context overflow repeats
```

---

## 11. Retry policy for model calls

Retry is allowed only with an action:

```text
same prompt retry: only for transport_disconnect / transient request timeout, max 1
idle timeout: shrink prompt or route alternate backend
context overflow/OOM: split WU, never same prompt retry
partial without finalize: continuation packet or degrade
```

Retry ledger:

```json
{
  "work_unit_id": "WU-004",
  "attempt": 2,
  "previous_failure": "model_idle_timeout",
  "retry_action": "shrink_prompt",
  "idempotency_key": "JOB-123:WU-004:v2",
  "dedup_keys_inherited": ["CLM-001", "SRC-003"]
}
```

---

## 12. Continuation packets

Do not ask “continue where you stopped” in free text. Create a packet:

```json
{
  "continuation_id": "CONT-004",
  "work_unit_id": "WU-004",
  "previous_model_call_id": "MC-00042",
  "completed_records": [
    "claim_card:CLM-1",
    "source_binding:CLM-1:SRC-3"
  ],
  "unfinished_tasks": [
    "classify SRC-7",
    "check contradiction for CLM-2"
  ],
  "known_gaps": [
    "SRC-9 fetch_timeout"
  ],
  "forbidden_repetition": [
    "do not reprocess CLM-1 unless contradiction found"
  ]
}
```

---

## 13. Cron isolation

Cron errors are less frequent, but they pollute reliability and can contend with interactive work.

Rules:

```text
cron must have lower priority than user-triggered RFO
cron must not run long LLM jobs unless explicitly scheduled for that
shell-only cron must not invoke model
cron timeout must write cron-timeout-ledger.jsonl
cron jobs must use lock files to avoid overlap
cron jobs must not mutate active RFO run directories
```

Artifacts:

```text
execution/cron-ledger.jsonl
execution/cron-locks/
execution/job-priority.json
```

Failure codes:

```text
F260 cron_job_timed_out_without_ledger
F261 cron_contended_with_interactive_rfo
F262 cron_mutated_active_run
F263 overlapping_cron_instances
```

---

## 14. Source/tool timeout integration

Execution reliability must connect to source acquisition:

```text
fetch timeout → source gap → source rank cap → claim verdict cap
model timeout → partial output → continuation/degrade → claim verdict cap
worker timeout → lease/requeue/dead-letter → lifecycle failure code
```

Do not let:

```text
blocked source + timed-out model = confident final claim
```

---

## 15. Final answer gate changes

Add:

```json
{
  "execution_reliability_gate": {
    "status": "pass|pass_with_degraded_outputs|fail",
    "model_timeouts": 0,
    "request_timeouts": 0,
    "worker_lease_expired": 0,
    "partial_outputs_used": 0,
    "partial_outputs_without_finalize": 0,
    "claims_capped_due_to_execution": [],
    "forbidden_claims": []
  }
}
```

Gate rules:

```text
confirmed claim requires complete WU or valid quorum
partial model output cannot confirm claim
snippet-only source cannot confirm claim
late result cannot be merged after finalization
worker failure must appear in report limitations
```

---

## 16. Renderer policy

HTML report must include an execution integrity section:

```text
Execution reliability:
- model calls: 42
- completed: 37
- partial: 3
- timed out: 2
- retries: 4
- claims capped due to timeout: CLM-4, CLM-9
- unavailable source gaps: 7
```

Chat summary:

```text
Проверка завершена с деградацией: часть источников/модельных вызовов упёрлась в timeout.
Эти claim-ы не повышались до confirmed; ограничения перечислены в HTML.
```

---

## 17. Validators to add

```text
validate_execution_reliability_gate.py
validate_model_call_ledger.py
validate_model_first_output_seen.py
validate_partial_output_not_complete.py
validate_finalize_marker_required.py
validate_retry_action_required.py
validate_retry_idempotency.py
validate_worker_lease_lifecycle.py
validate_heartbeat_required_for_running.py
validate_timeout_reflected_in_claim_caps.py
validate_late_results_not_merged.py
validate_context_budget_policy.py
validate_no_large_model_generated_html.py
validate_no_ambient_context_runtime_override.py
validate_cron_isolation.py
```

---

## 18. Regression corpus

Add cases:

```text
F230 ambient-agent-direct-subagent-overrides-rfo.json
F231 main-agent-fallback-handwrites-report.json
F233 unbounded-token-instruction-reaches-model-call.json
F240 job-queued-no-worker-claimed.json
F244 model-call-no-first-output-before-timeout.json
F245 partial-jsonl-without-finalize.json
F246 partial-output-used-as-complete.json
F247 timeout-not-reflected-in-final-gate.json
F250 same-prompt-retried-after-context-overflow.json
F251 late-result-merged-after-retry.json
F260 cron-timeout-without-ledger.json
F261 cron-contends-with-interactive-rfo.json
```

---

## 19. Implementation priority

### P0 — must do first

```text
1. Finalize marker required.
2. Partial output cannot mark WU complete.
3. Model call ledger with timeout classification.
4. Work-unit size policy.
5. Execution reliability gate.
6. Host/ambient context override guard.
```

### P1 — high impact

```text
1. Inference broker.
2. Local model circuit breaker.
3. Continuation packets.
4. Worker leases and heartbeats.
5. Retry action/idempotency ledger.
```

### P2 — after core stable

```text
1. Cron isolation.
2. Backend health dashboards.
3. Adaptive model routing.
4. Historical SLO reports.
```

---

## 20. Expected stability improvement

Given the current profile:

```text
error rate all history: 13.23%
last-24h error rate: 7.78%
timeout share of errors: 88.4%
```

The first target is not “zero timeouts”. The target is:

```text
timeout no longer equals run failure
```

Desired v18.3 outcome:

```text
raw model/tool timeouts may remain,
but finalStatus=error should drop because:
  timeout → partial/degraded WU
  partial WU → claim cap
  claim cap → honest report
  honest report → successful run with limitations
```

Target metrics:

```text
finalStatus error rate: < 5%
LLM idle timeout causing whole run failure: < 2%
partial outputs used as final: 0
confirmed claims from partial/no-finalize output: 0
late result silently merged: 0
unbounded model calls: 0
```

---

## 21. Short formula

```text
Do not make the model more reliable.
Make the skill survive unreliable models.
```

```text
Timeout is data.
Partial is not final.
Retry must change something.
Long report does not require long model call.
Host-agent memory is not runtime authority.
Cron must not compete with interactive research.
```
