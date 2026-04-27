# Test: draft is not final

**Input:** any multi-stage item.

**Expected behavior:** `draft_ready` is never treated as `complete`; final user delivery requires fact-check, citation anchors for verified claims, error audit, validation.

**Failure:** Marking `complete` right after `draft.html` or delivering user answer without verification stages.
