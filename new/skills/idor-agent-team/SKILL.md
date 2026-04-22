---
name: idor-agent-team
description: Use this skill when the user wants a main-agent plus subagent workflow specialized for IDOR and object-level authorization reviews, especially when the codebase is large enough that the audit should be decomposed into narrow lanes such as input-parameter analysis, auth-context analysis, call-chain tracing, input-to-auth relation checks, output-to-auth relation checks, evidence merge, and final judgment.
---

# IDOR Agent Team

Use this skill when the task is to audit source code for:

- IDOR
- object-level authorization flaws
- resource ownership bypass
- route-parameter-based unauthorized access
- data exposure or mutation caused by unscoped object lookup

This skill is specialized for **fine-grained decomposition**.

It is designed for situations where the model context is limited and a single
"read the whole path and decide" agent would be too broad or too noisy.

## Why this skill exists

For many IDOR reviews, a single large review lane is not enough.

A better split is often:

1. analyze attacker-controlled input parameters
2. analyze trusted authentication and identity context
3. trace the call chain
4. compare input parameters with trusted auth parameters
5. compare outputs or accessed objects with trusted auth parameters
6. synthesize evidence and decide whether IDOR exists

This skill treats that decomposition as a first-class design.

## When to use

Use this skill when the user asks to:

- review code for IDOR
- inspect object-level authorization
- verify whether user-controlled IDs are properly scoped to the caller
- audit whether returned or mutated resources belong to the authenticated user or tenant
- build a reusable multi-agent workflow for IDOR-style reviews

Do not use this skill when:

- the main issue is not object-level authorization
- there is no meaningful request path or resource access logic to inspect
- the task is a broad generic security review better served by a wider BAC workflow

## Main agent role

The main agent is the control plane.

It owns:

1. understanding the audit request
2. defining scope and review depth
3. deciding whether to activate the full fine-grained team
4. delegating narrow tasks
5. merging facts from multiple lanes
6. separating stable facts from hypotheses
7. deciding final findings
8. producing the final answer

The main agent should not:

- skip the relation checks between input and trusted identity
- blindly promote weak hypotheses into findings
- let subagents write the final report directly

## Default fine-grained agent team

Use this team when the path is long enough or the repo is large enough that
context should be split deliberately:

1. `scope-agent`
2. `input-parameter-agent`
3. `auth-context-agent`
4. `call-chain-agent`
5. `input-auth-relation-agent`
6. `output-auth-relation-agent`
7. `idor-hypothesis-agent`
8. `evidence-agent`
9. `judge-agent`
10. `reporter-agent`

### Ownership

- `scope-agent`: identifies relevant routes, handlers, services, repositories, serializers, and hotspots
- `input-parameter-agent`: tracks attacker-controlled IDs, filters, and selectors from route, query, form, or JSON input
- `auth-context-agent`: identifies trusted identity data such as `current_user`, `account_id`, `tenant_id`, role, or session-derived context
- `call-chain-agent`: traces how request input and auth context move through the code path
- `input-auth-relation-agent`: checks whether attacker-controlled resource identifiers are compared, constrained, or joined to trusted identity context before access
- `output-auth-relation-agent`: checks whether the accessed, returned, or mutated object is actually scoped to the trusted identity context
- `idor-hypothesis-agent`: turns verified facts into candidate IDOR findings
- `evidence-agent`: deduplicates, groups, and normalizes evidence
- `judge-agent`: confirms, rejects, or downgrades findings and assigns severity and confidence
- `reporter-agent`: writes the final human-readable result from accepted findings only

## Standard workflow

### Step 1. Understand the target

The main agent should determine:

- which route or flow is in scope
- whether the concern is read, download, update, delete, or export access
- which identifiers are likely attacker-controlled
- which authenticated identity values are likely trusted

### Step 2. Choose review shape

For small code paths, the main agent may compress some lanes.

For larger or ambiguous flows, the main agent should activate the full
fine-grained team so that:

- input analysis stays narrow
- auth-context analysis stays narrow
- call-chain tracing stays narrow
- relation checks are not lost in the noise

### Step 3. Dispatch narrow lanes

Each subagent should receive:

- one bounded question
- one bounded ownership area
- relevant files only
- an explicit output structure
- an explicit evidence rule

### Step 4. Stabilize facts

The main agent should first stabilize:

- which identifiers are user-controlled
- which identity fields are trusted
- where objects are fetched or mutated
- where results are returned or serialized

### Step 5. Run relation checks

The main agent should treat these as mandatory for IDOR:

- input-to-auth relation
- output-to-auth relation

Without these checks, the review risks becoming a shallow "I saw an id" pass.

### Step 6. Generate and judge findings

Only after the facts and relation checks are stable should the team:

- generate candidate IDOR findings
- normalize evidence
- judge validity

### Step 7. Produce the final answer

The final answer should include:

- scope
- executive summary
- confirmed findings
- code evidence
- exploit path
- remediation guidance
- unresolved assumptions or missing layers

## Global constraints

- Facts before conclusions.
- User-controlled identifiers and trusted identity fields must be analyzed separately.
- Severity is impact; confidence is certainty.
- Relation checks are mandatory for strong IDOR analysis.
- Unsupported findings must be marked as unproven or rejected.
- Final user-facing conclusions must be centrally controlled.

## Recommended review priorities

Review these high-risk patterns first:

- fetch by route-controlled `id`
- download by object id
- update or delete by object id
- export, invoice, ticket, order, file, or document read paths
- repository queries with no owner or tenant scoping
- serializers returning fetched objects without identity-bound filtering

## References

- Read `references/architecture.md` for the fine-grained team topology.
- Read `references/workflow.md` for the end-to-end IDOR review flow.
- Read `references/agent-contracts.md` for role boundaries and forbidden actions.
- Read `references/output-schema.md` for stable output fields.
- Read `references/idor-checklist.md` for IDOR-specific review prompts.
- Read `references/prompt-templates.md` for reusable prompts.
- Read `references/dispatch-examples.md` for concrete main-agent task assignments.
- Read `references/subagent-output-examples.md` for examples of good specialist outputs.
- Read `references/main-agent-decision-rules.md` for planning, decomposition, and confidence-control rules for fine-grained IDOR review.
- Read `references/main-agent-playbook.md` for a practical operating handbook for the main agent.
- Read `references/execution-demo.md` for a realistic end-to-end execution example.
