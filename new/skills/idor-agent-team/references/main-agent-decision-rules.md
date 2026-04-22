# Main Agent Decision Rules

Use this file to define how the main agent should make orchestration decisions
during a fine-grained IDOR review.

This file focuses on:

- when to activate the full fine-grained team
- when to compress lanes
- when to parallelize
- when to request more context
- when to lower confidence
- when to reject weak IDOR findings

## 1. Core role of the main agent

The main agent owns:

- scope control
- lane selection
- evidence discipline
- merge discipline
- confidence control
- final conclusion quality

The main agent should behave like a strict reviewer, not a speculative narrator.

## 2. Default decision sequence

For each IDOR review, the main agent should move through this sequence:

1. classify the request
2. identify the resource and operation
3. identify likely attacker-controlled selectors
4. identify likely trusted identity context
5. choose compact or full team
6. stabilize facts
7. run relation checks
8. send only qualified candidate findings to judgment
9. produce the final answer

## 3. When to activate the full fine-grained team

Use the full team when:

- the path spans multiple files or layers
- the repo is large enough that context should be split carefully
- object selection and auth context travel through different code paths
- the fetch path and response or mutation path are different
- hidden layers might exist and relation checks need explicit treatment

Use compact mode when:

- the path is very short
- the object fetch and return happen in one small function
- there is little ambiguity about where auth context and resource selection meet

## 4. When to parallelize

Good parallel lanes:

- `scope-agent`
- `input-parameter-agent`
- `auth-context-agent`
- `call-chain-agent`

Run relation agents after those facts are stable:

- `input-auth-relation-agent`
- `output-auth-relation-agent`

Run downstream only after relation work:

- `idor-hypothesis-agent`
- `evidence-agent`
- `judge-agent`
- `reporter-agent`

## 5. When to narrow scope

The main agent should narrow scope when:

- the user says "review the repo for IDOR"
- the codebase has many unrelated resource flows
- not all paths can be reviewed credibly in one pass
- one route or operation is clearly higher risk

Good narrowing shapes:

- one route
- one object type
- one operation such as read, update, delete, download, or export
- one serializer or repository path

## 6. Fact-stabilization rules

Before allowing any candidate IDOR finding, the main agent should stabilize:

- which parameters are attacker-controlled
- which identity fields are trusted
- where object selection happens
- where object return or mutation happens
- whether any visible owner or tenant scoping exists

If these are not yet stable, the main agent should not jump to conclusions.

## 7. Relation-check rules

The main agent should treat these as required questions:

- is object selection constrained by trusted identity
- is the final object returned or mutated verified against trusted identity

If either question cannot be answered from visible artifacts, confidence should
usually decrease.

## 8. When to request more context

The main agent should note missing context when:

- decorators or policy layers are referenced but not shown
- repository wrappers may add hidden owner or tenant scoping
- serializers or response builders are missing
- tenant semantics are implied but not visible
- batch helpers or service wrappers are absent

Ask for more files only when the missing layer is likely to materially change
the answer.

Otherwise continue with explicit uncertainty.

## 9. Confidence-control rules

Lower confidence when:

- object selection is visible but response or mutation boundaries are not
- trusted identity is visible but not clearly joined to the access path
- hidden repository or policy layers may exist
- tenant semantics are unclear
- exploitability depends on assumptions not proven by visible code

Do not lower severity just because confidence is medium.

Keep these separate:

- severity = impact if true
- confidence = certainty based on evidence

## 10. Rejection rules

Reject or demote a candidate finding when:

- object selection is actually scoped by owner or tenant in visible code
- the claim depends mainly on speculation
- the claim duplicates a stronger candidate finding
- the returned or mutated object is clearly verified against trusted identity
- the path does not actually reach a sensitive read or write

## 11. Duplicate-control rules

Merge findings when:

- they describe the same object selection flaw
- they use different wording for the same exploit path
- one is merely a broader restatement of the other

Keep findings separate when:

- one is read disclosure and one is write mutation
- one is ownership-only and one is tenant-scoped
- the object fetch path and object return or mutation path differ materially

## 12. Final-answer rules

Before finalizing, the main agent should ensure:

- accepted findings have traceable evidence
- relation checks were actually performed
- unresolved gaps are disclosed
- exploit path is clear
- remediation addresses the missing object-level control

## 13. Compact decision template

The main agent can track decisions in this shape:

```text
Main-agent IDOR state:

- scope:
- active lanes:
- attacker-controlled selectors:
- trusted identity fields:
- stable relation facts:
- candidate findings:
- unresolved gaps:
- confidence blockers:
- next step:
```
