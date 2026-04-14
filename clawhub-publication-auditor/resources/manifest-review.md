# Manifest Review Guide

Use this file to quickly audit package/plugin manifest quality before ClawHub publication.

## Required checks

- name, version, description are present and meaningful
- entrypoints are explicit and resolvable in clean install
- exports map is intentional and minimal
- dependency and peer dependency contracts are explicit
- license/repository/homepage fields are present if applicable
- publish include/exclude boundaries are explicit
- no local/private paths in scripts or fields

## Blocker triggers

- missing entrypoint or broken export path
- hidden required runtime config or secrets
- workspace-only or machine-local path assumptions
- inconsistent versioning or no change story
- package payload includes private/internal files

## Major triggers

- weak description/discovery metadata
- incomplete compatibility notes
- no migration notes for breaking changes
- no install smoke-test path documented

## Fast output format

- Verdict:
- Top blockers:
- Major risks:
- Exact patch actions:
