# Output Schema

Use this file to keep agent-team outputs stable, mergeable, and easy to judge.

The main rule is:

- specialists produce structured intermediate artifacts
- judge produces verdict artifacts
- reporter produces the final human-readable result

Do not let every agent invent its own output shape.

## 1. Shared principles

- Every claim should be traceable.
- Facts and conclusions should be separated.
- Unconfirmed items should not be mixed into confirmed findings.
- Confidence is not the same as severity.
- Missing evidence should be explicit.

## 2. Standard intermediate schema

Most specialist agents should return the following sections when possible:

```yaml
agent: code-reader-agent
scope:
  - auth middleware
  - order update flow
facts:
  - "The updateOrder handler checks only whether the user is logged in."
  - "No ownership check is visible before order mutation."
evidence:
  - file: "app/controllers/order.py"
    function: "update_order"
    lines: "42-67"
    reason: "Mutation occurs without resource ownership validation."
risks:
  - type: "broken-access-control"
    title: "Possible order update authorization bypass"
    confidence: "medium"
open_questions:
  - "Is ownership validated later in the service layer?"
```

## 3. Scope-agent schema

```yaml
agent: scope-agent
scope:
  - route: "PATCH /orders/{id}"
  - module: "app/controllers/order.py"
hotspots:
  - "order update handler"
  - "authorization middleware"
architecture_facts:
  - "Requests pass from router to controller to service."
  - "Authentication middleware runs before controller execution."
open_questions:
  - "Where is tenant isolation enforced?"
```

## 4. Code-reader schema

```yaml
agent: code-reader-agent
facts:
  - "Handler reads order_id from the URL."
  - "Service updates the order directly after login check."
code_paths:
  - entry: "routes.py:update_order_route"
    flow:
      - "routes.py:update_order_route"
      - "controllers/order.py:update_order"
      - "services/order_service.py:update_order"
evidence:
  - file: "controllers/order.py"
    function: "update_order"
    lines: "42-67"
    reason: "Missing ownership check before update."
missing_checks:
  - "resource ownership validation"
open_questions:
  - "Is authorization enforced by a decorator not shown here?"
```

## 5. Vulnerability-hypothesis schema

```yaml
agent: vulnerability-hypothesis-agent
risks:
  - type: "idor"
    title: "Possible order modification IDOR"
    confidence: "medium"
    exploit_conditions:
      - "Attacker can guess or enumerate order IDs."
      - "No downstream ownership check exists."
    attacker_prerequisites:
      - "Authenticated low-privilege account"
assumptions:
  - "No hidden policy layer performs authorization."
follow_up_checks:
  - "Search for order ownership validation in services and repositories."
```

## 6. Evidence-agent schema

```yaml
agent: evidence-agent
merged_facts:
  - "PATCH /orders/{id} reaches update_order and then order_service.update_order."
  - "Visible checks show authentication but not ownership validation."
merged_findings:
  - finding_key: "BAC-order-update-01"
    title: "Possible broken access control in order update flow"
    supporting_evidence:
      - "controllers/order.py:42-67"
      - "services/order_service.py:10-31"
    confidence: "medium"
weak_items_to_drop:
  - "Speculation about admin-only fields without direct code evidence."
unresolved_conflicts:
  - "Middleware behavior is partially unknown."
```

## 7. Judge-agent schema

Judge output should be stricter than specialist output.

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
      - "No resource ownership check is present in the handler or called service."
    evidence:
      - "controllers/order.py:42-67"
      - "services/order_service.py:10-31"
    impact:
      - "Authenticated users may modify orders that do not belong to them."
    remediation:
      - "Enforce resource ownership checks in trusted server-side logic before mutation."
rejected_findings:
  - title: "Admin privilege escalation through hidden flag"
    reason: "No code evidence in the reviewed artifacts."
evidence_gaps:
  - "Repository layer was not available for review."
severity_rationale:
  - "Unauthorized modification of another user's resource is a high-severity integrity issue."
```

## 8. Reporter schema

The reporter may internally receive structured inputs, but the final output is
human-readable. A good final report should preserve these sections:

- scope
- executive summary
- findings
- evidence
- impact
- remediation
- unresolved questions

## 9. Finding field definitions

Use these stable meanings across the team:

- `type`: vulnerability class such as `broken-access-control`, `idor`, `ssrf`, `sql-injection`
- `title`: short human-readable issue name
- `severity`: business/security impact, not certainty
- `confidence`: certainty that the finding is real based on current evidence
- `reason`: concise why-this-is-a-problem explanation
- `evidence`: concrete traceable locations
- `impact`: what an attacker can do
- `remediation`: minimum credible fix direction

## 10. Severity guidance

Use severity for impact:

- `critical`: direct system takeover, broad data compromise, or unauthenticated high-impact abuse
- `high`: strong confidentiality, integrity, or tenant-isolation impact
- `medium`: meaningful but constrained security impact
- `low`: limited impact or defense-in-depth issue

Use confidence for certainty:

- `high`: directly supported by visible code or artifacts
- `medium`: likely based on strong indicators, but one assumption remains
- `low`: weakly supported and needs more validation

Do not use severity as a substitute for confidence.
