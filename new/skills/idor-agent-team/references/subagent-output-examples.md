# Subagent Output Examples

Use this file to study what good outputs look like in a fine-grained IDOR
review.

## Input-parameter agent example

```yaml
agent: input-parameter-agent
input_parameters:
  - name: "order_id"
    source: "route"
    attacker_controlled: true
    notes:
      - "Used as the selector for order retrieval."
evidence:
  - file: "routes.py"
    function: "order_detail_route"
    lines: "1-1"
    reason: "The route accepts order_id from the request path."
open_questions:
  - "Is order_id normalized elsewhere before repository access?"
```

## Auth-context agent example

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
  - "The controller checks that request.context.user exists."
  - "Trusted identity is available before the service call."
evidence:
  - file: "controllers/order.py"
    function: "get_order"
    lines: "1-8"
    reason: "The handler reads request.context.user before calling the service."
open_questions:
  - "No separate policy object was shown."
```

## Input/auth relation agent example

```yaml
agent: input-auth-relation-agent
relation_facts:
  - "No visible predicate links order_id to current_user.id."
  - "No tenant-scoped filter is visible in the repository lookup."
evidence:
  - file: "repositories/order_repo.py"
    function: "get_order"
    lines: "1-2"
    reason: "Lookup uses order_id only."
open_questions:
  - "A hidden repository wrapper might add scope, but it was not provided."
```

## Output/auth relation agent example

```yaml
agent: output-auth-relation-agent
relation_facts:
  - "The fetched order is returned to the caller after id-only lookup."
  - "No visible ownership validation appears before serialization."
evidence:
  - file: "services/order_service.py"
    function: "get_order"
    lines: "1-4"
    reason: "The service returns the fetched object directly."
open_questions:
  - "Serializer implementation was not shown."
```
