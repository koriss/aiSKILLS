# Host ↔ skill handshake (P6 draft)

States: `unsupported` · `partial` · `full`.

- **Full**: host routes `/research_factory_orchestrator` through adapter, blocks free-text replies that claim attachments without ledger+ack, enforces smoke/stub banners.
- **Partial**: skill validators only; agent may still bypass — log `manual_fallback_presented_as_rfo` when detected.
- **Unsupported**: skill treated as documentation; no delivery guarantees.

Pair with `tests/host-integration/agent_bypasses_skill.json` for CI once host exposes hooks.
