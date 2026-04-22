# Broken Access Control Review: Order Update and Delete Flows

## Scope

Reviewed:

- `sample_artifacts/routes.py`
- `sample_artifacts/controllers/order.py`
- `sample_artifacts/services/order_service.py`
- `sample_artifacts/repositories/order_repo.py`

## Executive Summary

The visible code authenticates the caller but does not show ownership or tenant
validation before updating or deleting orders selected by attacker-controlled
`order_id`.

## Findings

### BAC-001: Order update flow lacks visible ownership validation

- Severity: high
- Confidence: medium

Evidence:

- `controllers/order.py`
- `services/order_service.py`
- `repositories/order_repo.py`

### BAC-002: Order delete flow lacks visible ownership validation

- Severity: high
- Confidence: medium

Evidence:

- `controllers/order.py`
- `services/order_service.py`
- `repositories/order_repo.py`

## Unresolved Questions

- hidden decorators or policy layers were not reviewed
- tenant semantics are not visible in the sample artifacts
