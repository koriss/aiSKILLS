# ADR-010 — Root patterns from fourth in-depth audit (G2)

## Status

Accepted — documentation-only (v19.0.3), companion to ADR-009.

## Three recurring root patterns

1. **Silent skip on rollback** — conditional writes (`if dm:`) break closure invariants; proof layer must **always** materialize rollback artifacts.
2. **Validator / schema semantic drift** — checks named for one invariant (e.g. “missing attachment”) implemented as another (e.g. “empty list”); requires **issue-code accurate semantics** + fixture coverage.
3. **Release path not exercising production profile** — green CI on legacy-only smoke while v19 profile path fails in the field; **dual smokes** (`smoke_telegram_v18` + `smoke_telegram_v19`) are mandatory gates.

## Three design rules (non-negotiable for future releases)

1. **No silent `{}` JSON** on proof artifacts — use `minimal_valid` whitelist + explicit merge functions.
2. **Physical artifacts for validator-visible paths** — if a schema references `report/foo.html`, the file must exist before V6 runs (rollback stub pattern).
3. **Transcript self-attestation** — `validate_release.py` MUST assert `REQUIRED_GATES` coverage (`B4`) so new steps cannot be added without being in the pass set.

## Relationship to ADR-009

- ADR-009 = **how to speak** (vocabulary + lenses).
- ADR-010 = **how not to regress** (anti-patterns + release gates).

## Consequences

Patch releases may still be **semver-exception** when proof-layer semantics change; document under release notes + SemVer disclaimer (see v19.0.3 notes).
