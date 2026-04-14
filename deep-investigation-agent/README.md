# Deep Investigation Agent
A skill package for agentic research and analysis.
This package is built for multi-step agents, not just chat prompts. It gives the agent a compact runtime contract plus deeper reference material for methodology, source criticism, competing hypotheses, output structure, and validation.
## What this skill is for
Use it when you need:
- deep research on contested or high-ambiguity topics;
- evidence-grounded analysis instead of surface summaries;
- explicit source verification and uncertainty handling;
- competing hypotheses rather than single-story answers;
- outputs that can be consumed both by humans and downstream systems.
Typical domains:
- geopolitics
- macroeconomics
- finance and ownership
- sanctions and trade
- corporate investigations
- medicine and epidemics
- technology and cyber
- humanitarian and food-security analysis
- narrative and influence analysis
## Package structure
- `SKILL.md` — compact runtime contract for the agent
- `references/` — detailed methodological playbooks
- `schemas/` — structured output schema
- `scripts/` — validation scripts
- `examples/` — example request and outputs
## Design principles
This package treats prompts as operational specifications.
That means:
- bounded loops instead of open-ended autonomy,
- explicit stop conditions,
- source hierarchy,
- memory discipline,
- quality gates,
- structured outputs,
- validation before trust.
## Suggested usage pattern
Use a single primary agent by default.
Escalate to multi-agent orchestration only when the task clearly benefits from specialization, for example:
- one planner,
- one researcher,
- one verifier,
- one challenger,
- one synthesizer.
Do not split into many agents unless the task complexity justifies the coordination overhead.
## Human-facing report sections
The default report format is:
1. Executive Summary
2. Question Framing
3. Established Facts
4. Key Claims and Verification Status
5. Timeline
6. Actors, Interests, and Capabilities
7. Evidence Map
8. Competing Hypotheses
9. Non-Obvious Links and Hidden Incentives
10. Risks, Opportunities, and Second-Order Effects
11. Forecast and Signposts
12. Bottom Line
13. Confidence and Unknowns
14. Sources
## Machine-readable output
Use the schema in:
`schemas/investigation_report.schema.json`
This is intentionally simple and validator-friendly.
## Validation
Run (из корня репозитория `aiSKILLS`):
python3 deep-investigation-agent/scripts/check_skill.py deep-investigation-agent
python3 deep-investigation-agent/scripts/validate_report.py --selftest
To validate a JSON report:
python3 deep-investigation-agent/scripts/validate_report.py deep-investigation-agent/examples/example-report.json
To validate a Markdown report:
python3 deep-investigation-agent/scripts/validate_report.py deep-investigation-agent/examples/example-report.md
## Notes for Cursor or other agentic IDE workflows
This package is repository-local and tool-agnostic.
You can:
- keep it under `skills/`,
- adapt it into your agent framework,
- or mirror the runtime contract into your own agent system prompt while preserving the references and validators as supporting assets.
## Minimal operator instruction
Use the `deep-investigation-agent` skill for high-stakes analytical tasks. Follow the runtime workflow, respect source hierarchy, generate competing hypotheses, and finalize only after quality gates pass.
