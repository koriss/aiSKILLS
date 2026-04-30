
# Source Snapshot Policy

For auditability, preserve source evidence snapshots when allowed.

Create:

```text
source-snapshots.json
sources-cache/
```

Each snapshot should record:

- source id;
- URL/local reference;
- accessed_at;
- title;
- publisher;
- content hash if available;
- short evidence excerpt or summary;
- snapshot path if stored;
- license/access note.

Do not store large copyrighted dumps when not needed. Store short evidence excerpts and metadata.
