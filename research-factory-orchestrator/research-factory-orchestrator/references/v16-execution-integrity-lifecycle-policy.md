
# v16 Execution Integrity and Lifecycle Policy

Version: `16.0.0-execution-integrity-lifecycle-hardening`.

The problem is not only bad research output. The whole lifecycle can fail:

```text
command → entrypoint → runtime → planning → dispatch → tools → sources → claims → synthesis → render → delivery → status → evals
```

Any layer can hallucinate success. Therefore every layer needs either:
- runtime artifact,
- validator,
- eval case,
- delivery gate.

`SKILL.md` is contract, not runtime. The only valid start is the configured entrypoint.
