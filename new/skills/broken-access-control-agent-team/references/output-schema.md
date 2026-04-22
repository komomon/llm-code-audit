# Output Schema

Use this file to keep broken access control review outputs stable.

## Specialist schema

Most non-judge agents should return fields like:

```yaml
agent: authz-mapper-agent
scope:
  - "PATCH /orders/{id}"
authorization_facts:
  - "Authentication middleware runs before the controller."
  - "No ownership check is visible in the handler."
  - "Repository query fetches order by id only."
evidence:
  - file: "controllers/order.py"
    function: "update_order"
    lines: "42-67"
    reason: "Mutation occurs after login check, but no owner comparison is visible."
  - file: "repositories/order_repo.py"
    function: "get_order"
    lines: "10-18"
    reason: "Query scopes by order id only."
risks:
  - type: "horizontal-privilege-escalation"
    title: "Possible cross-account order update"
    confidence: "medium"
open_questions:
  - "Is ownership enforced in an unseen service decorator?"
```

## Hypothesis schema

```yaml
agent: access-control-hypothesis-agent
candidate_findings:
  - finding_key: "BAC-order-update-01"
    type: "idor"
    title: "Possible IDOR in order update flow"
    confidence: "medium"
    exploit_conditions:
      - "Attacker can control or enumerate order_id."
      - "No downstream ownership check exists."
    attacker_prerequisites:
      - "Authenticated low-privilege user"
    mapped_dimensions:
      - "ownership"
      - "write access"
assumptions:
  - "No hidden policy layer performs ownership validation."
follow_up_checks:
  - "Search services for order.owner_id checks."
```

## Evidence schema

```yaml
agent: evidence-agent
merged_facts:
  - "Visible code authenticates the caller but does not show ownership validation."
  - "Repository lookup uses attacker-controlled order_id without tenant scoping."
merged_findings:
  - finding_key: "BAC-order-update-01"
    type: "broken-access-control"
    title: "Possible unauthorized order update"
    supporting_evidence:
      - "controllers/order.py:42-67"
      - "repositories/order_repo.py:10-18"
    confidence: "medium"
weak_items_to_drop:
  - "Speculation about admin-only fields without direct code support."
unresolved_conflicts:
  - "Service-layer authorization helpers were not provided."
```

## Judge schema

```yaml
agent: judge-agent
accepted_findings:
  - finding_id: "BAC-001"
    type: "broken-access-control"
    subtype: "horizontal-privilege-escalation"
    title: "Order update endpoint lacks ownership validation"
    severity: "high"
    confidence: "high"
    dimensions:
      - "ownership"
      - "write access"
    reason:
      - "Visible code validates authentication only."
      - "No owner or tenant check is present before mutation."
    evidence:
      - "controllers/order.py:42-67"
      - "repositories/order_repo.py:10-18"
    impact:
      - "Authenticated users may modify other users' orders."
    remediation:
      - "Enforce resource ownership or tenant scope in trusted server-side logic before update."
rejected_findings:
  - title: "Vertical privilege escalation to admin update flow"
    reason: "The reviewed artifacts did not show a reachable admin-only path."
evidence_gaps:
  - "Decorator implementations were not available."
severity_rationale:
  - "Unauthorized mutation of another user's resource is a high-severity integrity flaw."
```

## Reporter sections

The final human-readable report should preserve:

- scope
- executive summary
- confirmed findings
- evidence
- impact
- remediation
- unresolved questions

## Stable field meanings

- `type`: broad vulnerability class such as `broken-access-control` or `idor`
- `subtype`: more specific class such as `horizontal-privilege-escalation` or `tenant-isolation-failure`
- `severity`: impact if true
- `confidence`: certainty based on visible evidence
- `dimensions`: which access-control dimensions are involved
- `evidence`: traceable code support
- `reason`: why the finding is real
- `impact`: attacker outcome
- `remediation`: minimum credible fix direction
