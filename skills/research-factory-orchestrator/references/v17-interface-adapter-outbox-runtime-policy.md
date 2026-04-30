
# v17 Interface Adapter and Outbox Runtime Policy

Version: `17.0.0-interface-adapter-outbox-runtime`.

The runtime is interface-agnostic. Chat/messenger specifics belong to provider adapters.

Architecture:

```text
interface request
→ normalized command
→ runtime job
→ queue
→ runtime worker
→ research runtime
→ chat message plan
→ outbox events
→ provider adapter
→ delivery ack
→ delivery manifest
```

This follows async job, durable workflow and outbox patterns:
- command creates a job, not a long synchronous chat turn;
- outbox events are delivered by a relay/worker;
- delivery is confirmed by acknowledgements;
- provider-specific logic must not leak into research runtime.
