# Execution Demo

Use this file to study a realistic end-to-end run of the IDOR agent team.

## 1. User request

```text
Please review the order detail endpoint and tell me whether an authenticated
user can read another user's order by changing the order_id in the URL.
```

## 2. Example code context

### routes.py

```python
router.get("/orders/<order_id>", get_order)
```

### controllers/order.py

```python
def get_order(request, order_id):
    user = request.context.user
    if not user:
        raise Unauthorized()
    return order_service.get_order(order_id)
```

### services/order_service.py

```python
def get_order(order_id):
    order = order_repo.get_order(order_id)
    return order_serializer.to_json(order)
```

### repositories/order_repo.py

```python
def get_order(order_id):
    return db.orders.find_one({"id": order_id})
```

## 3. Main-agent plan

```text
Plan:
1. Identify attacker-controlled selectors.
2. Identify trusted auth context.
3. Trace the request-to-fetch-to-response path.
4. Check whether input selectors are constrained by trusted identity.
5. Check whether returned objects are scoped to trusted identity.
6. Generate candidate IDOR findings.
7. Normalize evidence and judge the result.
```

## 4. Example conclusion flow

Stable facts:

- `order_id` is attacker-controlled through the route
- `request.context.user` provides trusted identity
- repository lookup uses `order_id` only
- the fetched object is returned to the caller
- no visible owner or tenant scoping is present in the provided code

Accepted finding shape:

```yaml
finding_id: "IDOR-001"
type: "idor"
title: "Order detail flow lacks visible object-level authorization"
severity: "high"
confidence: "medium"
reason:
  - "order_id is attacker-controlled"
  - "trusted identity is available but not visibly used to scope object retrieval"
  - "the fetched order is returned after id-only lookup"
impact:
  - "an authenticated user may be able to read another user's order"
```

## 5. What this demo teaches

This example shows the value of the fine-grained split:

- one lane confirms attacker-controlled input
- one lane confirms trusted identity
- one lane traces the fetch and return path
- two separate relation lanes test the core authorization question

That is often stronger than asking one broad agent to reason about everything at once.
