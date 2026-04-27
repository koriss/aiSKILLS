# Tool Discovery Protocol

## Goals
Populate `tool-registry.json` with real availability and test status for the current environment.

## Categories to detect (best-effort, tool-agnostic)
- Web / search; browser / fetch; local filesystem; user uploads; shell `curl`/`wget`; no external access.

## Each tool entry
`tool_name`, `available` (bool), `trust_level`, `allowed_actions`, `write_access`, `risk`, `fallback`, `test_status` (`passed|failed|not_tested`).

## Policy
Select strongest **read-consistent** path for evidence collection. If none: enter **source-limited** mode; do not invent URLs.
