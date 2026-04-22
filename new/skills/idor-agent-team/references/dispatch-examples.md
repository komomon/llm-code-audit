# Dispatch Examples

Use this file when the main agent needs concrete dispatch patterns for a
fine-grained IDOR review.

## 1. Dispatch to input-parameter-agent

```text
Task:
Identify all attacker-controlled resource selectors in the order detail flow.

Your role:
input-parameter-agent

Relevant context:
- target route: GET /orders/<order_id>
- target files: routes.py, controllers/order.py

Required output:
- input_parameters
- evidence
- open_questions
```

## 2. Dispatch to auth-context-agent

```text
Task:
Identify all trusted identity values available in the order detail flow and where they are first read.

Your role:
auth-context-agent

Relevant context:
- target files: middleware/auth.py, controllers/order.py

Required output:
- trusted_identity
- auth_facts
- evidence
- open_questions
```

## 3. Dispatch to input-auth-relation-agent

```text
Task:
Determine whether the route-controlled order_id is ever constrained by current_user or tenant context before object retrieval.

Your role:
input-auth-relation-agent

Relevant context:
- target files: controllers/order.py, services/order_service.py, repositories/order_repo.py
- verified facts:
  - order_id is attacker-controlled
  - current_user.id is trusted

Required output:
- relation_facts
- evidence
- open_questions
```

## 4. Dispatch to output-auth-relation-agent

```text
Task:
Determine whether the object returned by the order detail flow is visibly scoped to the authenticated caller.

Your role:
output-auth-relation-agent

Relevant context:
- target files: services/order_service.py, repositories/order_repo.py, serializers/order_serializer.py

Required output:
- relation_facts
- evidence
- open_questions
```
