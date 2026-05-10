# Canonical work roots — RFO skill package vs monorepo

All `python3 -S scripts/...`, `validate_skill`, and unittest commands assume **`cwd`** is the **inner** skill package directory (the tree that contains `runtime/`, `scripts/`, `contracts/`):

| Layer | Absolute path (this maintainer checkout) |
|-------|------------------------------------------|
| Git monorepo root (`aiSKILLS`) | `/home/kazak/_projects/aiSKILLS` |
| RFO skill package (operator `cwd`) | `/home/kazak/_projects/aiSKILLS/research-factory-orchestrator/research-factory-orchestrator` |

Do not treat arbitrary workspace copies under a host deployment tree as the git source of truth; edit canonical sources here, then sync deploy trees per operator policy.
