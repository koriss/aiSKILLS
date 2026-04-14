# Release Blockers Catalog

Use this list to decide if publication must stop.

## Hard blockers (stop publication)

1. Missing or ambiguous publication target (`skill` / `package` / `both`)
2. Missing core metadata (`name`, `description`, `version`, or `SKILL.md`)
3. Broken install path on clean environment
4. Broken startup due to undocumented required config/secrets
5. Unsupported host/runtime behavior without explicit refusal
6. Entrypoint/exports mismatch
7. Security-sensitive defaults or secret leakage in docs/examples
8. Public artifact includes internal/private files
9. Breaking changes with no migration notes
10. Docs materially misrepresent actual behavior

## Escalation rule

If any hard blocker exists:
- verdict must be `not publishable` or `publishable with blockers`
- release recommendation must not be `safe to publish`

## Minimum unblock evidence

- updated artifact(s)
- clear patch note per blocker
- successful clean install/start smoke proof
- docs and examples synced with real behavior
