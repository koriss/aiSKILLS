# v17 Interface Adapter and Outbox Runtime

Version: `17.0.0-interface-adapter-outbox-runtime`

v17 implements an interface-agnostic adapter layer:

```text
interface request
→ normalized-command.json
→ runtime-job.json
→ file queue
→ runtime_job_worker.py
→ run_research_factory.py
→ chat-message-plan.json
→ outbox events
→ provider adapter
→ delivery-ack.json
```

Main goal: remove Telegram hardcoding from research runtime and make Telegram only one provider.
