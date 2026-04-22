# Example Adaptations

Use this file to specialize the generic template without changing the core
workflow.

## Access control review

- emphasize ownership checks
- emphasize tenant boundaries
- use broken-access-control and IDOR checklist items

## Injection review

- emphasize user-controlled inputs
- emphasize interpreter boundaries
- use SQL, command, template, and NoSQL checklist items

## SSRF review

- emphasize outbound request sinks
- emphasize URL validation and network boundary controls

## Business logic review

- emphasize workflow states
- emphasize approvals, quotas, balances, and sequence-sensitive transitions

## Large monorepo review

- add a `dependency-agent` or `config-agent` only if needed
- keep output schema stable
- keep final judgment centralized
