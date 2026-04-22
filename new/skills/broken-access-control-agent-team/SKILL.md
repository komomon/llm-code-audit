---
name: broken-access-control-agent-team
description: Use this skill when the user wants a main-agent plus subagent workflow to audit source code for broken access control, IDOR, horizontal privilege escalation, vertical privilege escalation, tenant-isolation failures, missing server-side authorization, or related authorization logic flaws.
---

# Broken Access Control Agent Team

Use this skill when the task is to audit source code for authorization flaws.

This skill is specialized for code review and vulnerability analysis of:

- broken access control
- IDOR
- horizontal privilege escalation
- vertical privilege escalation
- tenant-isolation failures
- missing ownership checks
- missing server-side authorization
- approval-flow bypass caused by weak authorization logic

This skill is not for auditing LLM systems themselves. It is for using an LLM
agent team to audit normal application code.

## When to use

Use this skill when the user asks to:

- audit code for access-control bugs
- review routes, handlers, services, or repositories for authorization flaws
- inspect whether a user can read, modify, delete, or approve another user's resources
- build a reusable agent-team workflow for authorization reviews

Do not use this skill when:

- the task is a generic code explanation with no security goal
- the task is dominated by non-authorization vulnerability classes
- there is no meaningful code or artifact to review

## Main agent role

The main agent is the control plane.

It owns:

1. understanding the audit request
2. defining scope and review depth
3. deciding which subagents to use
4. delegating bounded review tasks
5. collecting facts, hypotheses, and evidence
6. merging outputs into candidate findings
7. deciding final findings
8. producing the final answer

The main agent should not:

- blindly trust every subagent
- skip evidence review
- let subagents write the final report directly
- treat weak hypotheses as confirmed vulnerabilities

## Default agent team

Use this default team unless the task clearly needs a different split:

1. `scope-agent`
2. `authz-mapper-agent`
3. `code-path-agent`
4. `access-control-hypothesis-agent`
5. `evidence-agent`
6. `judge-agent`
7. `reporter-agent`

### Ownership

- `scope-agent`: finds routes, controllers, services, repositories, background jobs, and hotspots where authorization should exist
- `authz-mapper-agent`: maps authentication, authorization, ownership, role, tenant, and approval boundaries
- `code-path-agent`: traces request-to-sink paths and identifies where sensitive reads or writes happen
- `access-control-hypothesis-agent`: turns verified code facts into candidate BAC, IDOR, tenant-breakout, and privilege-escalation findings
- `evidence-agent`: groups evidence, removes duplicates, and normalizes finding drafts
- `judge-agent`: confirms, rejects, or downgrades findings and assigns severity and confidence
- `reporter-agent`: produces the final human-readable report from accepted findings only

## Standard workflow

### Step 1. Understand the target

The main agent should determine:

- which files, modules, or services are in scope
- whether the user wants a broad review or a targeted review
- whether the main concern is read access, write access, admin access, tenant isolation, or approval flow
- what kind of deliverable is expected

### Step 2. Plan the review

The main agent should decide:

- which endpoints or code paths to inspect first
- which subagents can run in parallel
- what evidence standard applies
- what output schema should be used

### Step 3. Delegate bounded tasks

Each subagent must receive:

- a narrow question
- a narrow ownership area
- the relevant files or artifacts
- the required output structure
- the evidence threshold

### Step 4. Collect intermediate outputs

The main agent should collect:

- scope notes
- authorization-boundary facts
- code-path facts
- candidate vulnerabilities
- traceable evidence
- open questions

### Step 5. Merge and normalize

The main agent with support from `evidence-agent` should:

- remove duplicates
- separate facts from hypotheses
- group evidence by candidate finding
- identify unresolved gaps
- discard unsupported claims

### Step 6. Judge findings

The `judge-agent` should decide:

- which findings are confirmed
- which are plausible but unproven
- which are rejected
- severity
- confidence
- remediation direction

### Step 7. Produce the final answer

The final answer should include:

- scope
- executive summary
- confirmed findings
- code evidence
- exploit impact
- remediation guidance
- unresolved assumptions or questions

The reporter should not invent new findings at this stage.

## Global constraints

- Facts before conclusions.
- Every finding must be traceable to code, configuration, or provided artifacts.
- Severity is impact; confidence is certainty.
- Ownership, tenant, role, and approval checks should be analyzed separately when needed.
- Subagents must stay inside their roles.
- Unsupported findings must be marked as unproven or rejected.
- Final user-facing conclusions must be centrally controlled.

## Recommended review priorities

Review these high-risk areas first:

- update, delete, approve, refund, export, or admin endpoints
- object fetches by user-controlled IDs
- service-layer mutations
- repository queries missing ownership or tenant scope
- admin or staff-only flows
- batch operations and background jobs

## References

- Read `references/architecture.md` for team topology and merge rules.
- Read `references/workflow.md` for the end-to-end BAC review flow.
- Read `references/agent-contracts.md` for ownership and forbidden actions.
- Read `references/output-schema.md` for stable output fields.
- Read `references/access-control-checklist.md` for review prompts specific to broken access control.
- Read `references/finding-rubric.md` for severity and confidence rules.
- Read `references/prompt-templates.md` for reusable prompts.
- Read `references/dispatch-examples.md` for concrete main-agent task assignment examples.
- Read `references/subagent-output-examples.md` for concrete example outputs from each specialist agent.
- Read `references/main-agent-decision-rules.md` for planning, delegation, escalation, and confidence-control rules.
- Read `references/main-agent-playbook.md` for a practical step-by-step operating handbook for the main agent.
- Read `references/example-flows.md` for concrete task patterns.
- Read `references/execution-demo.md` for a realistic end-to-end main-agent execution example.
