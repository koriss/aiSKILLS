
# Artifact Manifest Validation

Artifact manifest must match real files.

Checks:

- every artifact path exists;
- every role is allowed;
- checksum exists for final artifacts when possible;
- final/full-report is not a draft;
- HTML report path matches final-answer gate;
- referenced artifacts are present.
