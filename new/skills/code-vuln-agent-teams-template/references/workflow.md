# Workflow

Use this as the default execution workflow for a code-vulnerability agent team.

## 1. Intake

The main agent should identify:

- user goal
- codebase or files in scope
- expected deliverable
- vulnerability focus, if any
- depth versus breadth preference

## 2. Planning

The main agent should produce a short execution plan:

- what to inspect
- which agents to delegate to
- what can run in parallel
- what evidence standard will be used

## 3. Specialist review

Specialist agents should review only their assigned lanes and return structured
intermediate outputs.

## 4. Evidence normalization

The evidence agent should:

- group matching evidence
- remove duplicates
- separate strong from weak support
- prepare merged finding drafts

## 5. Judgment

The judge agent should:

- confirm or reject candidate findings
- assign severity and confidence
- identify unresolved evidence gaps

## 6. Reporting

The reporter agent should:

- turn accepted findings into the final report
- preserve traceability
- keep unresolved items explicit

## 7. Escalation rules

The main agent should pause and realign if:

- evidence conflicts significantly
- scope is too broad to audit credibly
- the user request implies a high-risk assumption that cannot be verified
- important artifacts are missing
