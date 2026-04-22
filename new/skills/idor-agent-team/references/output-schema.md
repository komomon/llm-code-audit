# Output Schema

Use this file to keep IDOR review outputs stable.

## Input-parameter agent schema

```yaml
agent: input-parameter-agent
input_parameters:
  - name: "order_id"
    source: "route"
    attacker_controlled: true
    notes:
      - "Used to select the target order."
evidence:
  - file: "routes.py"
    function: "order_detail_route"
    lines: "1-1"
    reason: "order_id is accepted from the request path."
open_questions:
  - "Is order_id normalized or validated elsewhere?"
```

## Auth-context agent schema

```yaml
agent: auth-context-agent
trusted_identity:
  - name: "current_user.id"
    source: "request.context.user"
    trusted: true
  - name: "current_user.tenant_id"
    source: "request.context.user"
    trusted: true
auth_facts:
  - "Authentication is visible in the controller."
  - "Trusted user identity exists, but usage in object scoping is not yet confirmed."
evidence:
  - file: "controllers/order.py"
    function: "get_order"
    lines: "1-8"
    reason: "request.context.user is read before service invocation."
open_questions:
  - "Does middleware derive tenant context elsewhere?"
```

## Relation agent schema

```yaml
agent: input-auth-relation-agent
relation_facts:
  - "No visible comparison links route-controlled order_id to current_user.id."
  - "No tenant-scoped predicate is visible in the repository query."
evidence:
  - file: "repositories/order_repo.py"
    function: "get_order"
    lines: "1-2"
    reason: "Lookup uses order_id only."
open_questions:
  - "Could an unseen repository wrapper add owner or tenant filters?"
```

## Judge schema

```yaml
agent: judge-agent
accepted_findings:
  - finding_id: "IDOR-001"
    type: "idor"
    subtype: "object-level-authorization"
    title: "Order detail path lacks visible owner scoping"
    severity: "high"
    confidence: "medium"
    reason:
      - "order_id is attacker-controlled."
      - "Trusted identity exists but is not visibly joined to object selection."
      - "The fetched object is returned without visible ownership validation."
    evidence:
      - "routes.py:1-1"
      - "controllers/order.py:1-8"
      - "repositories/order_repo.py:1-2"
    impact:
      - "An authenticated user may be able to read another user's order."
    remediation:
      - "Scope object lookup by actor or tenant context."
rejected_findings:
  - title: "Cross-tenant order disclosure"
    reason: "Tenant semantics were not visible in the provided code."
evidence_gaps:
  - "Serializer implementation was not provided."
```
