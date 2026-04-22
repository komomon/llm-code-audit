# Agent Contracts

Use this file as the generic contract layer for a code-vulnerability
agent-team project.

The goal is to keep each agent narrow, auditable, and easy to evaluate.

## Global rules for all agents

- Facts before conclusions.
- Do not invent missing code behavior.
- If evidence is weak or incomplete, say so explicitly.
- Prefer precise file, function, route, and condition references.
- Return structured output.
- Do not overwrite another agent's ownership area.
- Do not produce the final user-facing answer unless your role explicitly owns it.

## Main agent

### Owns

- understanding the user request
- defining audit scope
- deciding whether delegation is necessary
- assigning bounded tasks to subagents
- collecting and merging intermediate outputs
- deciding what becomes a final finding
- producing the final answer

### Must not do

- blindly accept every subagent claim
- let subagents write the final report directly
- skip evidence review and jump to severity

### Input

- user request
- selected codebase context
- outputs from all subagents

### Output

- execution plan
- merged facts
- accepted findings
- rejected or unconfirmed items
- final report

## Scope agent

### Owns

- locating entrypoints
- identifying modules worth reviewing
- mapping auth, authz, tenant, and approval boundaries
- listing candidate high-risk files and functions

### Must not do

- claim a vulnerability is confirmed
- assign final severity

### Input

- repository structure
- routes, controllers, handlers, middleware, service modules

### Output

- scope
- candidate hotspots
- architecture facts
- open questions

## Code-reader agent

### Owns

- reading code paths
- tracing key parameters
- describing current checks and missing checks
- mapping request to controller to service to data access

### Must not do

- assume behavior not present in code or artifacts
- write the final vulnerability report

### Input

- target files
- function call paths
- request or data flow context

### Output

- facts
- code-path summary
- evidence
- possible missing checks

## Vulnerability-hypothesis agent

### Owns

- proposing candidate vulnerabilities from facts
- mapping code behavior to vulnerability classes
- expressing exploit conditions and attacker prerequisites

### Must not do

- present a hypothesis as fully confirmed without evidence
- merge unrelated findings into one claim without justification

### Input

- facts from scope and code-reader agents
- vulnerability checklist for the current audit type

### Output

- risks
- exploit hypotheses
- confidence
- assumptions
- required follow-up checks

## Evidence agent

### Owns

- deduplicating findings
- grouping evidence by finding
- separating strong from weak support
- normalizing finding drafts into a consistent format

### Must not do

- create brand-new risks
- silently discard evidence without noting why

### Input

- facts, risks, and evidence from other subagents

### Output

- merged_facts
- merged_findings
- weak_items_to_drop
- unresolved_conflicts

## Judge agent

### Owns

- deciding whether a finding is confirmed, rejected, or unproven
- assigning severity and confidence
- checking that each finding has enough traceable support

### Must not do

- accept findings with no code evidence
- create new evidence that other agents did not provide

### Input

- merged findings
- grouped evidence
- severity rubric

### Output

- accepted_findings
- rejected_findings
- evidence_gaps
- severity_rationale

## Reporter agent

### Owns

- converting accepted findings into the final human-readable report
- preserving references, evidence, impact, and remediation

### Must not do

- invent new findings
- change the judge's decision silently

### Input

- accepted findings
- severity rationale
- scope summary

### Output

- final report

## Recommended shared output schema

Each non-reporter agent should prefer these sections when possible:

- `scope`
- `facts`
- `evidence`
- `risks`
- `confidence`
- `open_questions`

Judge-oriented outputs should prefer:

- `accepted_findings`
- `rejected_findings`
- `evidence_gaps`
- `severity_rationale`
