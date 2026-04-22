# IDOR Review: Order Detail and Update Flows

## Scope

Reviewed:

- `sample_artifacts/routes.py`
- `sample_artifacts/controllers/order.py`
- `sample_artifacts/services/order_service.py`
- `sample_artifacts/repositories/order_repo.py`
- `sample_artifacts/serializers/order_serializer.py`

## Executive Summary

The visible code accepts attacker-controlled `order_id`, has trusted user
context available, but does not show visible owner or tenant scoping during
object retrieval. The fetched order is returned and updated after id-only lookup.

## Findings

### IDOR-001: Order detail flow lacks visible object-level authorization

- Severity: high
- Confidence: medium

Evidence:

- `routes.py`
- `controllers/order.py`
- `services/order_service.py`
- `repositories/order_repo.py`

### IDOR-002: Order update flow lacks visible object-level authorization

- Severity: high
- Confidence: medium

Evidence:

- `controllers/order.py`
- `services/order_service.py`
- `repositories/order_repo.py`

## Unresolved Questions

- hidden repository wrappers or policy layers were not reviewed
- tenant semantics are not visible in the sample artifacts
