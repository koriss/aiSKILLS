# Self Audit

## Critical failures fixed

1. Adaptive/lightweight mode removed.
2. Shortcut stages removed.
3. Optional core stages removed.
4. Full stage list made mandatory.
5. Stage-record contract added.
6. Search strategy fixed by mandatory query families.
7. Universal domains supported without hardcoded search recipes.
8. Final-answer gate is mandatory.
9. Adversarial review is mandatory.
10. Chat summary cannot add new facts.
11. Source laundering detector added.
12. Staleness gate added.
13. Strict enum schemas added.
14. Package validator rejects unsafe paths and symlinks.
15. Install script validates skill after copy.

## Remaining risk

Actual research depth still depends on hosting OpenClaw tools and model compliance, but the skill no longer gives the model permission to simplify the workflow.
