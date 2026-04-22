---
name: code-vuln-agent-teams-template
description: Use this skill when the user wants a generic main-agent plus subagent workflow for source-code security review, vulnerability analysis, code auditing, or building reusable agent teams for security assessment across vulnerability classes such as access control, injection, SSRF, deserialization, path traversal, and business logic flaws.
---

# Code Vulnerability Agent Teams Template

Use this skill when the goal is to build, teach, or adapt a reusable
`main agent + subagents` workflow for code security auditing.

This is a generic template. It is not tied to one vulnerability class.

## When to use

Use this skill when the task involves:

- auditing source code for security vulnerabilities
- designing a multi-agent code review workflow
- creating a reusable security-audit skill
- adapting one agent-team structure to many vulnerability classes

Do not use this skill when the task is only to explain a single bug without
needing a reusable agent-team structure.

## Main agent role

The main agent is the control plane.

It owns:

1. understanding the user goal
2. defining scope and success criteria
3. deciding whether delegation is necessary
4. selecting which specialist agents to use
5. assigning bounded tasks
6. collecting and merging results
7. deciding final findings
8. producing the final answer

The main agent should not:

- blindly trust every subagent
- skip evidence review
- let subagents write the final user-facing answer directly

## Default agent team

Use this default team unless the task clearly needs a different split:

1. `scope-agent`
2. `code-reader-agent`
3. `vulnerability-hypothesis-agent`
4. `evidence-agent`
5. `judge-agent`
6. `reporter-agent`

### Ownership

- `scope-agent`: defines review boundaries, hotspots, entrypoints, auth boundaries, and high-risk modules
- `code-reader-agent`: traces code paths, request flow, data flow, control flow, and visible checks
- `vulnerability-hypothesis-agent`: maps verified code facts to candidate vulnerability classes and exploit paths
- `evidence-agent`: deduplicates, groups, and normalizes evidence into stable finding drafts
- `judge-agent`: confirms, rejects, or downgrades candidate findings and assigns severity and confidence
- `reporter-agent`: converts accepted findings into the final human-readable result

## Standard workflow

### Step 1. Understand the task

The main agent should first determine:

- what codebase or files are in scope
- what the user wants as output
- whether a general security review or a vulnerability-specific review is needed
- whether the audit should prioritize depth, coverage, or speed

### Step 2. Decide the review shape

The main agent should decide:

- which subagents are required
- which tasks can run in parallel
- what evidence standard applies
- what output schema will be used

Use the references in this skill instead of inventing a new workflow each time.

### Step 3. Delegate bounded tasks

Only delegate tasks that are:

- narrow
- independent
- materially useful
- easy to merge later

Each subagent must receive:

- one clear question
- one bounded ownership area
- one expected output structure
- one evidence threshold

### Step 4. Collect intermediate outputs

The main agent should collect:

- scope notes
- confirmed code facts
- candidate risks
- evidence groups
- open questions

Specialist output should stay structured and compact.

### Step 5. Merge and normalize

The main agent, often with support from `evidence-agent`, should:

- remove duplicates
- separate facts from hypotheses
- group evidence by candidate finding
- mark unresolved gaps
- reject unsupported claims

### Step 6. Judge findings

The `judge-agent` or main agent should decide:

- which findings are confirmed
- which are plausible but unproven
- which are rejected
- severity
- confidence
- remediation direction

### Step 7. Produce the final answer

The final answer should contain:

- scope
- summary
- final findings
- code evidence
- impact
- remediation
- unresolved questions or assumptions

The reporter should not create new findings at this stage.

## Global constraints

- Facts before conclusions.
- Every finding must be traceable to code, configuration, or provided artifacts.
- Severity is impact; confidence is certainty.
- Subagents should not overwrite each other's responsibilities.
- Unsupported findings must be marked as unproven or rejected.
- Final user-facing conclusions must be centrally controlled.

## How to adapt this template

Adapt this skill by changing:

- the checklist in `references/vuln-checklists.md`
- the team split in `references/architecture.md`
- the role prompts in `references/prompt-templates.md`
- the field definitions in `references/output-schema.md`

Keep the overall workflow stable unless there is a strong reason to change it.

## References

- Read `references/architecture.md` for team topology and merge rules.
- Read `references/workflow.md` for the step-by-step execution flow.
- Read `references/agent-contracts.md` for ownership, forbidden actions, and input/output contracts.
- Read `references/output-schema.md` for structured output fields.
- Read `references/vuln-checklists.md` for vulnerability-class-specific review prompts.
- Read `references/prompt-templates.md` for reusable prompts.
- Read `references/example-adaptations.md` for ways to specialize this template.
