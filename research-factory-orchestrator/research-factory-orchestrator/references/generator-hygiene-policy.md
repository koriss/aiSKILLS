# Generator Hygiene Policy

Mass cleanup or replacement operations are high-risk.

Rules:

```text
1. Never run broad replacement over validators after they are written.
2. Validators must be written last or excluded from cleanup.
3. Protected zones: scripts/validate_*.py, scripts/security_*.py, package scripts, manifests, raw KB.
4. A validator may contain forbidden strings as denylist literals; code hygiene checks must understand this.
5. Current version must never appear in the forbidden denylist.
6. Self-check must scan for validator self-contradictions before packaging.
```
