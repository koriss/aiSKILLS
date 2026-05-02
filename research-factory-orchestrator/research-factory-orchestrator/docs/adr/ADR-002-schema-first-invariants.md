# ADR-002: Schema-first invariants

Status: accepted

All v19 core artifacts are validated against schemas before semantic validators. Runtime writers MUST emit schema-conformant JSON first; semantic checks come after.
