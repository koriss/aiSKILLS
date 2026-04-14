# Skill vs Package vs Both — Decision Guide

Use this guide before deciding what to publish.

---

## Publish as skill when

Publish as a **skill** when:
- the main value is guidance, workflow, review logic, or reusable reasoning
- the artifact is mostly markdown/text-based
- the consumer does not need executable runtime code from the artifact
- the primary goal is discoverability, invocation guidance, or reusable review/playbook logic

Good fit:
- audit skills
- writing skills
- architecture/review skills
- process skills
- evaluation playbooks

---

## Publish as package when

Publish as a **package/plugin** when:
- the main value is executable behavior
- the artifact needs entrypoints, manifests, host integration, runtime configuration, or code loading
- the consumer expects installation into a runtime
- diagnostics, compatibility, and startup behavior matter materially

Good fit:
- host extensions
- adapters
- executable tools
- runtime integrations

---

## Publish as both when

Publish as **both** when:
- there is a real executable integration
- and there is a reusable reasoning / review / operational knowledge layer worth publishing separately

Typical pattern:
- skill = how to reason about / operate / review / use the system
- package = executable implementation

Use both only if:
- docs and code can stay in sync
- public contract boundaries are clear
- examples do not drift between skill and package
- versioning story is manageable

---

## Do not publish yet when

Do not publish yet when:
- artifact boundary is unclear
- metadata is weak
- code depends on undocumented private environment
- startup/install path is not clean
- examples are misleading
- portability claims are aspirational only

---

## Quick decision checklist

- [ ] Is the main value executable?
- [ ] Is the main value instructional?
- [ ] Can the docs stand alone without the code?
- [ ] Can the code stand alone without insider docs?
- [ ] Can both stay version-aligned?

### Recommendation
- mostly instructional -> skill
- mostly executable -> package
- both independently useful and maintainable -> both
