# Review Lifecycle

Use this workflow for a normal broken access control review.

1. Intake the user request.
2. Narrow the review to one or a few high-risk flows.
3. Run `scope-agent`, `authz-mapper-agent`, and `code-path-agent`.
4. Merge stable facts.
5. Run `access-control-hypothesis-agent`.
6. Run `evidence-agent`.
7. Run `judge-agent`.
8. Run `reporter-agent`.
9. Deliver the final report with evidence and unresolved gaps.

Keep the review narrow enough that each accepted finding is traceable.
