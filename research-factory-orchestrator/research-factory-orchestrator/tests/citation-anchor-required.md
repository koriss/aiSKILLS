# Test: citation anchor required

**Input:** a claim marked confirmed/partially_confirmed in output.

**Expected behavior:** claim has `source_id`, URL or `local_ref`, `evidence_anchor`, `evidence_summary` in citation locator output; otherwise verification status must be lower or claim removed.

**Failure:** "verified" claim with URL only and no anchor; post-hoc citation without path from evidence note.
