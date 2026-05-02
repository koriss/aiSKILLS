# `run_core_validators.py` — specification (v19)

## Purpose

Single entrypoint executing **exactly six** validators in order, aggregating results into `validation-transcript.json` using the v19 transcript schema.

## CLI

```
python scripts/run_core_validators.py --run-dir <path> [--profile mvr|full-rigor|propaganda-io|book-verification]
```

- Default profile: `mvr`
- Profile JSON loaded from `validation-profiles/<name>.json` **after implementation**; during design phase drafts live under `docs/v19/drafts/validation-profiles/`.

## Behaviour

1. Resolve profile → list of validator ids (always six fixed ids; profile tweaks **options**, not id set).
2. For each validator: `subprocess.run([sys.executable, script, "--run-dir", run_dir], cwd=skill_root, timeout=...)`
3. Parse stdout JSON; on non-JSON or crash → synthesize `{ "validator_id": "...", "passed": false, "blocking": true, "issues": [{"code":"CRASH"}], ... }`
4. Append to `validators[]` in transcript.
5. `overall_pass = all(r.passed for r in validators if not skipped)`; any `blocking` failure ⇒ `overall_pass=false`.
6. Write `validation-transcript.json` atomically (write temp + rename).

## Forbidden

- Shelling out to `jq`
- Network calls
- Implicit profile selection without logging `profile_used` + escalation metadata

## Exit code

`0` iff `overall_pass`.
