
# Stage Record Hash Policy

Each stage writes a separate record under:

```text
stage-records/<NN>-<stage-name>.json
```

A completed stage must include stage name, status, required artifacts, artifact paths, sha256, byte size, record count when applicable, validator name, validator status, validator transcript reference, and timestamp.

No artifact hash = stage not complete.
