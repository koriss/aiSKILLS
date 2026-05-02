# Design-phase verification checklist (v19)

Use this checklist before declaring design phase **complete**.

## Internal consistency

- [ ] D1–D11 documents do not contradict each other on: six validators, profile names, status caps, L0 scan rules, delivery split semantics.
- [ ] `role_for_claim` appears **only** in `claims-registry.support_set` (not `sources.json`) — see D3, D7.
- [ ] `validation-transcript` included as **core** schema (D7).
- [ ] `contradictions-lite` optional rules aligned with D5 + V4 text.

## Sacred path coverage

- [ ] V1+V2+V3+V4+V5 together cover: artifacts exist → chain complete → thresholds → final text mapping.
- [ ] [`sacred-path-contract.md`](./sacred-path-contract.md) matches `validators-core.md` and profile copies of the six-validator list.

## Truth-gate preservation (v18.5.1)

- [ ] V6 explicitly encodes: stub ≠ external, fail-closed rollback expectations, expanded path leak scan beyond chat txt only.
- [ ] No regression of CLI external delivery false positives called out in ADR-001.

## Profile coverage

- [ ] Each draft JSON under `drafts/validation-profiles/` lists same six `active_validators` ids; differences only in `options` / `claim_type_policies` / `blocking_rules`.

## Neutral rubric / bias audit

- [ ] D5 schema forbids moralized **system** enums; L2 matrix uses neutral `parties[].label`.
- [ ] `propaganda-io.json` uses pattern/topic separation; `kb_match_is_evidence: false`.
- [ ] Machine pattern ids conform to [`propaganda-io-neutrality.md`](./propaganda-io-neutrality.md); `claim_topics_*` labels are descriptive routing only (no partisan verdict taxonomy).

## Corpus / memory (design linkage)

- [ ] [`corpus-crawlers-book-memory.md`](./corpus-crawlers-book-memory.md) read and accepted as upstream context for implementation beyond phase 1 (no crawler code in narrow phase 1).

## Phase 1+ hardening awareness

- [ ] [`production-hardening-phase1.md`](./production-hardening-phase1.md) reviewed — release manifest/unzip/meta-coverage prioritized for GA zips even if deferred from first merge.

## Migration completeness (design obligation)

- [ ] D8 maps all 16 DAG validators + all registry rows to `core` / `heavy` / `legacy` / `ci-only`.

## Anti-ceremony

- [ ] No seventh core validator introduced in any doc.
- [ ] No heavy module required in MVR default JSON.

## Next step gate

- [ ] D10 fixture list agreed.
- [ ] Implementation phase scoped in `IMPLEMENTATION-PHASE-1-HANDOFF.md`.
