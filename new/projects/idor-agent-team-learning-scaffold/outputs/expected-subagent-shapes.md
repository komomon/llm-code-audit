# Expected Subagent Shapes

## Scope agent

- `scope`
- `hotspots`
- `architecture_facts`
- `open_questions`

## Input-parameter agent

- `input_parameters`
- `evidence`
- `open_questions`

## Auth-context agent

- `trusted_identity`
- `auth_facts`
- `evidence`
- `open_questions`

## Call-chain agent

- `facts`
- `code_paths`
- `evidence`
- `open_questions`

## Input-auth-relation agent

- `relation_facts`
- `evidence`
- `open_questions`

## Output-auth-relation agent

- `relation_facts`
- `evidence`
- `open_questions`

## IDOR-hypothesis agent

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
