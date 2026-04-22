# Expected Subagent Shapes

Use these field groups as the expected output shape.

## Scope agent

- `scope`
- `hotspots`
- `architecture_facts`
- `open_questions`

## Authz mapper agent

- `scope`
- `authorization_facts`
- `evidence`
- `open_questions`

## Code-path agent

- `facts`
- `code_paths`
- `evidence`
- `missing_checks`
- `open_questions`

## Access-control-hypothesis agent

- `candidate_findings`
- `assumptions`
- `follow_up_checks`

## Evidence agent

- `merged_facts`
- `merged_findings`
- `weak_items_to_drop`
- `unresolved_conflicts`

## Judge agent

- `accepted_findings`
- `rejected_findings`
- `evidence_gaps`
- `severity_rationale`

## Reporter agent

- `final_report`
