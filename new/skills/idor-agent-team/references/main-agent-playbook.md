# Main Agent Playbook

Use this file as the practical operating handbook for the main agent during a
fine-grained IDOR review.

This playbook focuses on what to do in order, not just what rules exist.

## 1. Main-agent mindset

The main agent should act like:

- a scope controller
- a fact stabilizer
- a relation-check owner
- a strict merger

The main agent should not act like:

- a broad guess generator
- a one-shot vulnerability classifier
- a reporter before facts are stable

## 2. The operating loop

Use this loop:

1. restate the route and resource under review
2. stabilize attacker-controlled selectors
3. stabilize trusted identity context
4. trace the path
5. run relation checks
6. generate candidate findings
7. normalize evidence
8. judge validity
9. write the final answer

If the review gets noisy, return to this loop.

## 3. Step-by-step operating sequence

## Step 1. Restate the task

Before dispatching, summarize:

- what route or function is in scope
- whether the operation is read, update, delete, download, or export
- what object type is at risk
- what output the user wants

Good example:

```text
We are reviewing whether an authenticated user can read another user's order by
changing order_id in the URL. The relevant path includes the route, controller,
service, repository, and any serializer used in the response.
```

## Step 2. Stabilize the attacker-controlled side

Dispatch `input-parameter-agent` early.

The goal is to answer:

- what selectors does the attacker control
- where do they enter the path
- where are they forwarded

If this is unclear, the rest of the review will be weak.

## Step 3. Stabilize the trusted side

Dispatch `auth-context-agent` early.

The goal is to answer:

- what identity values are trusted
- where are they first created or read
- are they available for authorization decisions

If this is unclear, relation analysis will be weak.

## Step 4. Trace the path

Use `call-chain-agent` to answer:

- where object selection happens
- where the object is returned, serialized, or mutated
- whether the trusted identity travels along the same path

## Step 5. Run relation checks deliberately

This is the core of strong IDOR review.

Use `input-auth-relation-agent` to ask:

- is the attacker-controlled selector constrained by trusted identity

Use `output-auth-relation-agent` to ask:

- is the returned or mutated object actually verified against trusted identity

Do not skip these lanes just because you already suspect an issue.

## Step 6. Merge facts before findings

Before generating findings, the main agent should stabilize:

- the attacker-controlled selector
- the trusted identity fields
- the fetch or mutation sink
- the presence or absence of visible scoping

Only after this should the team propose IDOR findings.

## Step 7. Generate candidate findings carefully

Use `idor-hypothesis-agent` only after facts and relation results are stable.

Require it to produce:

- candidate finding
- exploit conditions
- attacker prerequisites
- assumptions

Do not let it jump straight to confirmed vulnerability language.

## Step 8. Normalize evidence

Use `evidence-agent` when:

- multiple drafts overlap
- several lanes discovered related facts
- you need one merged finding per exploit path

The evidence agent should simplify the judge's work, not replace it.

## Step 9. Judge strictly

The judge should only receive:

- merged facts
- grouped evidence
- stable candidate findings
- clear unresolved gaps

Do not send raw notes from all lanes directly to the judge.

## Step 10. Report without invention

The final answer should:

- preserve scope
- preserve the exploit path
- preserve evidence
- preserve uncertainty
- avoid inventing new claims

## 4. Tactical decisions

## Decision: compact or full team

Use compact mode when:

- one file or one short path is enough

Use full mode when:

- there are several layers
- object selection and auth context are separated
- relation checks are easy to miss

## Decision: is this really IDOR

The main agent should ask:

- is the object selected by attacker-controlled input
- does trusted identity exist
- is that identity used to scope the selected object
- is the fetched object returned or mutated without visible owner scoping

If yes, this is a strong IDOR review path.

## Decision: is the issue read-only or write-impacting

Keep these separate when impact differs:

- read disclosure
- update or delete mutation
- export or download disclosure

## Decision: ask for serializer or repository code

Ask for more material when:

- the response path matters but serializer code is missing
- repository helpers are referenced but hidden
- ownership logic may live below the visible service layer

## 5. Output quality controls

Reject subagent outputs that are:

- vague
- repetitive
- missing file references
- overconfident
- mixing facts with final conclusions

Prefer outputs that are:

- structured
- lane-correct
- relation-aware
- uncertainty-aware

## 6. Confidence management

A common good IDOR answer is:

- severity: high
- confidence: medium

This is appropriate when:

- impact is strong if true
- object scoping is not visible
- but hidden repository or policy layers could still exist

## 7. Useful phrases for the main agent

When relation analysis is incomplete:

```text
The current artifacts show attacker-controlled object selection and visible
trusted identity, but they do not yet show whether those two are joined by an
owner or tenant-scoping control.
```

When scope is too broad:

```text
I am narrowing the IDOR review to the highest-risk object retrieval and
mutation paths first so the findings remain evidence-backed.
```

When confidence is limited:

```text
The visible code supports a likely IDOR path, but confidence remains medium
because serializer or repository wrapper logic was not provided.
```

## 8. Final pre-report checklist

Before finishing, the main agent should confirm:

- attacker-controlled selectors are explicit
- trusted identity fields are explicit
- relation checks were performed
- accepted findings are evidence-backed
- unresolved gaps are disclosed
- remediation matches the missing object-level control

## 9. Compact operating state

The main agent can track progress like this:

```text
Main-agent IDOR state:

- route and resource:
- attacker-controlled selectors:
- trusted identity fields:
- stable path facts:
- stable relation facts:
- candidate findings:
- evidence gaps:
- next step:
```
