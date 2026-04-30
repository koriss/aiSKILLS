
# Full HTML Report Contract

The complete standalone HTML report is mandatory for every final delivery.

The HTML report is the primary full report.

The chat summary is not a replacement for the HTML report.

## Required output

```text
items/<item_slug>/full-report.html
```

or an equivalent final HTML path recorded in:

```text
items/<item_slug>/html-report-delivery.json
artifact-manifest.json
```

## Required sections

The report must be readable independently without chat context.

Required sections, when applicable:

1. Title and metadata.
2. Executive summary.
3. Research question and scope.
4. Methodology.
5. Search strategy.
6. Source acquisition summary.
7. Source quality and source-laundering assessment.
8. Evidence map.
9. Verified claims.
10. Uncertain/disputed claims.
11. Fact-check results.
12. Citation locator and source anchors.
13. Adversarial review summary.
14. Error audit summary.
15. Final assessment.
16. Known gaps and limitations.
17. Complete source list.
18. Appendices/tables/datasets when useful.

## Delivery rule

Final chat response must include both:

```text
1. detailed summary in chat;
2. link/path/attachment to full HTML report.
```

Supporting artifacts may also be linked, but they do not replace the full HTML report.

## Blocking conditions

Do not mark task delivered if:

- no full HTML report exists;
- HTML report is only a short summary;
- HTML report lacks sources;
- HTML report lacks verified claims;
- HTML report lacks fact-check summary;
- HTML report lacks citation/source anchors;
- HTML report lacks limitations/gaps;
- chat response does not link/reference the HTML report.

No full HTML report = no final delivery.


## Required validation proof section

The full HTML report must include a validation proof section with stage/artifact/validator/status/hash table.



## Full source links

The HTML report must include full clickable URLs for all sources in the source table.
