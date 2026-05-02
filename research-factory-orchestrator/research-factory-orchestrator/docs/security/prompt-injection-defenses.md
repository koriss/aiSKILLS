# Prompt injection — defense in depth

1. **Input validation** — host handshake + normalized command contracts.
2. **Output filtering** — `runtime/output_filter.py` on every outbound `.txt` payload before ack (`cmd_outbox`).
3. **Capability sandbox** — `runtime/capability.py` scopes adapter actions (`deliver_external:<provider>`).
4. **Static skill scan** — `scripts/validate_skill_markdown_injection.py` in CI / `validate()` subset.
5. **Manual vetting + approval gates** — Reality Checker default `NEEDS_WORK`.

Citations: arXiv:2510.26328 (Agent Skills), arXiv:2604.23887 (output filtering), arXiv:2601.17548 SoK.
