
# HTML Report Delivery Audit

## Problem found

v4-strict required a mandatory chat summary but did not make the full standalone HTML report an explicit mandatory final deliverable.

This could allow weak agents to stop with only a chat answer or a short summary.

## Fix in v5

v5 adds:

- mandatory full HTML report delivery;
- `references/full-html-report-contract.md`;
- `schemas/html-report-delivery.schema.json`;
- `schemas/full-html-report.schema.json`;
- `items/<item_slug>/full-report.html`;
- `items/<item_slug>/html-report-delivery.json`;
- final-answer-gate checks for HTML report existence and chat link;
- explicit blocking rule: no full HTML report = no final delivery.

## Final delivery model

Final delivery now requires both:

1. detailed chat summary;
2. complete standalone HTML report.

The HTML report is the full final report.
The chat summary is not a replacement.
