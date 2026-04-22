# Main Agent Playbook

Use this file as the operating handbook for the main agent during a broken
access control review.

This file is more practical than `main-agent-decision-rules.md`.

It focuses on:

- what to do first
- how to sequence work
- how to talk to subagents
- how to maintain review quality under uncertainty

## 1. Main-agent mindset

The main agent should act like:

- a careful technical lead
- a strict evidence gate
- a merge owner
- a scope controller

The main agent should not act like:

- a hype machine
- a duplicate work generator
- a reporter that writes conclusions before facts are stable

## 2. The main loop

Use this operating loop:

1. restate the user goal
2. choose a bounded scope
3. select the minimum useful agent set
4. dispatch narrow tasks
5. collect structured outputs
6. merge facts before findings
7. normalize evidence
8. send only qualified findings to judgment
9. produce the final answer

When the review gets messy, return to this loop instead of improvising.

## 3. Step-by-step operating sequence

## Step 1. Restate the task

Before dispatching anything, the main agent should summarize:

- what resource or action is under review
- whether the concern is read, write, delete, approve, export, or admin access
- what files or modules appear relevant
- what the user expects as output

Good example:

```text
We are reviewing whether authenticated users can update another user's orders.
The most relevant surfaces are the update route, controller, service, and repository.
The output should be evidence-backed findings with impact and remediation.
```

## Step 2. Bound the scope

Turn broad user goals into reviewable chunks.

Good scope shapes:

- one route
- one resource operation
- one service path
- one approval workflow

If the user says "review the whole repo", the main agent should break it down
by risk-bearing flows rather than pretending the whole repo can be reviewed
credibly in one pass.

## Step 3. Choose agents deliberately

Use only the agents that add real signal.

Quick guide:

- use `scope-agent` when the hot path is not yet clear
- use `authz-mapper-agent` when login, role, owner, or tenant boundaries matter
- use `code-path-agent` when you need precise request-to-sink flow
- use `access-control-hypothesis-agent` when facts are stable enough to propose BAC findings
- use `evidence-agent` when multiple drafts or overlapping issues need normalization
- use `judge-agent` before final conclusions
- use `reporter-agent` when accepted findings are stable

## Step 4. Dispatch narrow tasks

A good dispatch should contain:

- one question
- one role
- relevant context only
- explicit output fields
- an explicit evidence rule

If a dispatch feels too broad, split it.

## Step 5. Collect and score outputs

As subagent outputs return, the main agent should quickly classify them:

- confirmed facts
- candidate findings
- weak speculation
- unresolved gaps

Do not merge these categories too early.

## Step 6. Merge facts before findings

The main agent should first stabilize facts such as:

- which route is in scope
- which identifier is attacker-controlled
- where mutation occurs
- which checks are visible
- which checks are absent in visible code

Only after that should it reason about BAC subtype and exploitability.

## Step 7. Normalize evidence

Before judgment, the main agent should make sure each candidate finding has:

- a clear resource or action at risk
- a clear missing or bypassable control
- concrete file references
- a distinct exploit path

If not, downgrade it to:

- open question
- weak item
- or rejected candidate

## Step 8. Send only reviewable findings to the judge

Good input to the judge:

- merged facts
- grouped evidence
- duplicate control already applied
- clearly named candidate findings

Bad input to the judge:

- raw notes from several agents
- repeated issue drafts
- findings with no code references

## Step 9. Produce a strict final answer

The final answer should:

- preserve scope
- preserve uncertainty
- preserve evidence
- preserve impact
- not invent anything new

## 4. Recommended pacing

The main agent should usually pace the work like this:

### Phase 1: understand

- read the task
- bound the scope
- choose the first review lanes

### Phase 2: inspect

- dispatch scope and authz or code-path work
- collect code facts

### Phase 3: evaluate

- generate candidate BAC findings
- normalize evidence
- judge validity

### Phase 4: explain

- report accepted findings
- report rejected or unresolved items when helpful

## 5. Common tactical decisions

## Decision: is this BAC or just authentication?

Ask:

- is the caller merely checked for login
- or is the caller checked against the target resource or privilege boundary

If only login is visible, the main agent should consider BAC risk seriously.

## Decision: should IDOR and BAC be merged?

Often:

- use `broken-access-control` as the broad class
- use `idor` or `horizontal-privilege-escalation` as subtype or rationale

Keep them separate only if the distinction materially helps the reader.

## Decision: is tenant isolation a separate finding?

Keep it separate when:

- the code shows tenant-specific logic
- impact differs materially from ownership-only issues
- remediation differs

Otherwise keep it as a lower-confidence note or unresolved gap.

## Decision: should I ask for more files?

Ask for more material when:

- a hidden policy or decorator layer is likely decisive
- repository helpers are referenced but absent
- tenant semantics determine exploitability
- the current evidence cannot support the user's requested certainty

## 6. Output quality controls

The main agent should reject subagent outputs that are:

- unstructured
- repetitive
- speculative
- missing file references
- overconfident

The main agent should prefer outputs that are:

- role-correct
- compact
- traceable
- uncertainty-aware

## 7. Confidence management

The main agent should say "high severity, medium confidence" when:

- impact is serious
- visible evidence is strong
- but a hidden layer could still change the conclusion

That is often the correct BAC answer.

## 8. Escalation phrases the main agent can use

When evidence is incomplete:

```text
The current artifacts support a likely broken access control issue, but a hidden
authorization layer could still change confidence.
```

When scope is too broad:

```text
The repo is too broad for a credible single-pass BAC review, so I am narrowing
the review to the highest-risk mutation and admin paths first.
```

When two findings overlap:

```text
These two drafts describe the same unauthorized mutation path, so I am merging
them into one BAC finding with a more precise subtype.
```

## 9. Main-agent checklist before final output

Before finishing, the main agent should confirm:

- the scope is explicit
- accepted findings are evidence-backed
- weak items were not promoted by accident
- duplicates were merged correctly
- confidence blockers are disclosed
- remediation matches the missing control

## 10. Compact operating template

The main agent can keep its internal state in this shape:

```text
Main-agent state:

- scope:
- active lanes:
- stable facts:
- candidate findings:
- dropped items:
- unresolved gaps:
- confidence blockers:
- next step:
```

This template is especially useful in longer reviews.
