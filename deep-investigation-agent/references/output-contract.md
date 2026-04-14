# Output Contract
This document defines both the human-readable report and the machine-readable object.
## Human-readable default report
Use this exact section order unless the user explicitly requests another structure.
# [Analysis Title]
## Executive Summary
3 to 8 sentences.
Lead with the main conclusion.
Include the main uncertainty.
## Question Framing
State the analytical question, scope, and limits.
## Established Facts
List only facts with solid support.
## Key Claims and Verification Status
For each important claim:
- claim
- status: confirmed / false / misleading / unverified / mixed / out-of-context
- evidence
## Timeline
Provide a dated sequence of material events.
## Actors, Interests, and Capabilities
Who matters, what they want, what they can do, what constrains them.
## Evidence Map
Strongest evidence, contradictions, gaps, and weak points.
## Competing Hypotheses
For each hypothesis:
- summary
- support
- contradictions
- assumptions
- current assessment
## Non-Obvious Links and Hidden Incentives
Only include evidence-backed links or clearly labeled inference.
## Risks, Opportunities, and Second-Order Effects
Near-term and medium-term implications.
## Forecast and Signposts
Most likely next developments and the indicators that would change the assessment.
## Bottom Line
Direct answer in plain language.
## Confidence and Unknowns
What is solid, what remains unresolved, and why.
## Sources
Group as:
- Primary
- Secondary
- Contextual
## Machine-readable object
Use keys aligned with:
`schemas/investigation_report.schema.json`
Expected shape:
- status
- main_answer
- executive_summary
- established_facts
- key_claims
- timeline
- actors
- hypotheses
- non_obvious_links
- risks
- forecast
- unknowns
- confidence
- sources
## Confidence guidance
Use:
- High
- Medium
- Low
Confidence means strength of basis, not probability of outcome.
Where forecasting matters, you may additionally use likelihood labels:
- Remote
- Unlikely
- Roughly even chance
- Likely
- Highly likely
- Nearly certain
Do not confuse likelihood with confidence.
## Brevity rule
Big output does not mean wordy output.
Aim for:
- dense evidence,
- precise wording,
- explicit uncertainty,
- minimal filler.
