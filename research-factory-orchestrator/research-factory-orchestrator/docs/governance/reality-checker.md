# Reality Checker

Default verdict is **`NEEDS_WORK`**. `READY` requires:

- `validation-transcript.json` status `pass`
- `delivery-manifest.delivery_status` in `{sent, delivered, stub_delivered}` per policy
- Critical gates present in `final-answer-gate.json` and passing
- Evidence / delivery ack material under `evidence-pack/` **or** `delivery-acks/`

Aligned with agency-agents **Reality Checker** + **Evidence Collector** discipline.
