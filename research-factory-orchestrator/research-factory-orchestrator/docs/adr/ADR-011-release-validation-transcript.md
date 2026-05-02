# ADR-011 — Release validation transcript as committed proof artifact

**Status:** Accepted — policy + repo hygiene (v19.0.4)  
**Context:** `scripts/validate_release.py` writes `release-validation-transcript.json` at the repository root after a full gate run (B4 self-attestation). An alternative was to add this file to `.gitignore` and regenerate it only in CI or locally.

## Decision

**Commit `release-validation-transcript.json` to the repository** as the canonical **proof artifact** of the last successful `validate_release` run that shipped a patch (same spirit as a signed build manifest, without external signing).

## Rationale

1. **Reproducibility** — reviewers and operators can diff transcript steps, gate names, and fingerprints without rerunning the full smoke matrix.
2. **B4 alignment** — the release script already hashes the transcript (`transcript_sha256`); keeping the file in-tree makes that check meaningful across clones.
3. **Explicit tradeoff** — ignoring the transcript would make “green release” claims depend on ephemeral CI artifacts; committed transcript ties HEAD to a verifiable gate snapshot.

## Consequences

- Every release that bumps `runtime/version.json` / `SKILL.md` should re-run `python scripts/validate_release.py` (rc 0) and **commit** the updated `release-validation-transcript.json` together with release notes.
- Do not hand-edit the transcript; regenerate via `validate_release.py`.

## References

- `scripts/validate_release.py` — gate list, transcript write, B4 verdict.
- `scripts/validate_release_report.py` — transcript integrity + run.json version consistency.
- `docs/release-notes/v19.0.4.md` — ships this ADR with the v19.0.4 boundary refresh.
