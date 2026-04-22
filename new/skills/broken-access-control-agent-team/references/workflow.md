# Workflow

Use this as the default workflow for a broken access control code audit.

## 1. Intake

The main agent should identify:

- user goal
- target codebase or files
- likely authorization surfaces
- expected output format
- whether the review is broad or path-specific

## 2. Scope and boundary mapping

The scope and authz mapper agents should identify:

- routes, handlers, controllers, services, jobs, repositories
- login checks
- role checks
- ownership checks
- tenant checks
- approval gates

## 3. Code-path tracing

The code-path agent should trace:

- request parameters such as `id`, `user_id`, `account_id`, `tenant_id`
- control flow from entrypoint to sensitive read or write
- where mutations or privileged reads actually happen
- where authorization should have happened but did not

## 4. Hypothesis generation

The access-control-hypothesis agent should test for:

- horizontal privilege escalation
- vertical privilege escalation
- IDOR
- tenant breakout
- missing server-side authorization
- approval bypass due to weak authority checks

## 5. Evidence normalization

The evidence agent should:

- group evidence by candidate issue
- deduplicate overlapping findings
- separate strong support from weak speculation
- preserve unresolved questions explicitly

## 6. Judgment

The judge agent should:

- confirm or reject findings
- assign severity and confidence
- explain why each accepted finding meets the evidence threshold
- explain why rejected items failed

## 7. Reporting

The reporter agent should produce:

- scope
- executive summary
- findings
- supporting code references
- exploit impact
- remediation guidance
- unresolved questions

## Escalation rules

The main agent should pause and realign if:

- key repository or service files are missing
- authorization may exist in a hidden layer not provided
- the requested scope is too broad to review credibly
- multiple code paths contradict one another in important ways
