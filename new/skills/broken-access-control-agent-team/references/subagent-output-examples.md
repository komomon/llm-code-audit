# Subagent Output Examples

Use this file to study what good subagent outputs look like in a broken access
control review.

These are not the only valid outputs, but they show the level of structure,
evidence quality, and role discipline that the main agent should expect.

## 1. Scope-agent example

Scenario:

- target concern: can users update or delete other users' orders
- target artifacts: `routes.py`, `controllers/order.py`, `services/order_service.py`, `repositories/order_repo.py`

Example output:

```yaml
agent: scope-agent
scope:
  - route: "PATCH /orders/<order_id>"
  - route: "DELETE /orders/<order_id>"
hotspots:
  - "controllers/order.py:update_order"
  - "controllers/order.py:delete_order"
  - "services/order_service.py:update_order"
  - "services/order_service.py:delete_order"
  - "repositories/order_repo.py:get_order"
architecture_facts:
  - "Order mutations are initiated from route-controlled order_id values."
  - "Controller and service layers both participate in the update and delete flows."
  - "Repository access is likely security-relevant because objects are fetched by id."
open_questions:
  - "Is there an authorization decorator in routing not shown in the provided files?"
  - "Does the repository expose scoped lookup helpers not yet reviewed?"
```

What makes this good:

- names the exact high-risk surfaces
- stays at scope and hotspot level
- does not claim a vulnerability is confirmed

## 2. Authz-mapper-agent example

Scenario:

- target concern: whether order update has authentication but not authorization

Example output:

```yaml
agent: authz-mapper-agent
scope:
  - "PATCH /orders/<order_id>"
authorization_facts:
  - "Authentication is enforced by checking request.context.user in the controller."
  - "No explicit role check is visible in the provided code path."
  - "No ownership validation is visible before the order mutation."
  - "No tenant constraint is visible in the repository lookup."
evidence:
  - file: "controllers/order.py"
    function: "update_order"
    lines: "1-7"
    reason: "The controller checks only that a user object exists."
  - file: "services/order_service.py"
    function: "update_order"
    lines: "1-5"
    reason: "The service mutates the fetched order without using actor identity."
  - file: "repositories/order_repo.py"
    function: "get_order"
    lines: "1-2"
    reason: "The repository query uses order_id only."
open_questions:
  - "Could an unseen policy layer apply ownership checks before the controller?"
  - "Is tenant context enforced at the database abstraction layer?"
```

What makes this good:

- distinguishes authentication from authorization
- separates role, ownership, and tenant dimensions
- keeps uncertainty explicit

## 3. Code-path-agent example

Scenario:

- target concern: trace the exact mutation path for order updates

Example output:

```yaml
agent: code-path-agent
facts:
  - "order_id enters the system from the route path."
  - "The controller authenticates the caller but does not pass actor identity into the service authorization logic."
  - "The service fetches an order and mutates its fields."
code_paths:
  - entry: "routes.py:order_update_route"
    flow:
      - "routes.py:order_update_route"
      - "controllers/order.py:update_order"
      - "services/order_service.py:update_order"
      - "repositories/order_repo.py:get_order"
      - "repositories/order_repo.py:save"
evidence:
  - file: "controllers/order.py"
    function: "update_order"
    lines: "1-7"
    reason: "The authenticated actor is checked only for existence."
  - file: "services/order_service.py"
    function: "update_order"
    lines: "1-5"
    reason: "The update occurs after object retrieval with no visible authz gate."
missing_checks:
  - "resource ownership validation before mutation"
  - "tenant scoping during object retrieval"
open_questions:
  - "Does save() perform hidden authorization checks?"
```

What makes this good:

- traces the path step by step
- points to the mutation sink
- calls out missing checks without over-claiming

## 4. Access-control-hypothesis-agent example

Scenario:

- target concern: turn verified facts into candidate BAC findings

Example output:

```yaml
agent: access-control-hypothesis-agent
candidate_findings:
  - finding_key: "BAC-order-update-01"
    type: "broken-access-control"
    subtype: "horizontal-privilege-escalation"
    title: "Possible unauthorized order update via attacker-controlled order_id"
    confidence: "medium"
    exploit_conditions:
      - "An authenticated attacker can supply another user's order_id."
      - "No downstream ownership validation exists."
    attacker_prerequisites:
      - "Authenticated low-privilege user"
    mapped_dimensions:
      - "ownership"
      - "write access"
  - finding_key: "BAC-order-update-02"
    type: "idor"
    subtype: "object-level-authorization"
    title: "Possible IDOR in order mutation path"
    confidence: "medium"
    exploit_conditions:
      - "The system trusts direct object lookup by route-provided id."
      - "No object-owner validation exists before mutation."
    attacker_prerequisites:
      - "Ability to guess or obtain another order id"
    mapped_dimensions:
      - "ownership"
      - "identifier control"
assumptions:
  - "No hidden decorator or policy layer enforces ownership."
follow_up_checks:
  - "Search for owner_id or tenant_id comparisons in service decorators or repository helpers."
```

What makes this good:

- stays in hypothesis mode
- maps the same code facts to explicit BAC subtypes
- records assumptions and follow-up checks

## 5. Evidence-agent example

Scenario:

- target concern: deduplicate overlapping BAC and IDOR drafts

Example output:

```yaml
agent: evidence-agent
merged_facts:
  - "Visible code authenticates the caller."
  - "order_id is taken from the route and used in object retrieval."
  - "The service mutates the order after retrieval."
  - "No visible ownership validation appears before mutation."
merged_findings:
  - finding_key: "BAC-order-update-01"
    type: "broken-access-control"
    subtype: "horizontal-privilege-escalation"
    title: "Possible unauthorized order update"
    supporting_evidence:
      - "controllers/order.py:1-7"
      - "services/order_service.py:1-5"
      - "repositories/order_repo.py:1-2"
    confidence: "medium"
    related_drafts:
      - "BAC-order-update-02"
weak_items_to_drop:
  - "Cross-tenant update theory lacks visible tenant semantics in the provided code."
unresolved_conflicts:
  - "Decorator or middleware implementations were not provided."
```

What makes this good:

- groups overlapping drafts instead of duplicating them
- preserves evidence references
- clearly separates weak items from supported ones

## 6. Judge-agent example

Scenario:

- target concern: decide whether the BAC finding is accepted

Example output:

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
      - "The controller verifies authentication only."
      - "The service mutates the order selected by route-provided order_id."
      - "No ownership check is visible in the reviewed artifacts."
    evidence:
      - "controllers/order.py:1-7"
      - "services/order_service.py:1-5"
      - "repositories/order_repo.py:1-2"
    impact:
      - "Authenticated users may be able to modify orders they do not own."
    remediation:
      - "Require ownership validation before mutation."
      - "Scope object retrieval by actor or tenant context."
rejected_findings:
  - title: "Cross-tenant order update"
    reason: "Tenant semantics were not visible in the provided code."
evidence_gaps:
  - "Policy or decorator implementations were not reviewed."
severity_rationale:
  - "Unauthorized write access to another user's resource is a high-severity integrity flaw."
```

What makes this good:

- accepts only one supported finding
- downgrades certainty because a hidden layer could still exist
- explains both acceptance and rejection

## 7. Reporter-agent example

Scenario:

- target concern: convert accepted BAC findings into the final report

Example output:

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

One broken access control finding was accepted. The visible code authenticates
the caller but does not show an ownership check before mutating an order
selected by route-controlled `order_id`.

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

Impact:

- an authenticated user may be able to modify another user's order

Remediation:

- enforce server-side ownership validation before mutation
- scope order retrieval by actor or tenant context

## Unresolved Questions

- policy or decorator implementations were not reviewed
```

What makes this good:

- formats accepted findings cleanly
- does not add new vulnerability claims
- preserves traceability and uncertainty

## 8. Weak output example to avoid

Example of a weak subagent output:

```text
This definitely looks vulnerable. The auth is probably broken because I do not
see enough checks, and there may also be tenant issues, privilege escalation,
and maybe admin bypass.
```

Why this is bad:

- no file references
- no separation between facts and conclusions
- no role discipline
- no traceable evidence
- too vague to merge or judge

## 9. Main-agent quality checks

The main agent should prefer subagent outputs that are:

- role-correct
- structured
- traceable
- compact
- uncertainty-aware

The main agent should push back on outputs that are:

- speculative
- repetitive
- unstructured
- missing evidence
- pretending certainty without support
