# Finding Rubric

Use this file when judging broken access control findings.

## Severity guidance

Use severity for impact, not certainty.

### Critical

Use when the flaw enables:

- broad tenant breakout
- widespread unauthorized admin actions
- mass disclosure or mass modification of sensitive resources
- unauthenticated or near-unauthenticated access to high-impact functions

### High

Use when the flaw enables:

- unauthorized modification of another user's resources
- access to another tenant's sensitive data
- approval or privileged workflow actions without proper authority
- repeated exploitation across many resources

### Medium

Use when the flaw enables:

- unauthorized read or write with meaningful but narrower impact
- constrained privilege escalation
- partial exposure or mutation limited by context

### Low

Use when the issue is:

- defense-in-depth
- low-impact due to strong practical constraints
- difficult to exploit and limited in consequence

## Confidence guidance

Use confidence for certainty based on evidence.

### High confidence

- the vulnerable path is directly visible in provided code
- there is no credible evidence of a downstream authorization layer
- the code evidence is sufficient to explain exploitability

### Medium confidence

- strong indicators exist
- one important assumption remains unresolved
- hidden decorators, middleware, or repository logic may still affect the result

### Low confidence

- the hypothesis depends on multiple assumptions
- only partial code or artifacts were available
- exploitability is plausible but weakly supported

## Rejection rules

Reject a candidate finding when:

- the visible code shows a valid authorization check
- the claimed issue depends on unsupported assumptions
- the evidence does not show a reachable sensitive operation
- a stronger explanation better matches the code

## Required elements for an accepted finding

Each accepted finding should have:

- a clear resource or action at risk
- a clear missing or bypassable authorization control
- traceable code evidence
- an explained attacker outcome
- a reasonable remediation direction

## Finding taxonomy

Prefer explicit subtypes such as:

- `horizontal-privilege-escalation`
- `vertical-privilege-escalation`
- `idor`
- `tenant-isolation-failure`
- `approval-authority-bypass`

If multiple subtypes apply, choose the most precise one and mention the others
in `dimensions` or rationale.
