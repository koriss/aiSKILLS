# ClawHub Publication Checklist

Use this checklist before publishing anything to ClawHub.

---

## 0. Publication target

- [ ] Publication target is explicit: `skill` / `package` / `both`
- [ ] Publication root directory is explicit
- [ ] Public artifact boundary is clear
- [ ] Internal-only files are excluded from public scope

---

## 1. Identity and registry surface

- [ ] Name is stable and human-readable
- [ ] Slug is lowercase and registry-safe
- [ ] Description is specific and useful for search/discovery
- [ ] Version is present and follows intended release strategy
- [ ] Changelog or release summary exists
- [ ] Tags/category labels are appropriate
- [ ] The artifact can be understood in under 20 seconds from metadata alone

Blockers:
- missing name/slug/version
- vague or misleading description
- ambiguous publication target

---

## 2. Skill-specific checklist

Apply only if publishing a skill.

### 2.1 SKILL.md quality

- [ ] `SKILL.md` exists
- [ ] Frontmatter/metadata is valid if used
- [ ] Clear one-line description exists
- [ ] Role/purpose is explicit
- [ ] "When to use" is explicit
- [ ] "Do not use when" is explicit
- [ ] Inputs/prerequisites are explicit
- [ ] Output expectations are explicit
- [ ] Sharp edges / limitations are explicit
- [ ] Related skills are listed if relevant

### 2.2 Skill usability

- [ ] At least one realistic example exists
- [ ] Examples reflect actual expected usage
- [ ] Terminology is consistent with docs/contracts
- [ ] Supporting files are text-based and relevant
- [ ] No internal notes or scratch content leak into public artifact

Blockers:
- missing `SKILL.md`
- skill does not explain when to invoke it
- examples contradict behavior

---

## 3. Package / plugin-specific checklist

Apply only if publishing a package/plugin.

### 3.1 Manifest and packaging

- [ ] Manifest exists (`package.json` or equivalent)
- [ ] Entrypoint/module path is explicit
- [ ] Package exports are correct
- [ ] Required config keys are documented
- [ ] Optional config keys are documented
- [ ] Feature flags are documented
- [ ] Required secrets/material are documented
- [ ] Publish/include/exclude rules are correct
- [ ] Local-only paths are not required
- [ ] Build artifacts are present if publish requires them

### 3.2 Startup and runtime

- [ ] Startup validation exists
- [ ] Missing required config fails clearly
- [ ] Unsupported host/runtime fails clearly
- [ ] Readiness checks exist before traffic exposure
- [ ] Degraded mode is explicit if supported
- [ ] Shutdown behavior is defined if relevant
- [ ] Diagnostics are available

Blockers:
- no clear entrypoint
- hidden required env/config
- startup depends on undocumented environment
- unsupported host behavior is silent

---

## 4. Host integration checklist

- [ ] Supported host/runtime range is documented
- [ ] Compatibility window is documented
- [ ] Required capabilities are documented
- [ ] Optional capabilities are documented
- [ ] Unsupported combinations are documented
- [ ] Capability negotiation result is defined
- [ ] Degraded mode is explicit
- [ ] Delivery semantics are documented
- [ ] Event normalization contract is documented
- [ ] Public behavior does not depend on hidden host assumptions

Blockers:
- host compatibility undefined
- capability assumptions hidden
- degraded mode silent or misleading

---

## 5. Config and installability checklist

- [ ] Clean install path is documented
- [ ] Clean startup path is documented
- [ ] Example config exists
- [ ] Config validation behavior is documented
- [ ] Secret vs non-secret config is separated
- [ ] Unsupported config combinations are documented
- [ ] First-success smoke path is documented
- [ ] Troubleshooting path exists for common failures

Blockers:
- cannot install/run from clean environment
- config surface is incomplete or ambiguous
- no first-success validation path

---

## 6. Documentation UX checklist

- [ ] README or equivalent overview exists
- [ ] Quick start exists
- [ ] Installation steps exist
- [ ] Configuration steps exist
- [ ] Minimal example exists
- [ ] Limitations are stated honestly
- [ ] Troubleshooting section exists
- [ ] Diagnostics section exists
- [ ] Upgrade/migration notes exist when relevant
- [ ] Docs do not assume insider knowledge

Majors:
- docs technically exist but are not enough for a new user
- docs hide limitations or degraded behavior

---

## 7. Examples checklist

- [ ] At least one realistic success-path example exists
- [ ] At least one config example exists if configuration is required
- [ ] Examples are consistent with real contracts and naming
- [ ] Failure/degraded examples exist if behavior is non-trivial
- [ ] Example commands/config are copyable with minimal edits

Majors:
- examples are toy-only
- examples drift from actual public interface

---

## 8. Security publication checklist

- [ ] Safe defaults are used
- [ ] Secrets are not embedded in docs/examples
- [ ] Logs do not expose tokens/secret material
- [ ] Public examples do not encourage insecure patterns
- [ ] Validation rules are explicit for untrusted inputs
- [ ] Permissions/capability requirements are no broader than needed
- [ ] Dangerous debug behavior is documented or disabled by default

Blockers:
- secrets in examples or package payload
- unsafe default behavior
- auth/security assumptions omitted from public docs

---

## 9. Diagnostics and supportability checklist

- [ ] Startup status can be inspected
- [ ] Readiness status can be inspected
- [ ] Config failures are actionable
- [ ] Capability/degraded mode is inspectable
- [ ] Diagnostic output is understandable by non-author
- [ ] Common failure modes are documented
- [ ] Correlation or trace fields exist when relevant
- [ ] Operator path is clear enough for support

Majors:
- public users would need author help for routine failures
- diagnostics exist but are not documented

---

## 10. Versioning and release checklist

- [ ] Version is incremented intentionally
- [ ] Release notes or changelog summary exists
- [ ] Breaking changes are called out
- [ ] Migration notes exist for breaking changes
- [ ] Deprecated behavior is documented
- [ ] Compatibility notes are present
- [ ] Public artifact does not silently change contract without version story

Blockers:
- breaking changes with no migration notes
- versioning present but meaningless or contradictory

---

## 11. Artifact hygiene checklist

- [ ] No editor junk / temp files
- [ ] No local environment files
- [ ] No accidental private notes
- [ ] No binaries unless intentionally required
- [ ] No internal-only references that break outside repo
- [ ] Public payload is minimal and relevant

Majors:
- publish root is cluttered enough to confuse consumers
- internal artifacts leak into release

---

## 12. Portability checklist

- [ ] Artifact can be understood outside original repo context
- [ ] Artifact can run outside author machine assumptions
- [ ] Repo-relative assumptions are documented or removed
- [ ] Internal service dependencies are documented
- [ ] Storage/runtime assumptions are explicit
- [ ] Portability claims match actual evidence

Majors:
- portability is claimed but not supported by docs/contracts/tests

---

## 13. Final publication decision

### Publication status
- [ ] Not publishable
- [ ] Publishable with blockers
- [ ] Publishable with majors
- [ ] Publishable with minors
- [ ] Publication-ready

### Required next actions
- [ ] Blockers resolved
- [ ] Major doc/config issues resolved
- [ ] Release notes prepared
- [ ] Final smoke/install test completed
- [ ] Final metadata reviewed
- [ ] Public artifact boundary reviewed

---

## Minimal blocker summary template

- Blocker 1:
- Blocker 2:
- Blocker 3:

## Minimal major summary template

- Major 1:
- Major 2:
- Major 3:

## Final recommendation template

- Publication target:
- Verdict:
- Recommended action:
