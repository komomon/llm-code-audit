# Execution Demo

Use this file to study a realistic end-to-end run of the broken access control
agent team.

This is not a framework implementation. It is an execution example showing:

- what the user asks
- how the main agent plans
- what each subagent receives
- what each subagent returns
- how findings are merged and judged
- what the final report looks like

## 1. User request

```text
Please review this order update flow for broken access control. I want to know
whether an authenticated user can modify another user's order.
```

## 2. Example code context

Assume the provided artifacts include:

### routes.py

```python
router.patch("/orders/<order_id>", update_order)
```

### controllers/order.py

```python
def update_order(request, order_id):
    user = request.context.user
    if not user:
        raise Unauthorized()

    payload = request.json
    return order_service.update_order(order_id, payload)
```

### services/order_service.py

```python
def update_order(order_id, payload):
    order = order_repo.get_order(order_id)
    order.status = payload["status"]
    order.note = payload["note"]
    return order_repo.save(order)
```

### repositories/order_repo.py

```python
def get_order(order_id):
    return db.orders.find_one({"id": order_id})
```

## 3. Main-agent intake

The main agent should first summarize the task like this:

```text
Goal:
- determine whether the order update flow has broken access control

Likely vulnerability classes:
- horizontal privilege escalation
- IDOR
- tenant-isolation failure if tenant scoping is relevant

Likely critical files:
- routes.py
- controllers/order.py
- services/order_service.py
- repositories/order_repo.py

Deliverable:
- evidence-backed findings with severity, confidence, and remediation
```

## 4. Main-agent execution plan

The main agent then creates a short plan:

```text
Plan:
1. Use scope-agent to identify the sensitive entrypoints and hotspot files.
2. Use authz-mapper-agent to map visible authentication, ownership, role, and tenant checks.
3. Use code-path-agent to trace order_id from route to mutation sink.
4. Use access-control-hypothesis-agent to generate BAC candidate findings from verified facts only.
5. Use evidence-agent to normalize and deduplicate the materials.
6. Use judge-agent to confirm or reject findings.
7. Use reporter-agent to produce the final report.
```

## 5. Main-agent dispatches

## 5.1 Dispatch to scope-agent

```text
Task:
Identify the highest-risk entrypoints and modules for a broken access control review of order update operations.

Your role:
scope-agent

Relevant context:
- target files: routes.py, controllers/order.py, services/order_service.py, repositories/order_repo.py
- target concern: whether users can modify other users' orders

Required output:
- scope
- hotspots
- architecture_facts
- open_questions
```

### Example scope-agent response

```yaml
agent: scope-agent
scope:
  - route: "PATCH /orders/<order_id>"
hotspots:
  - "controllers/order.py:update_order"
  - "services/order_service.py:update_order"
  - "repositories/order_repo.py:get_order"
architecture_facts:
  - "The route forwards directly to update_order."
  - "The controller checks that a user object exists."
  - "The service mutates order state."
  - "The repository fetches by order_id."
open_questions:
  - "No tenant or ownership helper is visible in the provided files."
```

## 5.2 Dispatch to authz-mapper-agent

```text
Task:
Map all visible authentication, role, ownership, tenant, and approval checks in the order update flow.

Your role:
authz-mapper-agent

Relevant context:
- target route: PATCH /orders/<order_id>
- target files: routes.py, controllers/order.py, services/order_service.py, repositories/order_repo.py

Required output:
- scope
- authorization_facts
- evidence
- open_questions
```

### Example authz-mapper-agent response

```yaml
agent: authz-mapper-agent
scope:
  - "PATCH /orders/<order_id>"
authorization_facts:
  - "The controller enforces authentication by requiring request.context.user."
  - "No role check is visible."
  - "No ownership comparison is visible."
  - "No tenant scoping is visible."
evidence:
  - file: "controllers/order.py"
    function: "update_order"
    lines: "1-7"
    reason: "Only authentication is visible before calling the service."
  - file: "repositories/order_repo.py"
    function: "get_order"
    lines: "1-2"
    reason: "Order fetch uses order_id only."
open_questions:
  - "A hidden decorator or policy layer might exist outside the provided files."
```

## 5.3 Dispatch to code-path-agent

```text
Task:
Trace the request-to-sink path for order updates and identify where sensitive mutation occurs and where authorization should have happened.

Your role:
code-path-agent

Relevant context:
- target route: PATCH /orders/<order_id>
- target files: routes.py, controllers/order.py, services/order_service.py, repositories/order_repo.py

Required output:
- facts
- code_paths
- evidence
- missing_checks
- open_questions
```

### Example code-path-agent response

```yaml
agent: code-path-agent
facts:
  - "order_id enters from the route parameter."
  - "The controller authenticates the user but does not use the user in the service call."
  - "The service fetches the order and mutates it."
code_paths:
  - entry: "routes.py"
    flow:
      - "routes.py -> controllers/order.py:update_order"
      - "controllers/order.py:update_order -> services/order_service.py:update_order"
      - "services/order_service.py:update_order -> repositories/order_repo.py:get_order"
      - "services/order_service.py:update_order -> repositories/order_repo.py:save"
evidence:
  - file: "controllers/order.py"
    function: "update_order"
    lines: "1-7"
    reason: "Authenticated user is checked but not passed into authorization logic."
  - file: "services/order_service.py"
    function: "update_order"
    lines: "1-5"
    reason: "The service updates the order without an owner or tenant check."
missing_checks:
  - "resource ownership validation before mutation"
  - "tenant scoping before repository fetch or save"
open_questions:
  - "The save implementation is not shown."
```

## 5.4 Dispatch to access-control-hypothesis-agent

```text
Task:
Using only the verified facts collected so far, generate candidate broken access control findings for the order update flow.

Your role:
access-control-hypothesis-agent

Relevant context:
- verified facts:
  - the route accepts order_id from the request path
  - authentication exists
  - no ownership or tenant check is visible
  - the service mutates the order after fetching it by id

Required output:
- candidate_findings
- assumptions
- follow_up_checks
```

### Example access-control-hypothesis-agent response

```yaml
agent: access-control-hypothesis-agent
candidate_findings:
  - finding_key: "BAC-order-update-01"
    type: "idor"
    title: "Possible IDOR in order update flow"
    confidence: "medium"
    exploit_conditions:
      - "An authenticated attacker can supply another user's order_id."
      - "No downstream ownership or tenant validation exists."
    attacker_prerequisites:
      - "Authenticated low-privilege user"
    mapped_dimensions:
      - "ownership"
      - "write access"
  - finding_key: "BAC-order-update-02"
    type: "tenant-isolation-failure"
    title: "Possible cross-tenant order update"
    confidence: "low"
    exploit_conditions:
      - "Orders are shared across tenants or tenant scoping is required."
      - "No tenant validation exists outside the provided code."
    attacker_prerequisites:
      - "Authenticated user with knowledge of another tenant's order id"
    mapped_dimensions:
      - "tenant"
      - "write access"
assumptions:
  - "No hidden authorization policy exists in middleware or decorators."
follow_up_checks:
  - "Search for ownership validation in decorators, policies, or repository helpers."
  - "Verify whether orders are tenant-scoped in the data model."
```

## 6. Main-agent merge before evidence normalization

The main agent should summarize the collected material like this:

```text
Merged facts so far:
- authentication is visible in the controller
- order_id is attacker-controlled through the route
- the service fetches and mutates the order by id
- no ownership check is visible
- no tenant check is visible in provided files

Candidate issues so far:
- likely horizontal privilege escalation / IDOR in the order update path
- possible tenant-isolation issue, but current support is weaker

Main unresolved gaps:
- hidden decorators or policy layers
- save implementation
- whether tenant scoping exists elsewhere
```

## 7. Dispatch to evidence-agent

```text
Task:
Normalize the candidate BAC findings for the order update flow, group evidence by finding, and separate strong support from weak speculation.

Your role:
evidence-agent

Relevant context:
- outputs from scope-agent, authz-mapper-agent, code-path-agent, and access-control-hypothesis-agent

Required output:
- merged_facts
- merged_findings
- weak_items_to_drop
- unresolved_conflicts
```

### Example evidence-agent response

```yaml
agent: evidence-agent
merged_facts:
  - "Visible code authenticates the caller but does not show ownership validation."
  - "order_id is taken from the route and used to fetch the order."
  - "The service mutates the order after fetching it by id."
merged_findings:
  - finding_key: "BAC-order-update-01"
    type: "broken-access-control"
    subtype: "horizontal-privilege-escalation"
    title: "Possible unauthorized order update via attacker-controlled order_id"
    supporting_evidence:
      - "controllers/order.py:1-7"
      - "services/order_service.py:1-5"
      - "repositories/order_repo.py:1-2"
    confidence: "medium"
weak_items_to_drop:
  - "Cross-tenant update claim remains weak because tenant semantics are not visible in the provided code."
unresolved_conflicts:
  - "No hidden policy layer was provided."
```

## 8. Dispatch to judge-agent

```text
Task:
Judge whether the candidate findings in the order update flow are confirmed, rejected, or still unproven, then assign severity and confidence.

Your role:
judge-agent

Relevant context:
- merged findings from evidence-agent
- rules from finding-rubric.md

Required output:
- accepted_findings
- rejected_findings
- evidence_gaps
- severity_rationale
```

### Example judge-agent response

```yaml
agent: judge-agent
accepted_findings:
  - finding_id: "BAC-001"
    type: "broken-access-control"
    subtype: "horizontal-privilege-escalation"
    title: "Order update flow lacks visible ownership validation"
    severity: "high"
    confidence: "medium"
    dimensions:
      - "ownership"
      - "write access"
    reason:
      - "The controller checks authentication only."
      - "The service mutates the order after fetching it by attacker-controlled order_id."
      - "No ownership validation is visible in the provided files."
    evidence:
      - "controllers/order.py:1-7"
      - "services/order_service.py:1-5"
      - "repositories/order_repo.py:1-2"
    impact:
      - "An authenticated user may be able to modify another user's order if no hidden policy layer exists."
    remediation:
      - "Require server-side ownership validation before updating the order."
      - "Prefer repository queries scoped by both order_id and actor or tenant context."
rejected_findings:
  - title: "Cross-tenant order update"
    reason: "Tenant semantics were not visible in the provided artifacts."
evidence_gaps:
  - "No decorator or policy implementation was provided."
severity_rationale:
  - "Unauthorized modification of another user's order is a high-severity integrity issue."
```

## 9. Dispatch to reporter-agent

```text
Task:
Write the final report for the broken access control review of the order update flow.

Your role:
reporter-agent

Relevant context:
- accepted findings
- rejected findings
- evidence gaps
- scope summary

Required output:
- final_report
```

### Example reporter-agent response

```md
# Broken Access Control Review: Order Update Flow

## Scope

Reviewed:

- `routes.py`
- `controllers/order.py`
- `services/order_service.py`
- `repositories/order_repo.py`

Focus:

- whether an authenticated user can modify another user's order

## Executive Summary

One high-severity broken access control finding was accepted with medium
confidence. The visible code authenticates the caller but does not show an
ownership check before mutating an order selected by route-controlled `order_id`.

## Findings

### BAC-001: Order update flow lacks visible ownership validation

- Severity: high
- Confidence: medium
- Type: broken-access-control
- Subtype: horizontal-privilege-escalation

Evidence:

- `controllers/order.py:1-7`
- `services/order_service.py:1-5`
- `repositories/order_repo.py:1-2`

Why this matters:

- the endpoint accepts attacker-controlled `order_id`
- the service fetches and mutates the order by that id
- no ownership validation is visible in the provided code

Impact:

- an authenticated user may be able to modify another user's order

Remediation:

- enforce server-side ownership validation before update
- scope order lookup by actor or tenant context
- keep authorization checks in trusted server-side logic, not only in handlers

## Unresolved Questions

- hidden decorators or policy layers were not provided
- tenant semantics were not visible in the reviewed artifacts
```

## 10. What this demo teaches

This example is intentionally simple, but it shows the main-agent pattern:

1. scope before judging
2. map authz boundaries separately from code-path tracing
3. generate hypotheses only from verified facts
4. normalize evidence before judgment
5. let the judge decide what is accepted
6. let the reporter format only accepted findings

## 11. How to adapt this demo

To adapt this flow:

- change the resource type, such as `invoice`, `account`, or `ticket`
- change the operation, such as read, update, delete, approve, or export
- change the subtype focus, such as vertical privilege escalation or tenant isolation
- add missing context files if your real project has middleware, decorators, policies, or ORM helpers
