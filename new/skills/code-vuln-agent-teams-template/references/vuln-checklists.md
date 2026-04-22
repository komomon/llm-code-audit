# Vulnerability Checklists

Use this file to adapt the generic workflow to specific vulnerability classes.

## Broken access control

- login check without ownership check
- role check without resource-scope check
- tenant filter missing from queries
- admin action enforced only in UI
- bulk action missing per-object validation

## IDOR

- object fetched by attacker-controlled ID
- no owner or tenant scoping
- predictable identifiers
- read and write paths inconsistently protected

## Authentication bypass

- route without auth middleware
- trust in unsafely sourced identity headers
- permissive fallback behavior
- internal or debug endpoints exposed

## SSRF

- server fetches user-controlled URLs
- missing protocol, host, or IP restrictions
- redirect following to internal destinations

## Injection

- string-built SQL or commands
- untrusted input reaches interpreters
- unsafe template rendering
- eval-like behavior

## Path traversal

- filesystem path built from user input
- no canonicalization
- archive extraction without traversal guards

## Deserialization

- unsafe YAML or pickle loading
- object rehydration from untrusted input
- dynamic class loading from request data

## Business logic flaws

- approval only in UI
- limit bypass by request sequencing
- client-trusted pricing, quota, or balance values
- invalid state transitions allowed
