# ClawHub Publication Audit Findings Template

Use this template to produce consistent publication-readiness audits.

---

## Audit Result

### Publication target
- `skill | package | both`

### Scope reviewed
- publication root:
- reviewed artifacts:
- reviewed code surfaces:
- reviewed docs:
- reviewed manifests:
- reviewed host/runtime assumptions:

### Verdict
- `not publishable | publishable with blockers | publishable with majors | publishable with minors | publication-ready`

### Release recommendation
- `do not publish`
- `publish after blockers resolved`
- `publish after documentation/metadata cleanup`
- `safe to publish`

---

## 1. Blocking findings

### B-001 — [Title]

**Severity:** blocker  
**Area:** metadata / packaging / host integration / config / docs / security / portability / diagnostics

**What is wrong**
- 

**Why it blocks publication**
- 

**Affected artifacts**
- 
- 

**Consumer impact**
- install failure / startup failure / broken discovery / security risk / hidden incompatibility / misleading package

**Exact fix**
- 

**Verification after fix**
- 

---

### B-002 — [Title]

**Severity:** blocker  
**Area:** 

**What is wrong**
- 

**Why it blocks publication**
- 

**Affected artifacts**
- 

**Consumer impact**
- 

**Exact fix**
- 

**Verification after fix**
- 

---

## 2. Major findings

### M-001 — [Title]

**Severity:** major  
**Area:** 

**What is wrong**
- 

**Why it matters**
- 

**Affected artifacts**
- 

**Consumer impact**
- confusion / degraded UX / support burden / misconfiguration / portability pain

**Exact fix**
- 

**Verification after fix**
- 

---

### M-002 — [Title]

**Severity:** major  
**Area:** 

**What is wrong**
- 

**Why it matters**
- 

**Affected artifacts**
- 

**Consumer impact**
- 

**Exact fix**
- 

**Verification after fix**
- 

---

## 3. Minor findings

### m-001 — [Title]

**Severity:** minor  
**Area:** 

**What is wrong**
- 

**Why it matters**
- 

**Affected artifacts**
- 

**Exact fix**
- 

---

### m-002 — [Title]

**Severity:** minor  
**Area:** 

**What is wrong**
- 

**Why it matters**
- 

**Affected artifacts**
- 

**Exact fix**
- 

---

## 4. Notes

### N-001 — [Title]
- 

### N-002 — [Title]
- 

---

## 5. Strong points

1. 
2. 
3. 
4. 
5. 

---

## 6. Evidence gaps

List anything that could not be verified.

### E-001 — Missing evidence
**Missing artifact or proof**
- 

**Why it matters**
- 

**What would verify it**
- 

---

### E-002 — Missing evidence
**Missing artifact or proof**
- 

**Why it matters**
- 

**What would verify it**
- 

---

## 7. Publication-readiness by lens

| Lens | Status | Notes |
|---|---|---|
| Registry readiness | pass / warn / fail |  |
| Skill metadata quality | pass / warn / fail |  |
| Package manifest quality | pass / warn / fail |  |
| Host compatibility | pass / warn / fail |  |
| Capability negotiation | pass / warn / fail |  |
| Event normalization | pass / warn / fail |  |
| Delivery semantics | pass / warn / fail |  |
| Installability | pass / warn / fail |  |
| Config surface | pass / warn / fail |  |
| Documentation UX | pass / warn / fail |  |
| Example quality | pass / warn / fail |  |
| Security publication posture | pass / warn / fail |  |
| Diagnostics/supportability | pass / warn / fail |  |
| Observability consistency | pass / warn / fail |  |
| Versioning/upgrade safety | pass / warn / fail |  |
| Artifact hygiene | pass / warn / fail |  |
| Portability | pass / warn / fail |  |
| Public support burden | pass / warn / fail |  |
| Maintainability | pass / warn / fail |  |
| Publication honesty | pass / warn / fail |  |

---

## 8. Recommended next patch-set

Prioritize only the most important actions.

1. 
2. 
3. 
4. 
5. 

Optional follow-up actions:
- 
- 
- 

---

## 9. Final publication summary

### Summary
- 

### Should this be published now?
- yes / no / only after blockers

### Best publication path
- skill only
- package only
- both
- neither yet

### Short recommendation
- 
