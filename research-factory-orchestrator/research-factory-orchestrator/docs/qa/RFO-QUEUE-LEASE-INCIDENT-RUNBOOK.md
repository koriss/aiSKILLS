# RFO queue / worker.lease incident runbook

**Scope:** `<runs-root>/queue/*` single-flight worker contour  
**Primary code:** `runtime/worker_impl.py` (`cmd_worker`)

---

## 0. Five-minute triage (quick path)

Use this first; only then read §1 onward for depth.

| Step | Action | If positive / signal |
|------|--------|-------------------------|
| 0:30 | Confirm `RUNS_ROOT` path and that you are not mixing two different `runs-root` trees between bridge and worker | Wrong path → fix env, not lease |
| 1:00 | `test -f "$RUNS_ROOT/queue/worker.lease" && cat` (read JSON) | Note `pid`, `job_file`, `created_at` |
| 1:30 | `ps -p <pid> -o pid,cmd=` (Linux) | **alive + rfo** → stop here: do **not** delete lease; wait or stop duplicate automation |
| 2:00 | `ls -la "$RUNS_ROOT/queue/pending" "$RUNS_ROOT/queue/running"` | Job only in `running` + dead PID → stalled claim (§3 R3) |
| 2:30 | Compare lease **mtime age** to `${RFO_WORKER_LEASE_STALE_SECONDS:-900}` | Age &lt; TTL + dead PID → **R2** (manual delete after proof) |
| 3:00 | `cat "$RUNS_ROOT/queue/failure-meta.json" 2>/dev/null` | All jobs **parked** → worker idle by design; wait or fix poison payload |
| 4:00 | **Recurrence?** Lease reappears immediately | Second worker or cron — find duplicate invocations |
| 5:00 | Apply **§3 Recovery** matching your case; verify with **§5** | — |

**Safe default:** do **not** `rm worker.lease` until Step 0:30–1:30 show PID is not an active worker for this `runs-root`.

---

Use this runbook when the relay bridge or automation logs:

- `claimed: false` with `reason: lease_present`
- repeated “worker did not claim a pending job”
- jobs stuck in `queue/pending` despite healthy disk

Companion analysis: [`RFO-DEEP-ANALYSIS-2026-05.md`](./RFO-DEEP-ANALYSIS-2026-05.md).  
Gateway-side timeouts / no–plain-subagent policy: [`../operators/openclaw-gateway-rfo-notes.md`](../operators/openclaw-gateway-rfo-notes.md).

---

## 1. Truth model (read this first)

- **Lease path:** `<runs-root>/queue/worker.lease` (JSON payload: `pid`, `job_file`, `created_at`, `token`, …).  
- **Stale cleanup:** Worker attempts unlink if lease file age **`≥ RFO_WORKER_LEASE_STALE_SECONDS`** (default **900**).  
- **Pending selection:** Pending jobs sorted; **Parking / backoff** may skip jobs with future `parked_until_ts` in `queue/failure-meta.json` (poison-job mitigation).

If **all** pendings are parked, worker returns `reason: all_pending_jobs_parked` — wait or fix metadata.

---

## 2. Safe triage checklist

### Step A — Identify active worker

```bash
LEASE_JSON=$(cat "${RUNS_ROOT}/queue/worker.lease")
```

Check `pid` field; on Linux:

```bash
ps -p <pid> -o pid,cmd=
```

- **Process exists** and matches `rfo_runtime_core.py` / orchestrated worker → lease is likely **live**; do **not** delete blindly. Reduce bridge concurrency / wait.

- **PID missing / wrong script** → treat lease as orphan candidate (continue to Step B).

### Step B — Measure lease age

```bash
stat -c '%Y age_sec=%Ys' "${RUNS_ROOT}/queue/worker.lease"  # GNU stat
python3 -c "import os,time;p='.../worker.lease';print(time.time()-os.path.getmtime(p))"
```

Compare to TTL:

```bash
echo "${RFO_WORKER_LEASE_STALE_SECONDS:-900}"
```

### Step C — Inspect queue layout

```bash
ls -la "${RUNS_ROOT}/queue/pending"
ls -la "${RUNS_ROOT}/queue/running"
ls -la "${RUNS_ROOT}/queue/done"
```

- File only in **`running`** with no alive worker ⇒ possible crash mid-flight; treat as stalled job (recovery procedures below).
- Duplicate run_ids or contradictory job payloads ⇒ operator merge issue (not solved by deleting lease alone).

### Step D — Inspect failure backoff

```bash
cat "${RUNS_ROOT}/queue/failure-meta.json" 2>/dev/null
```

Repeated failures increase `parked_until_ts`; if **now** `< parked_until_ts` for **every** pending file, worker idles deliberately.

---

## 3. Recovery procedures

### R1 — Orphan lease (no live PID, age > TTL)

**Preferred:** rerun worker — code path `_unlink_stale_lease` should remove automatically.

If TTL is too long:

```bash
export RFO_WORKER_LEASE_STALE_SECONDS=60   # shorten window for this shell only
# re-run bridge/worker invocation
```

### R2 — Orphan lease (no live PID, age < TTL)

**Operator override** after confirming **no** `rfo_runtime_core.py run …` subprocess for that `runs-root`:

```bash
rm -f "${RUNS_ROOT}/queue/worker.lease"
```

Then retry **one** worker instance.

### R3 — Job stuck in `running/`

Requires human judgment:

1. If worker dead: move JSON back manually following same semantics as `_return_job_pending` (from `running` → `pending`) **only if** you accept duplicate execution risk; preferred path is to **fix automation** to call worker again after lease cleanup.

2. If unsure, copy job file aside, clear lease, re-queue under new `job_id` via normal factory path (avoids double-send of outbox events).

### R4 — Poison job / infinite fail loop

Read `queue/failure-meta.json`. Options:

- Fix payload (bad `run_dir`, permissions, task string).
- Temporarily remove offending `JOB-*.json` from `pending` to `done_failed/` (ad-hoc dir, not standard — only with ops approval).
- Wait for exponential backoff to release other pending jobs.

---

## 4. Anti-patterns

- **Never** `rm worker.lease` while a live worker PID holds the same `runs-root` — risks two workers mutating `queue/` and `outbox/`.
- **Never** run **two** workers against the same `runs-root` on different machines without a real distributed lock (lease file is not that).
- **Avoid** setting `RFO_WORKER_LEASE_STALE_SECONDS=0` globally — disables automatic stale cleanup (only for narrow debugging).

---

## 5. Verification after recovery

```bash
python3 -S scripts/interface_runtime_adapter.py worker --runs-root "${RUNS_ROOT}" --execute-runtime  # CLI shape per SKILL-core.md
```

Expect `claimed: true` or explicit `reason` JSON on stdout — not silence.

Additionally: **`python3 -m unittest discover -s tests -p "test_*.py"`** for repo-level regressions unrelated to fleet state.
