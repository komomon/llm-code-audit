# Output Schema

Use this file to keep outputs stable across agents.

## Specialist schema

```yaml
agent: code-reader-agent
scope:
  - auth middleware
facts:
  - "The handler checks authentication only."
evidence:
  - file: "app/controllers/order.py"
    function: "update_order"
    lines: "42-67"
    reason: "No ownership validation before update."
risks:
  - type: "broken-access-control"
    title: "Possible order update authorization bypass"
    confidence: "medium"
open_questions:
  - "Is ownership enforced deeper in the stack?"
```

## Judge schema

```yaml
agent: judge-agent
accepted_findings:
  - finding_id: "BAC-001"
    type: "broken-access-control"
    title: "Order update endpoint lacks ownership validation"
    severity: "high"
    confidence: "high"
    reason:
      - "Visible code validates authentication only."
    evidence:
      - "controllers/order.py:42-67"
    impact:
      - "Authenticated users may modify other users' orders."
    remediation:
      - "Enforce server-side resource ownership validation before mutation."
rejected_findings:
  - title: "Admin bypass via hidden flag"
    reason: "No evidence in reviewed artifacts."
evidence_gaps:
  - "Repository layer not reviewed."
```

## Field meanings

- `severity`: impact
- `confidence`: certainty
- `evidence`: traceable support
- `reason`: why the issue matters
- `impact`: attacker outcome
- `remediation`: minimum credible fix direction
