# External Patterns Review

## OpenClaw skill format

OpenClaw skills are AgentSkills-compatible folders with `SKILL.md` and YAML frontmatter. This package uses:

```text
skills/research-factory-orchestrator/SKILL.md
```

## Design decision

Earlier variants allowed adaptive/lightweight behavior. That was rejected because it reduces predictability and allows weak models to skip work.

v4-strict uses one mandatory full pipeline for every research task.

## Patterns adopted

- internal compiler + immediate execution;
- durable state and ledgers;
- mandatory full state machine;
- evidence cards;
- claims registry;
- citation locator;
- adversarial reviewer;
- final-answer gate;
- mandatory chat summary from verified claims only;
- package security checks.
