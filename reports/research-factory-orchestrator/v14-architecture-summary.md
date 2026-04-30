
# v14 Architecture Summary

Version: `14.0.0-failure-corpus-superagent-hardening`

v14 treats v12 outputs as failure corpus and adds guards inspired by production-grade agent systems:

- orchestrator-worker decomposition;
- bounded work-units;
- durable checkpoints;
- timeout recovery;
- failure packets;
- provenance manifests;
- observability events;
- regression eval corpus;
- strict delivery-state machine;
- safe Telegram channel;
- raw evidence vault + service-use annex.
