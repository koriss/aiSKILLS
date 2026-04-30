
# Full Source URL Policy

The final HTML report must include full clickable URLs for sources.

Forbidden:

- source title without URL;
- abbreviated link text only;
- "source: LinkedIn" without full URL;
- source group names instead of actual source URLs;
- URL hidden only in JSON artifact but absent from HTML.

Required source table columns:

- source_id;
- title;
- source_type;
- publisher;
- full_url;
- accessed_at;
- supports_claim_ids.

Each important source must be rendered as:

```html
<a href="FULL_URL">FULL_URL</a>
```

No full source URLs in HTML = no final delivery.



Inline citation references must also expose full clickable URLs in the ordered bibliography.
