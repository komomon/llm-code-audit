# Main Agent Decision Rules

Use this file to define how the main agent should make control-plane decisions
during a broken access control review.

This file is about orchestration quality, not vulnerability content.

It should help the main agent decide:

- when to delegate
- when to parallelize
- when to ask for more context
- when to lower confidence
- when to reject a finding
- when to stop expanding scope

## 1. Core role of the main agent

The main agent is responsible for:

- shaping the review
- choosing the right subagents
- maintaining evidence discipline
- preserving mergeability
- deciding when the team knows enough to report

The main agent should behave like a careful reviewer, not a hype amplifier.

## 2. Default decision sequence

For each review request, the main agent should move through this sequence:

1. classify the request
2. define a bounded scope
3. choose the minimum useful agent set
4. decide what can run in parallel
5. collect and compare outputs
6. identify gaps and conflicts
7. decide whether more context is necessary
8. send only confirmed or clearly qualified findings to judgment
9. produce the final answer

## 3. When to delegate

Delegate when:

- the question can be cleanly separated by ownership
- multiple independent review lanes will materially improve the result
- the main agent would otherwise mix facts, hypotheses, and judgment too early
- a specialist view makes later judgment easier

Do not delegate when:

- the task is tiny and the overhead would exceed the value
- the question is too vague to assign cleanly
- the main agent is missing the minimum context needed to form a useful task
- the subagent would just repeat work already done

## 4. Minimum useful agent set

Use the smallest team that still preserves review quality.

Recommended minimums:

- narrow path review:
  - `scope-agent`
  - `code-path-agent`
  - `judge-agent`

- normal BAC review:
  - `scope-agent`
  - `authz-mapper-agent`
  - `code-path-agent`
  - `access-control-hypothesis-agent`
  - `evidence-agent`
  - `judge-agent`

- high-ambiguity or high-risk review:
  - use the full default team including `reporter-agent`

Do not spawn extra review lanes just because they sound thorough.

## 5. When to parallelize

Parallelize only when outputs have distinct ownership and can be merged later
without ambiguity.

Good parallel lanes:

- `scope-agent` plus `authz-mapper-agent`
- `scope-agent` plus `code-path-agent`
- `authz-mapper-agent` plus `code-path-agent`

Usually do not parallelize:

- `evidence-agent` before specialist outputs exist
- `judge-agent` before evidence has been normalized
- `reporter-agent` before accepted findings exist

## 6. When to narrow scope

The main agent should narrow scope when:

- the repo is too large for credible review
- the user question names one specific flow
- multiple unrelated flows are mixed together
- there is not enough evidence to support broad conclusions

Good narrowing patterns:

- by route
- by resource type
- by operation type such as read, update, delete, approve, export
- by trust boundary such as public endpoint, admin endpoint, batch job

Bad narrowing pattern:

- "review the whole repo for BAC"

## 7. When to request more context

The main agent should explicitly note missing context when:

- a hidden decorator, middleware, or policy layer could change the result
- repository methods are referenced but not shown
- tenant semantics are central but the model layer is missing
- approval logic may exist in workflow code not provided
- routes are shown but target handlers are missing

Missing context should usually lower confidence, not automatically block all
review.

Only stop and ask for more context when the missing layer is likely to change
the answer materially.

## 8. Confidence-control rules

The main agent should lower confidence when:

- key authz layers are not visible
- the code path is only partially observed
- the exploit depends on hidden assumptions
- the finding rests on framework behavior that has not been verified

The main agent should not lower severity just because confidence is medium.

Keep these separate:

- severity = impact if true
- confidence = certainty based on evidence

## 9. Evidence sufficiency rules

Before sending a finding to the judge, the main agent should ask:

- what exact resource or action is at risk
- what exact authorization control is missing or bypassable
- where in the code that support appears
- whether a hidden layer could plausibly negate the claim
- whether the issue is distinct from other findings or just a duplicate

If those answers are weak, the item should remain:

- a candidate finding
- a low-confidence note
- or a rejected item

## 10. Duplicate-control rules

The main agent should merge findings when:

- they describe the same sink and same exploit path
- the distinction is naming only
- one is a broader phrasing of the other

The main agent should keep findings separate when:

- one is ownership-based and one is tenant-based
- one is read-only and one is write-impacting
- one is horizontal and one is vertical privilege escalation
- the remediation or impact differs materially

## 11. Escalation rules

The main agent should pause and realign when:

- two subagents disagree on a core fact
- the available artifacts are too incomplete to support the requested claim
- the review has expanded beyond the initial scope
- a likely hidden authorization layer is the main uncertainty driver
- a finding would be high impact but currently relies on assumptions

In these cases, the main agent should:

1. summarize what is known
2. state what is missing
3. explain how the missing context affects confidence
4. continue with qualified conclusions or request more material if necessary

## 12. Rejection rules

The main agent should reject a candidate finding before judgment when:

- it has no traceable evidence
- it is based mostly on guesswork
- it duplicates a stronger finding without adding meaning
- the visible code directly contradicts it
- it depends on tenant or ownership semantics not present anywhere in the artifacts

Rejecting weak findings is part of good orchestration.

## 13. Final-answer rules

Before finalizing, the main agent should ensure:

- all accepted findings have evidence
- all major evidence gaps are disclosed
- findings are sorted by practical impact
- remediation is tied to the actual missing control
- the report does not invent anything new

The final answer should be:

- clear
- evidence-backed
- explicit about uncertainty
- strict about scope

## 14. Review-quality checklist for the main agent

Before finishing, the main agent should check:

- did I keep facts separate from conclusions
- did each subagent stay inside its role
- did I merge duplicates correctly
- did I preserve unresolved questions
- did I avoid overstating certainty
- did I avoid understating impact
- did I keep the report scoped to reviewed artifacts

## 15. Simple decision template

The main agent can summarize its own decisions in this shape:

```text
Main-agent review state:

- current scope:
- active subagents:
- known facts:
- candidate findings:
- unresolved gaps:
- confidence blockers:
- next action:
```

This makes the orchestration easier to inspect and easier to improve later.
