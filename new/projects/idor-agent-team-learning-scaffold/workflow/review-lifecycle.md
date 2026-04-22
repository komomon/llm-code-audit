# Review Lifecycle

Use this workflow for a fine-grained IDOR review.

1. Intake the user request.
2. Narrow the review to one route or one object path.
3. Run `scope-agent`, `input-parameter-agent`, `auth-context-agent`, and `call-chain-agent`.
4. Stabilize facts.
5. Run `input-auth-relation-agent` and `output-auth-relation-agent`.
6. Run `idor-hypothesis-agent`.
7. Run `evidence-agent`.
8. Run `judge-agent`.
9. Run `reporter-agent`.

Keep attacker-controlled selectors separate from trusted identity context until relation checks are complete.
