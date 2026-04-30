
# v6 Enforcement Audit

## Problem

v5 had strong instructions but lacked enough mechanical validators. A weak model could still create placeholder files and claim completion.

## v6 Fixes

Added:

- `validate_html_report.py`
- `validate_final_answer_gate.py`
- `validate_summary_no_new_claims.py`
- `validate_artifact_manifest.py`
- `validate_item.py`
- `validate_all_items.py`
- `security_scan_skill.py`
- `openclaw_postinstall_check.sh`
- `templates/full-report-template.html`
- `references/mechanical-validators.md`
- `references/minimum-completion-package.md`
- `references/domain-source-classes.md`
- `references/pdf-table-figure-policy.md`
- `references/contradiction-matrix.md`
- `references/source-snapshot-policy.md`
- `schemas/contradiction-matrix.schema.json`
- `schemas/source-snapshot.schema.json`
- `schemas/html-section-check.schema.json`

## Critical Schema Fix

`stage-record.schema.json` now permits:

```text
pending
running
complete
blocked
failed
```

This fixes the mismatch with `init_runtime.py`.
