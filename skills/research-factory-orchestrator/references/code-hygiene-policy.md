# Code Hygiene Policy

Before packaging, run code hygiene checks:

```text
stale version scan
forbidden shortcut mode scan
external KB dependency scan
self-forbidden current version scan
protected-zone cleanup scan
schema JSON parse
zip path traversal scan
symlink scan
standalone HTML validator smoke test
Telegram delivery validator smoke test
```

Do not treat denylist strings inside validator source as normal runtime claims.
