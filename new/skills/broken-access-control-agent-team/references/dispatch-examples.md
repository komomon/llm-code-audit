# Dispatch Examples

Use this file when the main agent needs concrete examples of how to assign work
to subagents during a broken access control review.

The goal is to make delegation:

- narrow
- evidence-oriented
- easy to merge later

Each dispatch should include:

- one bounded question
- one clear ownership area
- relevant context only
- required output fields
- an explicit evidence rule

## 1. Generic dispatch wrapper

Use this as the default pattern.

```text
Task:
<one bounded BAC review question>

Your role:
<subagent role>

Your ownership:
- <responsibility 1>
- <responsibility 2>

Do not:
- <forbidden action 1>
- <forbidden action 2>

Relevant context:
- target routes: <routes>
- target files: <files>
- prior facts: <facts already established>

Required output:
- <field 1>
- <field 2>
- <field 3>

Evidence rule:
Only include claims tied to provided code or artifacts.
If a key authorization layer is missing from the materials, say so explicitly.
```

## 2. Dispatch to scope-agent

```text
Task:
Identify the highest-risk entrypoints and modules for a broken access control review of order update and delete operations.

Your role:
scope-agent

Your ownership:
- locate routes, handlers, services, repositories, jobs, and hotspots
- identify sensitive read and write surfaces related to orders

Do not:
- confirm a vulnerability
- assign severity

Relevant context:
- target files: routes.py, controllers/order.py, services/order_service.py, repositories/order_repo.py
- target concern: whether users can modify or delete other users' orders

Required output:
- scope
- hotspots
- architecture_facts
- open_questions

Evidence rule:
Only include items supported by the provided files.
If a likely authz layer is missing, note it under open_questions.
```

## 3. Dispatch to authz-mapper-agent

```text
Task:
Map all visible authentication, role, ownership, tenant, and approval checks in the order update flow.

Your role:
authz-mapper-agent

Your ownership:
- identify where authentication is enforced
- identify where ownership, role, tenant, and approval checks appear or are absent

Do not:
- treat missing visible checks as a confirmed bug by itself
- write final findings

Relevant context:
- target route: PATCH /orders/{id}
- target files: middleware/auth.py, controllers/order.py, services/order_service.py, repositories/order_repo.py
- prior facts: the handler reads order_id from the route

Required output:
- scope
- authorization_facts
- evidence
- open_questions

Evidence rule:
Use exact file and function references whenever possible.
If hidden decorators or policies may exist but are not shown, say so explicitly.
```

## 4. Dispatch to code-path-agent

```text
Task:
Trace the request-to-sink path for order updates and identify where sensitive mutation occurs and where authorization should have happened.

Your role:
code-path-agent

Your ownership:
- trace order_id and actor identity through the request path
- identify where the update actually happens and what checks are visible before it

Do not:
- assume unseen middleware or decorators exist
- produce final user-facing conclusions

Relevant context:
- target route: PATCH /orders/{id}
- target files: routes.py, controllers/order.py, services/order_service.py, repositories/order_repo.py
- prior facts: authentication exists, ownership validation is not yet confirmed

Required output:
- facts
- code_paths
- evidence
- missing_checks
- open_questions

Evidence rule:
Only describe flows directly visible in the provided code.
If a key downstream call target is missing, note that gap.
```

## 5. Dispatch to access-control-hypothesis-agent

```text
Task:
Using only the verified facts collected so far, generate candidate broken access control findings for the order update flow.

Your role:
access-control-hypothesis-agent

Your ownership:
- map verified facts to horizontal privilege escalation, IDOR, tenant, vertical, or approval-bypass classes
- state exploit conditions and attacker prerequisites

Do not:
- present a hypothesis as confirmed without evidence
- merge unrelated issue types casually

Relevant context:
- verified facts:
  - PATCH /orders/{id} reaches update_order and then order_service.update_order
  - visible code authenticates the caller
  - no ownership check is visible in the reviewed files
  - repository lookup uses order id

Required output:
- candidate_findings
- assumptions
- follow_up_checks

Evidence rule:
Base all candidate findings on the verified facts above.
If a hypothesis depends on a missing layer, mark that dependence explicitly.
```

## 6. Dispatch to evidence-agent

```text
Task:
Normalize the candidate BAC findings for the order update flow, group evidence by finding, and separate strong support from weak speculation.

Your role:
evidence-agent

Your ownership:
- deduplicate findings
- group evidence by finding
- normalize drafts into the standard structure
- identify weak items to drop

Do not:
- invent new vulnerabilities
- silently discard important evidence

Relevant context:
- scope-agent output
- authz-mapper-agent output
- code-path-agent output
- access-control-hypothesis-agent output

Required output:
- merged_facts
- merged_findings
- weak_items_to_drop
- unresolved_conflicts

Evidence rule:
Every merged finding must retain traceable code references.
If two findings look similar but differ in impact, keep them separate and explain why.
```

## 7. Dispatch to judge-agent

```text
Task:
Judge whether the candidate findings in the order update flow are confirmed, rejected, or still unproven, then assign severity and confidence.

Your role:
judge-agent

Your ownership:
- decide whether each finding meets the evidence threshold
- assign severity and confidence
- explain acceptance, rejection, or downgrade decisions

Do not:
- accept unsupported BAC findings
- invent evidence that other agents did not provide

Relevant context:
- merged findings from evidence-agent
- severity and confidence rules from finding-rubric.md

Required output:
- accepted_findings
- rejected_findings
- evidence_gaps
- severity_rationale

Evidence rule:
Accept only findings that have a clear resource or action at risk, a missing or bypassable authorization control, and traceable code evidence.
```

## 8. Dispatch to reporter-agent

```text
Task:
Write the final report for the broken access control review of the order update flow.

Your role:
reporter-agent

Your ownership:
- convert accepted findings into a clear final report
- preserve scope, evidence, impact, remediation, and unresolved questions

Do not:
- invent new findings
- silently change the judge's decisions

Relevant context:
- accepted findings
- evidence gaps
- scope summary

Required output:
- final_report

Evidence rule:
Use only accepted findings and confirmed facts.
Do not add new vulnerability claims at this stage.
```

## 9. Dispatch pattern for broad repo review

When the repo is large, the main agent should narrow each task.

Bad dispatch:

- "Review the whole repo for access control bugs."

Better dispatch:

- "Review account update and delete routes for ownership checks."
- "Map tenant scoping in invoice list and invoice export flows."
- "Trace whether admin export services are reachable from non-admin handlers."

## 10. Dispatch pattern for unresolved gaps

When key code is missing, dispatch explicitly for gap analysis.

```text
Task:
Identify which missing files or hidden layers would most affect confidence in the current BAC findings.

Your role:
authz-mapper-agent

Your ownership:
- identify unresolved authorization layers
- explain how each missing layer could change the current conclusion

Do not:
- confirm or reject findings directly

Required output:
- open_questions
- confidence_blockers
- suggested_next_files
```

## 11. Main-agent reminder

Before dispatching, the main agent should check:

- is this question narrow enough
- does this agent clearly own it
- is the expected output mergeable
- does the agent have enough context to answer
- is the evidence rule explicit
