# Workflow registry (4-view)

## 1. Pipeline (workflow)

`init` → `adapter` → `worker` → `run` → `render` → `outbox` → `validate` → `package` → `deliver`

## 2. Components

- `runtime/impl.py` — orchestration
- `runtime/handoff.py` — signed envelopes
- `runtime/trace.py` — tamper-evident trace chain
- `runtime/capability.py` — scoped agency (OWASP LLM08)
- `runtime/output_filter.py` — injection guard on outbound text

## 3. User journey

Operator queues job → worker renders → outbox emits events → delivery acks → gates → optional `scripts/reality_checker.py`.

## 4. State machine

See `contracts/state-machine.json` and `scripts/validate_state_transitions.py`.

## Handoff contracts

| Contract file | Phases |
|---------------|--------|
| `contracts/handoffs/init-to-run.json` | init → run |
| `contracts/handoffs/run-to-render.json` | run → render |
| `contracts/handoffs/render-to-outbox.json` | render → outbox |
